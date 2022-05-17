"""Main module of amlight/sdntrace_cp Kytos Network Application.

Run tracepaths on OpenFlow in the Control Plane
"""

from datetime import datetime
from kytos.core import KytosNApp, KytosEvent, log, rest
from kytos.core.helpers import listen_to
from flask import jsonify, request
from napps.amlight.sdntrace_cp import settings
from napps.amlight.sdntrace_cp.automate import Automate
from napps.amlight.sdntrace_cp.utils import (
    convert_entries, find_endpoint, prepare_json
)
from napps.amlight.flow_stats.main import Main as FlowManager


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
        if settings.TRIGGER_SCHEDULE_TRACES:
            event = KytosEvent('amlight/scheduler.add_job')
            event.content['id'] = 'automatic_traces'
            event.content['func'] = self.automate.run_traces
            try:
                trigger = settings.SCHEDULE_TRIGGER
                kwargs = settings.SCHEDULE_ARGS
            except AttributeError:
                trigger = 'interval'
                kwargs = {'seconds': 60}
            event.content['kwargs'] = {'trigger': trigger}
            event.content['kwargs'].update(kwargs)
            self.controller.buffers.app.put(event)
        if settings.TRIGGER_IMPORTANT_CIRCUITS:
            event = KytosEvent('amlight/scheduler.add_job')
            event.content['id'] = 'automatic_important_traces'
            event.content['func'] = self.automate.run_important_traces
            try:
                trigger = settings.IMPORTANT_CIRCUITS_TRIGGER
                kwargs = settings.IMPORTANT_CIRCUITS_ARGS
            except AttributeError:
                trigger = 'interval'
                kwargs = {'minutes': 10}
            event.content['kwargs'] = {'trigger': trigger}
            event.content['kwargs'].update(kwargs)
            self.controller.buffers.app.put(event)

    def execute(self):
        """This method is executed right after the setup method execution.

        You can also use this method in loop mode if you add to the above setup
        method a line like the following example:

            self.execute_as_loop(30)  # 30-second interval.
        """
        pass

    def shutdown(self):
        """This method is executed when your napp is unloaded.

        If you have some cleanup procedure, insert it here.
        """
        event = KytosEvent('amlight/scheduler.remove_job')
        event.content['id'] = 'automatic_traces'
        self.controller.buffers.app.put(event)
        event = KytosEvent('amlight/scheduler.remove_job')
        event.content['id'] = 'automatic_important_traces'
        self.controller.buffers.app.put(event)

    @rest('/trace', methods=['PUT'])
    def trace(self):
        """Trace a path."""
        entries = request.get_json()
        result = self.tracepath(entries)
        return jsonify(prepare_json(result))

    def tracepath(self, entries):
        """Trace a path for a packet represented by entries."""
        self.last_id += 1
        trace_id = self.last_id
        entries = convert_entries(entries)
        trace_result = []
        trace_type = 'starting'

        do_trace = True
        while do_trace:
            trace_step = {'in':
                              {'dpid': entries['dpid'],
                               'port': entries['in_port'],
                               'time': str(datetime.now()),
                               'type': trace_type}}
            if 'vlan_vid' in entries:
                trace_step['in'].update({'vlan': entries['vlan_vid'][0]})
            switch = self.controller.get_switch_by_dpid(entries['dpid'])
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
            else:
                do_trace = False
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

    @staticmethod
    def trace_step(switch, entries):
        """Perform a trace step.

        Match the given fields against the switch's list of flows."""
        flow, entries, port = FlowManager.match_and_apply(switch, entries)
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
