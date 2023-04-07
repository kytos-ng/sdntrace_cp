"""Main module of amlight/sdntrace_cp Kytos Network Application.

Run tracepaths on OpenFlow in the Control Plane
"""

import ipaddress
import pathlib
from datetime import datetime

from flask import jsonify
from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import load_spec, validate_openapi
from napps.amlight.sdntrace_cp import settings
from napps.amlight.sdntrace_cp.automate import Automate
from napps.amlight.sdntrace_cp.utils import (convert_entries,
                                             convert_list_entries,
                                             find_endpoint, get_stored_flows,
                                             match_field_dl_vlan, prepare_json)


class Main(KytosNApp):
    """Main class of amlight/sdntrace_cp NApp.

    This application gets the list of flows from the switches
    and uses it to trace paths without using the data plane.
    """

    spec = load_spec(pathlib.Path(__file__).parent / "openapi.yml")

    def setup(self):
        """Replace the '__init__' method for the KytosNApp subclass.

        The setup method is automatically called by the controller when your
        application is loaded.

        """
        log.info("Starting Kytos SDNTrace CP App!")

        self.traces = {}
        self.last_id = 30000
        self.automate = Automate(self)
        self.automate.schedule_traces()
        self.automate.schedule_important_traces()

    def execute(self):
        """This method is executed right after the setup method execution.

        You can also use this method in loop mode if you add to the above setup
        method a line like the following example:

            self.execute_as_loop(30)  # 30-second interval.
        """

    def shutdown(self):
        """This method is executed when your napp is unloaded.

        If you have some cleanup procedure, insert it here.
        """
        self.automate.unschedule_ids()
        self.automate.sheduler_shutdown(wait=False)

    @rest('/trace', methods=['PUT'])
    @validate_openapi(spec)
    def trace(self, data):
        """Trace a path."""
        result = []
        entries = convert_entries(data)
        if not entries:
            return "Bad request", 400
        stored_flows = get_stored_flows()
        result = self.tracepath(entries, stored_flows)
        return jsonify(prepare_json(result))

    @rest('/traces', methods=['PUT'])
    @validate_openapi(spec)
    def get_traces(self, data):
        """For bulk requests."""
        entries = convert_list_entries(data)
        stored_flows = get_stored_flows()
        results = []
        for entry in entries:
            results.append(self.tracepath(entry, stored_flows))
        temp = prepare_json(results)
        return jsonify(temp)

    def tracepath(self, entries, stored_flows):
        """Trace a path for a packet represented by entries."""
        # pylint: disable=too-many-branches
        self.last_id += 1
        trace_id = self.last_id
        trace_result = []
        trace_type = 'starting'
        do_trace = True
        while do_trace:
            if 'dpid' not in entries or 'in_port' not in entries:
                break
            trace_step = {'in': {'dpid': entries['dpid'],
                                 'port': entries['in_port'],
                                 'time': str(datetime.now()),
                                 'type': trace_type}}
            if 'dl_vlan' in entries:
                trace_step['in'].update({'vlan': entries['dl_vlan'][-1]})

            switch = self.controller.get_switch_by_dpid(entries['dpid'])
            if not switch:
                trace_step['in']['type'] = 'last'
                trace_result.append(trace_step)
                break
            result = self.trace_step(switch, entries, stored_flows)
            if result:
                out = {'port': result['out_port']}
                if 'dl_vlan' in result['entries']:
                    out.update({'vlan': result['entries']['dl_vlan'][-1]})
                trace_step.update({
                    'out': out
                })
                if 'dpid' in result:
                    next_step = {'dpid': result['dpid'],
                                 'port': result['in_port']}
                    entries = result['entries']
                    entries['dpid'] = result['dpid']
                    entries['in_port'] = result['in_port']
                    if self.has_loop(next_step, trace_result):
                        trace_step['in']['type'] = 'loop'
                        do_trace = False
                    else:
                        trace_type = 'intermediary'
                else:
                    trace_step['in']['type'] = 'last'
                    do_trace = False
            else:
                trace_step['in']['type'] = 'incomplete'
                do_trace = False
            if 'out' in trace_step and trace_step['out']:
                if self.check_loop_trace_step(trace_step, trace_result):
                    do_trace = False
            trace_result.append(trace_step)
        self.traces.update({
            trace_id: trace_result
        })
        return trace_result

    @staticmethod
    def check_loop_trace_step(trace_step, trace_result):
        """Check if there is a loop in the trace and add the step."""
        # outgoing interface is the same as the input interface
        if not trace_result and \
                trace_step['in']['type'] == 'last' and \
                trace_step['in']['port'] == trace_step['out']['port']:
            trace_step['in']['type'] = 'loop'
            return True
        if trace_result and \
                trace_result[0]['in']['dpid'] == trace_step['in']['dpid'] and \
                trace_result[0]['in']['port'] == trace_step['out']['port']:
            trace_step['in']['type'] = 'loop'
            return True
        return False

    @staticmethod
    def has_loop(trace_step, trace_result):
        """Check if there is a loop in the trace result."""
        for trace in trace_result:
            if trace['in']['dpid'] == trace_step['dpid'] and \
                            trace['in']['port'] == trace_step['port']:
                return True
        return False

    def trace_step(self, switch, entries, stored_flows):
        """Perform a trace step.

        Match the given fields against the switch's list of flows."""
        flow, entries, port = self.match_and_apply(
                                                    switch,
                                                    entries,
                                                    stored_flows
                                                )

        if not flow or not port:
            return None

        endpoint = find_endpoint(switch, port)
        if endpoint is None:
            log.warning(f'Interface not found')
            return None
        endpoint = endpoint['endpoint']
        if endpoint is None:
            return {'out_port': port,
                    'entries': entries}

        return {'dpid': endpoint.switch.dpid,
                'in_port': endpoint.port_number,
                'out_port': port,
                'entries': entries}

    def update_circuits(self):
        """Update the list of circuits after a flow change."""
        # pylint: disable=unused-argument
        if settings.FIND_CIRCUITS_IN_FLOWS:
            self.automate.find_circuits()

    @classmethod
    def do_match(cls, flow, args):
        """Match a packet against this flow (OF1.3)."""
        # pylint: disable=consider-using-dict-items
        # pylint: disable=too-many-return-statements
        if ('match' not in flow['flow']) or (len(flow['flow']['match']) == 0):
            return False
        for name in flow['flow']['match']:
            field_flow = flow['flow']['match'][name]
            if name == 'dl_vlan':
                field = args.get(name)
                if field:
                    field = field[-1]
                if not match_field_dl_vlan(field, field_flow):
                    return False
                continue
            if name not in args:
                return False
            field = args[name]
            if name not in ('ipv4_src', 'ipv4_dst', 'ipv6_src', 'ipv6_dst'):
                if field_flow != field:
                    return False
            else:
                packet_ip = int(ipaddress.ip_address(field))
                ip_addr = flow['flow']['match'][name]
                if packet_ip & ip_addr.netmask != ip_addr.address:
                    return False
        return flow

    def match_flows(self, switch, args, stored_flows, many=True):
        # pylint: disable=bad-staticmethod-argument
        """
        Match the packet in request against the stored flows from flow_manager.
        Try the match with each flow, in other. If many is True, tries the
        match with all flows, if False, tries until the first match.
        :param args: packet data
        :param many: Boolean, indicating whether to continue after matching the
                first flow or not
        :return: If many, the list of matched flows, or the matched flow
        """
        if switch.dpid not in stored_flows:
            return None
        response = []
        if switch.dpid not in stored_flows:
            return None
        try:
            for flow in stored_flows[switch.dpid]:
                match = Main.do_match(flow, args)
                if match:
                    if many:
                        response.append(match)
                    else:
                        response = match
                        break
        except AttributeError:
            return None
        if not many and isinstance(response, list):
            return None
        return response

    # pylint: disable=redefined-outer-name
    def match_and_apply(self, switch, args, stored_flows):
        # pylint: disable=bad-staticmethod-argument
        """Match flows and apply actions.
        Match given packet (in args) against
        the stored flows (from flow_manager) and,
        if a match flow is found, apply its actions."""
        flow = self.match_flows(switch, args, stored_flows, False)
        port = None
        actions = []
        # pylint: disable=too-many-nested-blocks
        if not flow or switch.ofp_version != '0x04':
            return flow, args, port
        if 'actions' in flow['flow']:
            actions = flow['flow']['actions']
        for action in actions:
            action_type = action['action_type']
            if action_type == 'output':
                port = action['port']
            if action_type == 'push_vlan':
                if 'dl_vlan' not in args:
                    args['dl_vlan'] = []
                args['dl_vlan'].append(0)
            if action_type == 'pop_vlan':
                if 'dl_vlan' in args:
                    args['dl_vlan'].pop()
                    if len(args['dl_vlan']) == 0:
                        del args['dl_vlan']
            if action_type == 'set_vlan':
                args['dl_vlan'][-1] = action['vlan_id']
        return flow, args, port
