
"""
    Tracer main class
"""
import time
import copy
from kytos.core import log
from kytos.core.switch import Interface
from napps.amlight.sdntrace_cp.tracing.rest import FormatRest
from napps.amlight.sdntrace.shared.switches import Switches
from napps.amlight.sdntrace.shared.colors import Colors
from napps.amlight.sdntrace import settings


class TracePath(object):
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

    def __init__(self, trace_manager, r_id, initial_entries):
        """
        Args:
            trace_manager: main TraceManager class - needed because Kytos.controller
            r_id: request ID
            initial_entries: user entries for trace
        """
        self.switches = Switches()
        self.trace_mgr = trace_manager
        self.id = r_id
        self.init_entries = initial_entries

        self.trace_result = []
        self.trace_ended = False
        self.init_switch = self.get_init_switch()
        self.rest = FormatRest()
        self.mydomain = settings.MY_DOMAIN

    def get_init_switch(self):
        """Get the Switch class of the switch requested by user

        Returns:
            Switch class
        """
        dpid = self.init_entries['trace']['switch']['dpid']
        return Switches().get_switch(dpid)

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
        # A loop waiting for 'trace_ended'. It changes to True when reaches timeout
        while not self.trace_ended:
            #in_port, probe_pkt = generate_trace_pkt(entries, color, self.id,
            #                                        self.mydomain)
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
                # If we got here, that means we need to keep going.
                #entries, color, switch = prepare_next_packet(entries, result,
                #                                             packet_in)

        # Add final result to trace_results_queue
        t_result = {"request_id": self.id, "result": self.trace_result,
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

        log.info('Entries %s' % entries)
        # send_packet_out(self.trace_mgr.controller, switch, in_port, probe_pkt.data)
        #send_packet_out(self.trace_mgr.controller, switch, in_port, probe_pkt)
        flow, actions, port = switch.match_and_apply(entries)
        log.info('Flow %s' % flow)
        if not flow:
            return 'timeout', None

        if not port:
            return 'timeout', None

        endpoint = self.find_endpoint(switch, port)
        log.info('Endpoint %s' % endpoint)
        if endpoint:
            entries['dpid'] = endpoint.switch.dpid
            entries['in_port'] = endpoint.port_number
        else:
            return 'timeout', None

        return {'dpid': entries['dpid'], "port": entries['in_port']}, entries

        # while True:
        #     time.sleep(0.5)  # Wait 0.5 second before querying for PacketIns
        #     timeout_control += 1
        #
        #     if timeout_control >= 3:
        #         return 'timeout', False
        #
        #     # Check if there is any Probe PacketIn in the queue
        #     for pIn in self.trace_mgr.trace_pktIn:
        #         # Let's look for traces with our self.id
        #         # Each entry has the following format:
        #         # (pktIn_dpid, pktIn_port, TraceMsg, pkt, ev)
        #         # packetIn_data_request_id is the request id
        #         # of the packetIn.data.
        #
        #         msg = pIn[2]
        #         if self.id == msg.request_id:
        #             self.clear_trace_pkt_in()
        #             return {'dpid': pIn[0], "port": pIn[1]}, pIn[4]
        #         else:
        #             log.warning('Sending PacketOut Again')
        #             # send_packet_out(self.trace_mgr.controller, switch, in_port, probe_pkt.data)
        #             send_packet_out(self.trace_mgr.controller, switch, in_port, probe_pkt)

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

    @staticmethod
    def find_endpoint(switch, port):
        """ Finds where switch/port is connected. If it is another switch, 
        returns the interface it is connected to, otherwise returns None """
        interface = switch.interfaces[port]
        for endpoint, _ in interface.endpoints:
            if isinstance(endpoint, Interface):
                return endpoint
        return None

    def clear_trace_pkt_in(self):
        """ Once the probe PacketIn was processed, delete it from queue """
        for pIn in self.trace_mgr.trace_pktIn:
            msg = pIn[2]
            if self.id == msg.request_id:
                self.trace_mgr.trace_pktIn.remove(pIn)

    def check_loop(self):
        """ Check if there are equal entries """
        i = 0
        last = len(self.trace_result) - 1
        while i < last:
            if self.trace_result[i]['dpid'] == self.trace_result[last]['dpid']:
                if self.trace_result[i]['port'] == self.trace_result[last]['port']:
                    return True
            i += 1
        return 0
