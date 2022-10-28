"""Automate circuit traces."""

import time

import requests
from kytos.core import KytosEvent, log
from napps.amlight.sdntrace_cp import settings
from napps.amlight.sdntrace_cp.scheduler import Scheduler
from napps.amlight.sdntrace_cp.utils import (clean_circuits, format_result,
                                             get_stored_flows)
from pyof.v0x04.common.port import PortNo as Port13


class Automate:
    """Find all circuits and automate trace execution."""

    def __init__(self, tracer):
        self._tracer = tracer
        self.ids = set()
        self.scheduler = Scheduler()

    # pylint: disable=too-many-nested-blocks, too-many-branches
    def find_circuits(self):
        """Discover all circuits in a topology.

        Using the list of stored flows from flow_manager, run control plane
        traces to find a list of circuits."""
        all_flows = {}
        circuits = []
        stored_flows = get_stored_flows()

        for switch in self._tracer.controller.switches.copy().values():
            all_flows[switch] = []
            if switch.ofp_version == '0x04':
                controller_port = Port13.OFPP_CONTROLLER

            try:
                for flow in stored_flows[switch.dpid]:
                    flow = flow['flow']
                    if 'match' not in flow:
                        continue
                    action_ok = False
                    in_port_ok = False
                    if 'in_port' in flow['match'] \
                            and flow['match']['in_port'] != 0:
                        in_port_ok = True
                    if in_port_ok:
                        for action in flow['actions']:
                            if action['action_type'] == 'output' \
                                    and action['port'] != controller_port:
                                action_ok = True
                    if action_ok:
                        all_flows[switch].append(flow)
            except AttributeError:
                pass
        for switch, flows in all_flows.items():
            for flow in flows:
                in_port = flow['match']['in_port']
                vlan = None
                if 'vlan_vid' in flow['match']:
                    vlan = flow['match']['vlan_vid']
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
        return clean_circuits(circuits, self._tracer.controller)

    def run_traces(self):
        """Run traces for all circuits."""

        results = []
        circuits = self.find_circuits()
        for circuit in circuits:
            entries = circuit['entries']
            result = self._tracer.tracepath(entries)
            try:
                result = format_result(result)
                if result != circuit['circuit']:
                    results.append(circuit)
            except KeyError:
                results.append(circuit)
        log.debug('Results %s, size %s', results, len(circuits))
        return results

    def get_circuit(self, circuit):
        """Find the given circuit in the list of circuits."""
        circuits = self.find_circuits()
        for steps in circuits:
            endpoint_a = steps['circuit'][0]
            endpoint_z = steps['circuit'][-1]
            # pylint: disable=too-many-boolean-expressions
            if (circuit['dpid_a'] == endpoint_a['dpid'] and
                    circuit['port_a'] == endpoint_a['in_port'] and
                    circuit['vlan_a'] == endpoint_a['in_vlan'] and
                    circuit['dpid_z'] == endpoint_z['dpid'] and
                    circuit['port_z'] == endpoint_z['out_port'] and
                    circuit['vlan_z'] == endpoint_z['out_vlan']):

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
            'channel': settings.SLACK_CHANNEL,
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
                result = requests.get(f'{settings.SDNTRACE_URL}/{trace_id}')
                trace = result.json()
                step_type = trace['result'][-1]['type']
            check = self._check_trace(circuit, trace['result'])
            if check is False:
                content['m_body'] = 'Trace in data plane different from ' \
                                    'trace in control plane for circuit ' \
                                    f'{circuit}'
                event.content['message'] = content
                self._tracer.controller.buffers.app.put(event)

    def schedule_id(self, id_):
        """Keep track of scheduled ids"""
        if not isinstance(id_, str):
            raise AttributeError("Invalid id type, for schedule.")
        self.ids.add(id_)
        return id_

    def schedule_traces(self, settings_=settings):
        """Check for invalid arguments from schedule"""
        if settings_.TRIGGER_SCHEDULE_TRACES:
            id_ = self.schedule_id('automatic_traces')
            trigger = settings_.SCHEDULE_TRIGGER
            kwargs = settings_.SCHEDULE_ARGS
            if (not isinstance(kwargs, dict) or
                    not isinstance(trigger, str)):
                raise AttributeError("Invalid attributes for "
                                     "job to be scheduled.")
            trigger_args = {}
            trigger_args['kwargs'] = {'trigger': trigger}
            trigger_args['kwargs'].update(kwargs)
            self.scheduler.add_callable(id_, self.run_traces,
                                        **trigger_args['kwargs'])
            return self.scheduler.get_job(id_)
        return None

    def schedule_important_traces(self, settings_=settings):
        """Check for invalid important arguments from schedule"""
        if settings_.TRIGGER_IMPORTANT_CIRCUITS:
            id_ = self.schedule_id('automatic_important_traces')
            trigger = settings_.IMPORTANT_CIRCUITS_TRIGGER
            kwargs = settings_.IMPORTANT_CIRCUITS_ARGS
            if (not isinstance(kwargs, dict) or
                    not isinstance(trigger, str)):
                raise AttributeError("Invalid attributes for "
                                     "job to be scheduled.")
            trigger_args = {}
            trigger_args['kwargs'] = {'trigger': trigger}
            trigger_args['kwargs'].update(kwargs)
            return self.scheduler.add_callable(id_,
                                               self.run_important_traces,
                                               **trigger_args['kwargs'])
        return None

    def unschedule_ids(self, id_set=None):
        """Remove ids to be unschedule"""
        if id_set is None:
            id_set = self.ids.copy()
        while id_set:
            id_ = id_set.pop()
            self.ids.discard(id_)
            self.scheduler.remove_job(id_)

    def sheduler_shutdown(self, wait):
        """Shutdown scheduler"""
        self.scheduler.shutdown(wait)

    @staticmethod
    def check_step(circuit_step, trace_step):
        """Check if a step in SDNTrace in data plane is what it should"""
        return (circuit_step['dpid'] == trace_step['dpid'] and
                circuit_step['in_port'] == trace_step['port'])
