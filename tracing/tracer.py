
"""
    Tracer main class
"""
import time
import copy
from kytos.core import log
from kytos.core.interface import Interface
from kytos.core.helpers import listen_to
from napps.amlight.sdntrace.tracing.rest import FormatRest
from napps.amlight.sdntrace.tracing.tracer import TracePath as DPTracePath
from napps.amlight.sdntrace.shared.switches import Switches
from napps.amlight.sdntrace.shared.colors import Colors
from napps.amlight.sdntrace import settings
from napps.amlight.kytos_flow_manager.main import Main as FlowManager


class TracePath(DPTracePath):
    """
        Tracer main class - responsible for running traces.
        It is composed of two parts:
         1) Sending PacketOut messages to switches
         2) Reading the pktIn queue with PacketIn received

        There are a few possibilities of result (except for errors):
        - Timeouts ({'trace': 'completed'}) - even positive results end w/
            timeouts.
        - Loops ({'trace': 'loop'}) - every time an entry is seen twice
            in the trace_result queue, we stop

        Some things to take into consideration:
        - we can have parallel traces
        - we can have flow rewrite along the path (vlan translation, f.i)
    """

    TRANSLATE_NAMES = {
        'dl_src': 'eth_src',
        'dl_dst': 'eth_dst',
        'dl_type': 'eth_type',
        'dl_vlan': 'vlan_vid',
        'nw_src': 'ip4_src',
        'nw_dst': 'ip4_dst',
        'nw_tos': 'ip_tos',
        'nw_proto': 'ip_proto',
    }

    def tracepath(self):
        """
            Do the trace path
            The logic is very simple:
            1 - Generate the probe packet using entries provided
            2 - Results a result and the packet_in (used to generate new probe)
                Possible results: 'timeout' meaning the end of trace
                                  or the trace step {'dpid', 'port'}
                Some networks do vlan rewriting, so it is important to get the
                packetIn msg with the header
            3 - If result is a trace step, send PacketOut to the switch that
                originated the PacketIn. Repeat till reaching timeout
        """
        log.warning("Starting Trace Path for ID %s" % self.id)

        entries = copy.deepcopy(self.init_entries)
        color = Colors().get_switch_color(self.init_switch.dpid)
        switch = self.init_switch
        # Add initial trace step
        self.rest.add_trace_step(self.trace_result, trace_type='starting',
                                 dpid=switch.dpid,
                                 port=entries['trace']['switch']['in_port'])
        entries = self.convert_entries(entries)

        # A loop waiting for 'trace_ended'.
        # It changes to True when reaches timeout
        while not self.trace_ended:
            switch = Switches().get_switch(entries['dpid'])
            result, entries = self.send_trace_probe(switch, entries)
            if result == 'timeout':
                self.rest.add_trace_step(self.trace_result, trace_type='last')
                log.warning("Intra-Domain Trace Completed!")
                self.trace_ended = True
            else:
                self.rest.add_trace_step(self.trace_result, trace_type='trace',
                                         dpid=result['dpid'], port=result['port'])
                if self.check_loop():
                    self.rest.add_trace_step(self.trace_result, trace_type='last',
                                             reason='loop')
                    self.trace_ended = True
                    break

        # Add final result to trace_results_queue
        t_result = {"request_id": self.id,
                    "result": self.trace_result,
                    "start_time": str(self.rest.start_time),
                    "total_time": self.rest.get_time(),
                    "request": self.init_entries}

        self.trace_mgr.add_result(self.id, t_result)

    def send_trace_probe(self, switch, entries):
        """ This method sends the PacketOut and checks if the
        PacketIn was received in 3 seconds.

        Args:
            switch: target switch to start with
            in_port: target port to start with
            probe_pkt: ethernet frame to send (PacketOut.data)

        Returns:
            Timeout
            {switch & port}
        """
        timeout_control = 0  # Controls the timeout of 1 second and two tries

        flow, entries, port = FlowManager.match_and_apply(switch, entries)
        if not flow or not port:
            return 'timeout', None

        endpoint = self.trace_mgr.find_endpoint(switch, port)
        if endpoint:
            parts = endpoint.split(':')
            dpid = ':'.join(parts[:8])
            port = parts[-1]
            entries['dpid'] = dpid
            entries['in_port'] = port
        else:
            return 'timeout', None

        return {'dpid': entries['dpid'], "port": entries['in_port']}, entries

    @staticmethod
    def convert_entries(entries):
        """ Transform entries dictionary in a plain dictionary suitable for
            matching
        
        :param entries: dict 
        :return: plain dict
        """
        new_entries = {}
        for entry in entries['trace'].values():
            for field, value in entry.items():
                if field in TracePath.TRANSLATE_NAMES:
                    new_entries[TracePath.TRANSLATE_NAMES[field]] = value
                else:
                    new_entries[field] = value
        return new_entries

