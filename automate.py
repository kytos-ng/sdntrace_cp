"""Automate circuit traces."""

from pyof.v0x01.common.phy_port import Port as Port10
from pyof.v0x04.common.port import PortNo as Port13
from napps.amlight.sdntrace_cp.utils import format_result, clean_circuits


class Automate:
    """Find all circuits and automate trace execution."""

    def __init__(self, tracer):
        self._tracer = tracer
        self.circuits = []
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

            for flow in switch.metadata['generic_flows']:
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

        for switch, flows in all_flows.items():
            for flow in flows:
                in_port = flow.match['in_port']
                vlan = flow.match['vlan_vid']
                if switch.ofp_version == '0x04':
                    in_port = in_port.value
                    vlan = vlan.value
                print(switch.dpid, in_port, vlan)
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
                circuits.append(format_result(result))

        self.circuits = clean_circuits(circuits)

    def run_traces(self):
        """Run traces for all circuits."""
        pass
