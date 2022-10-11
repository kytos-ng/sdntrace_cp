"""Main module of amlight/sdntrace_cp Kytos Network Application.

Run tracepaths on OpenFlow in the Control Plane
"""

from datetime import datetime
import requests
import ipaddress
from flask import jsonify, request
from kytos.core import KytosNApp, log, rest, switch
from kytos.core.helpers import listen_to
from napps.kytos.of_core.v0x04.flow import Action
from napps.kytos.of_core.v0x04.match_fields import MatchFieldFactory
from napps.amlight.sdntrace_cp import settings
from napps.amlight.sdntrace_cp.automate import Automate
from napps.amlight.sdntrace_cp.utils import (convert_entries, find_endpoint,
                                             prepare_json)


class Main(KytosNApp):
    """Main class of amlight/sdntrace_cp NApp.

    This application gets the list of flows from the switches
    and uses it to trace paths without using the data plane.
    """

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
        self.stored_flows = None

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
    def trace(self):
        """Trace a path."""
        entries = request.get_json()
        entries = convert_entries(entries)
    
        dpid = entries['dpid']
        self.stored_flows = Main.get_stored_flows([dpid], state='installed')
        switches = [self.controller.get_switch_by_dpid(dpid)]
        self.map_flows(switches)
        print('stores1')
        print(self.stored_flows)
        result = self.tracepath(entries,switches[0])
        return jsonify(prepare_json(result))

    def tracepath(self, entries,switch):
        """Trace a path for a packet represented by entries."""
        self.last_id += 1
        trace_id = self.last_id
        trace_result = []
        trace_type = 'starting'

        do_trace = True
        while do_trace:
            trace_step = {'in': {'dpid': entries['dpid'],
                                 'port': entries['in_port'],
                                 'time': str(datetime.now()),
                                 'type': trace_type}}
            if 'vlan_vid' in entries:
                trace_step['in'].update({'vlan': entries['vlan_vid'][-1]})
            result = self.trace_step(switch, entries)
            if result:
                out = {'port': result['out_port']}
                if 'vlan_vid' in result['entries']:
                    out.update({'vlan': result['entries']['vlan_vid'][-1]})
                trace_step.update({
                    'out': out
                })
                if 'dpid' in result:
                    next_step = {'dpid': result['dpid'],
                                 'port': result['in_port']}
                    if self.has_loop(next_step, trace_result):
                        do_trace = False
                    else:
                        entries = result['entries']
                        entries['dpid'] = result['dpid']
                        entries['in_port'] = result['in_port']
                        trace_type = 'trace'
                else:
                    do_trace = False
                    print('***************nodpid')
                print('do_trace')
                print(do_trace)
                print(result)
                print(trace_step)
            else:
                do_trace = False
                print('//////////////noresult')
            trace_result.append(trace_step)
        self.traces.update({
            trace_id: trace_result
        })
        return trace_result

    @staticmethod
    def has_loop(trace_step, trace_result):
        """Check if there is a loop in the trace result."""
        for trace in trace_result:
            if trace['in']['dpid'] == trace_step['dpid'] and \
                            trace['in']['port'] == trace_step['port']:
                return True
        return False

    def trace_step(self, switch, entries):
        """Perform a trace step.

        Match the given fields against the switch's list of flows."""
        flow, entries, port = self.match_and_apply(switch, entries)
        
        if not flow or not port:
            return None

        endpoint = find_endpoint(switch, port)
        if endpoint is None:
            return {'out_port': port,
                    'entries': entries}

        return {'dpid': endpoint.switch.dpid,
                'in_port': endpoint.port_number,
                'out_port': port,
                'entries': entries}

    @listen_to('amlight/flow_stats.flows_updated')
    def update_circuits(self, event):
        """Update the list of circuits after a flow change."""
        # pylint: disable=unused-argument
        if settings.FIND_CIRCUITS_IN_FLOWS:
            self.automate.find_circuits()

    def map_flows(self, switches = None):
        """Map the flows in memory given the stored flows"""
        flows = {}
        if not switches:
            switches = self.controller.switches.copy().values() 
        for switch in switches:
            flows[switch.dpid] = []
            flows_sw_dict = {flow_sw.id:flow_sw for flow_sw in switch.flows}
            for flow_item in self.stored_flows[switch.dpid]:
                id = flow_item['flow_id']
                if id in flows_sw_dict:
                    flow = flows_sw_dict[id]
                    flow_item = flow_item['flow']
                    flow.cookie = flow_item['cookie']
                    flow.hard_timeout = flow_item['hard_timeout']
                    flow.idle_timeout = flow_item['idle_timeout']
                    flow.priority = flow_item['priority']
                    flow.table_id = flow_item['table_id']
                    flow.actions = []
                    for action in flow_item['actions']:
                        action = Action.from_dict(action)
                        flow.actions.append(action) 
                    flows[switch.dpid].append(flow)          
        self.stored_flows = flows 

    @staticmethod
    def get_stored_flows(dpids:list = None, state:str = None):  
        api_url = f'{settings.FLOW_MANAGER_URL}/stored_flows'
        if dpids:
            str_dpids = ''
            for dpid in dpids:
                str_dpids += f'&dpid={dpid}' 
            api_url += '/?'+str_dpids[1:]
        if state:
            char = '&' if dpids else '/?'
            api_url += char+f'state={state}'
        result = requests.get(api_url)
        flows_from_manager = result.json()
        return flows_from_manager

    def do_match(flow, args):
        """Match a packet against this flow (OF1.3)."""
        # pylint: disable=consider-using-dict-items
        if len(flow.as_dict()['match']) == 0:
            return False
        for name in flow.as_dict()['match']:
            field_flow = flow.as_dict()['match'][name]
            if name == 'dl_vlan':
                name = 'vlan_vid'
            if name not in args:
                return False
            if name == 'vlan_vid':
                field = args[name][-1]
            else:
                field = args[name]
            if name not in ('ipv4_src', 'ipv4_dst', 'ipv6_src', 'ipv6_dst'):
                if field_flow != field:
                    return False
            else:
                packet_ip = int(ipaddress.ip_address(field))
                ip_addr = flow.as_dict()['match'][name]
                if packet_ip & ip_addr.netmask != ip_addr.address:
                    return False
        return flow

    def match_flows(self, switch, args, many=True):
        # pylint: disable=bad-staticmethod-argument
        """
        Match the packet in request against the flows installed in the switch and stored according flow_manager.
        Try the match with each flow, in other. If many is True, tries the
        match with all flows, if False, tries until the first match.
        :param args: packet data
        :param many: Boolean, indicating whether to continue after matching the
                first flow or not
        :return: If many, the list of matched flows, or the matched flow
        """
        '''
        stored_flows = Main.get_stored_flows([switch.dpid], state='installed')
        self.stored_flows = self.map_flows(stored_flows, [switch])
        '''         
        response = []
        try:
            for flow in self.stored_flows[switch.dpid]:
                match = Main.do_match(flow,args)
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
        
    def match_and_apply(self, switch, args):
        # pylint: disable=bad-staticmethod-argument
        """Match flows and apply actions.
        Match given packet (in args) against the switch flows (stored) and,
        if a match flow is found, apply its actions."""
        flow = self.match_flows(switch, args, False)
        port = None
        actions = None
        # pylint: disable=too-many-nested-blocks
        if flow:
            actions = flow.actions
            if switch.ofp_version == '0x04':
                for action in actions:
                    action_type = action.action_type
                    if action_type == 'output':
                        port = action.port
                    if action_type == 'push_vlan':
                        if 'vlan_vid' not in args:
                            args['vlan_vid'] = []
                        args['vlan_vid'].append(0)
                    if action_type == 'pop_vlan':
                        if 'vlan_vid' in args:
                            args['vlan_vid'].pop()
                            if len(args['vlan_vid']) == 0:
                                del args['vlan_vid']
                    if action_type == 'set_vlan':
                        args['vlan_vid'][-1] = action.vlan_id
        return flow, args, port


        