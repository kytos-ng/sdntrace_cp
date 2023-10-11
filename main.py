"""Main module of amlight/sdntrace_cp Kytos Network Application.

Run tracepaths on OpenFlow in the Control Plane
"""

import pathlib
from datetime import datetime

import tenacity
from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import load_spec, validate_openapi
from kytos.core.rest_api import (HTTPException, JSONResponse, Request,
                                 get_json_or_400)
from napps.amlight.sdntrace_cp.utils import (convert_entries,
                                             convert_list_entries,
                                             find_endpoint, get_stored_flows,
                                             match_field_dl_vlan,
                                             match_field_ip, prepare_json)


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

    @rest('/v1/trace', methods=['PUT'])
    @validate_openapi(spec)
    def trace(self, request: Request) -> JSONResponse:
        """Trace a path."""
        result = []
        data = get_json_or_400(request, self.controller.loop)
        entries = convert_entries(data)
        if not entries:
            raise HTTPException(400, "Empty entries")
        try:
            stored_flows = get_stored_flows()
        except tenacity.RetryError as exc:
            raise HTTPException(424, "It couldn't get stored_flows") from exc
        try:
            result = self.tracepath(entries, stored_flows)
        except ValueError as exception:
            log.debug("tracepath error {exception}")
            raise exception
        return JSONResponse(prepare_json(result))

    @rest('/v1/traces', methods=['PUT'])
    @validate_openapi(spec)
    def get_traces(self, request: Request) -> JSONResponse:
        """For bulk requests."""
        data = get_json_or_400(request, self.controller.loop)
        entries = convert_list_entries(data)
        results = []
        try:
            stored_flows = get_stored_flows()
        except tenacity.RetryError as exc:
            raise HTTPException(424, "It couldn't get stored_flows") from exc
        for entry in entries:
            try:
                results.append(self.tracepath(entry, stored_flows))
            except ValueError as exception:
                log.debug("tracepath error {exception}")
                raise exception
        return JSONResponse(prepare_json(results))

    def tracepath(self, entries, stored_flows):
        """Trace a path for a packet represented by entries."""
        # pylint: disable=too-many-branches
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
                # No match
                break
            if 'out' in trace_step and trace_step['out']:
                if self.check_loop_trace_step(trace_step, trace_result):
                    do_trace = False
            trace_result.append(trace_step)
        if len(trace_result) == 1 and \
                trace_result[0]['in']['type'] == 'starting':
            trace_result[0]['in']['type'] = 'last'
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
            log.warning(f"Port {port} not found on switch {switch}")
            return None
        endpoint = endpoint['endpoint']
        if endpoint is None:
            return {'out_port': port,
                    'entries': entries}

        return {'dpid': endpoint.switch.dpid,
                'in_port': endpoint.port_number,
                'out_port': port,
                'entries': entries}

    @classmethod
    def do_match(cls, flow, args, table_id):
        """Match a packet against this flow (OF1.3)."""
        # pylint: disable=consider-using-dict-items
        # pylint: disable=too-many-return-statements
        if ('match' not in flow['flow']) or (len(flow['flow']['match']) == 0):
            return False
        table_id_ = flow['flow'].get('table_id', 0)
        if table_id != table_id_:
            return False
        for name in flow['flow']['match']:
            field_flow = flow['flow']['match'][name]
            field = args.get(name)
            if name == 'dl_vlan':
                if not match_field_dl_vlan(field, field_flow):
                    return False
                continue
            # In the case of dl_vlan field, the match must be checked
            # even if this field is not in the packet args.
            if not field:
                return False
            if name in ('nw_src', 'nw_dst', 'ipv6_src', 'ipv6_dst'):
                if not match_field_ip(field, field_flow):
                    return False
                continue
            if field_flow != field:
                return False
        return flow

    # pylint: disable=too-many-arguments
    def match_flows(self, switch, table_id, args, stored_flows, many=True):
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
                match = Main.do_match(flow, args, table_id)
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

    def process_tables(self, switch, table_id, args, stored_flows, actions):
        """Resolve the table context and get actions in the matched flow"""
        goto_table = False
        actions_ = []
        flow = self.match_flows(switch, table_id, args, stored_flows, False)
        if flow and 'actions' in flow['flow']:
            actions_ = flow['flow']['actions']
        elif flow and 'instructions' in flow['flow']:
            for instruction in flow['flow']['instructions']:
                if instruction['instruction_type'] == 'apply_actions':
                    actions_ = instruction['actions']
                elif instruction['instruction_type'] == 'goto_table':
                    table_id_ = instruction['table_id']
                    if table_id < table_id_:
                        table_id = table_id_
                        goto_table = True
                    else:
                        msg = f"Wrong table_id in {flow['flow']}: \
                            The packet can only been directed to a \
                                flow table number greather than {table_id}"
                        raise ValueError(msg) from ValueError
        actions.extend(actions_)
        return flow, actions, goto_table, table_id

    def match_and_apply(self, switch, args, stored_flows):
        """Match flows and apply actions.
        Match given packet (in args) against
        the stored flows (from flow_manager) and,
        if a match flow is found, apply its actions."""
        table_id = 0
        goto_table = True
        port = None
        actions = []
        while goto_table:
            try:
                flow, actions, goto_table, table_id = self.process_tables(
                    switch, table_id, args, stored_flows, actions)
            except ValueError as exception:
                raise exception
        if not flow or switch.ofp_version != '0x04':
            return flow, args, port

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
