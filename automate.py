"""Automate circuit traces."""

import time
import requests
from pyof.v0x01.common.phy_port import Port as Port10
from pyof.v0x04.common.port import PortNo as Port13
from napps.amlight.sdntrace_cp.utils import format_result, clean_circuits
from napps.amlight.sdntrace_cp import settings
from kytos.core import KytosEvent, log


class Automate:
    """Find all circuits and automate trace execution."""

    def __init__(self, tracer):
        self._tracer = tracer
        self._circuits = []
        self.find_circuits()

    def find_circuits(self):
        """Discover all circuits in a topology.

        Using the list of flows per switch, run control plane
        traces to find a list of circuits."""
        all_flows = {}
        circuits = []

        for switch in self._tracer.controller.switches.values():
            all_flows[switch] = []
            if switch.ofp_version == '0x01':
                controller_port = Port10.OFPP_CONTROLLER
            else:
                controller_port = Port13.OFPP_CONTROLLER

            try:
                for flow in switch.generic_flows:
                    action_ok = False
                    in_port_ok = False
                    if 'in_port' in flow.match and flow.match['in_port'] != 0:
                        in_port_ok = True
                    if in_port_ok:
                        for action in flow.actions:
                            if action.action_type == 'output' \
                                    and action.port != controller_port:
                                action_ok = True
                    if action_ok:
                        all_flows[switch].append(flow)
            except AttributeError:
                pass

        for switch, flows in all_flows.items():
            for flow in flows:
                in_port = flow.match['in_port']
                vlan = flow.match['vlan_vid']
                if switch.ofp_version == '0x04':
                    in_port = in_port.value
                    vlan = vlan.value
                entries = {
                    'trace': {
                        'switch': {
                            'dpid': switch.dpid,
                            'in_port': in_port
                        },
                        'eth': {
                            'dl_vlan': vlan
                        }
                    }
                }
                result = self._tracer.tracepath(entries)
                circuits.append({'circuit': format_result(result),
                                 'entries': entries})

        self._circuits = clean_circuits(circuits, self._tracer.controller)

    def run_traces(self):
        """Run traces for all circuits."""

        results = []
        for circuit in self._circuits:
            entries = circuit['entries']
            result = self._tracer.tracepath(entries)
            try:
                result = format_result(result)
                if result != circuit['circuit']:
                    results.append(circuit)
            except KeyError:
                results.append(circuit)
        log.info('Results %s, tamanho %s' % (results, len(self._circuits)))
        return results

    def get_circuit(self, circuit):
        """Find the given circuit in the list of circuits."""
        for steps in self._circuits:
            endpoint_a = steps['circuit'][0]
            endpoint_z = steps['circuit'][-1]
            if circuit['dpid_a'] == endpoint_a['dpid'] and \
                circuit['port_a'] == endpoint_a['in_port'] and \
                circuit['vlan_a'] == endpoint_a['in_vlan'] and \
                circuit['dpid_z'] == endpoint_z['dpid'] and \
                circuit['port_z'] == endpoint_z['out_port'] and \
                circuit['vlan_z'] == endpoint_z['out_vlan']:
                return steps['circuit']
        return None

    def _check_trace(self, circuit, trace):
        steps = self.get_circuit(circuit)
        if steps:
            if len(steps) != len(trace) - 1:
                return False
            for i, step in enumerate(steps):
                if not self.check_step(step, trace[i]):
                    return False
        else:
            return False
        return True

    def run_important_traces(self):
        """Run SDNTrace in data plane for important circuits as defined
            by user."""
        event = KytosEvent(name='amlight/kytos_courier.slack_send')
        content = {
            'channel': 'tests',
            'source': 'amlight/sdntrace_cp'
        }

        try:
            important_circuits = settings.IMPORTANT_CIRCUITS
        except AttributeError:
            return

        for circuit in important_circuits:
            entries = {
                'trace': {
                    'switch': {
                        'dpid': circuit['dpid_a'],
                        'in_port': circuit['port_a']
                    },
                    'eth': {
                        'dl_vlan': circuit['vlan_a']
                    }
                }
            }
            result = requests.put(settings.SDNTRACE_URL, json=entries)
            trace = result.json()
            trace_id = trace['result']['trace_id']
            step_type = None
            while step_type != 'last':
                time.sleep(5)
                result = requests.get('%s/%s' %
                                      (settings.SDNTRACE_URL, trace_id))
                trace = result.json()
                step_type = trace['result'][-1]['type']
            check = self._check_trace(circuit, trace['result'])
            if check is False:
                content['m_body'] = 'Trace in data plane different from ' \
                                    'trace in control plane for circuit ' \
                                    '%s' % circuit
                event.content['message'] = content
                self._tracer.controller.buffers.app.put(event)

    @staticmethod
    def check_step(circuit_step, trace_step):
        """Check if a step in SDNTrace in data plane is what it should"""
        return circuit_step['dpid'] == trace_step['dpid'] and \
               circuit_step['in_port'] == trace_step['port']
