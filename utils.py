"""Utility functions to be used in this Napp"""

import requests
from kytos.core import KytosEvent
from napps.amlight.sdntrace_cp import settings


def get_stored_flows(dpids: list = None, state: str = "installed"):
    """Get stored flows from flow_manager napps."""
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


def convert_entries(entries):
    """ Transform entries dictionary in a plain dictionary suitable for
        matching

    :param entries: dict
    :return: plain dict
    """
    new_entries = {}
    for entry in entries['trace'].values():
        for field, value in entry.items():
            new_entries[field] = value
    if 'dl_vlan' in new_entries:
        new_entries['dl_vlan'] = [new_entries['dl_vlan']]
    return new_entries


def convert_list_entries(entries):
    """ Transform a list of entries dictionary in a list
    of plain dictionary suitable for matching
    :param entries: list(dict)
    :return: list(plain dict)
    """
    new_entries = []
    for entry in entries:
        new_entry = convert_entries(entry)
        if new_entry:
            new_entries.append(new_entry)
    return new_entries


def find_endpoint(switch, port):
    """ Find where switch/port is connected. If it is another switch,
    returns the interface it is connected to, otherwise returns None """

    interface = switch.get_interface_by_port_no(port)
    if interface.link:
        if interface == interface.link.endpoint_a:
            return interface.link.endpoint_b
        return interface.link.endpoint_a
    return None


def _prepare_json(trace_result):
    """Auxiliar function to return the json for REST call."""
    result = []
    for trace_step in trace_result:
        result.append(trace_step['in'])
    if result:
        result[-1]["out"] = trace_result[-1].get("out")
    return result


def prepare_json(trace_result):
    """Prepare return json for REST call."""
    result = []
    if trace_result and isinstance(trace_result[0], list):
        for trace in trace_result:
            result.append(_prepare_json(trace))
    else:
        result = _prepare_json(trace_result)
    return {'result': result}


def format_result(trace):
    """Format the result for automate circuit finding"""
    result = []
    for step in trace:
        new_result = {'dpid': step['in']['dpid'],
                      'in_port': step['in']['port']}
        if 'out' in step:
            new_result.update({'out_port': step['out']['port']})
            if 'vlan' in step['out']:
                new_result.update({'out_vlan': step['out']['vlan']})
        if 'vlan' in step['in']:
            new_result.update({'in_vlan': step['in']['vlan']})
        result.append(new_result)
    return result


def clean_circuits(circuits, controller):
    """Remove sub-circuits."""
    cleaned_circuits = []
    event = KytosEvent(name='amlight/kytos_courier.slack_send')
    content = {
        'channel': settings.SLACK_CHANNEL,
        'source': 'amlight/sdntrace_cp'
    }
    for circuit in circuits:
        sub = False
        for other in circuits:
            if circuit['circuit'] == other['circuit']:
                continue
            sub = True
            for step in circuit['circuit']:
                if step not in other['circuit']:
                    sub = False
                    break
            if sub:
                break
        if not sub:
            cleaned_circuits.append(circuit)

    for circuit in cleaned_circuits:
        has_return = False
        for other in cleaned_circuits:
            if _compare_endpoints(circuit['circuit'][0],
                                  other['circuit'][-1]) \
                    and _compare_endpoints(circuit['circuit'][-1],
                                           other['circuit'][0]):
                has_return = True
        if not has_return:
            content['m_body'] = f"Circuit {circuit['circuit']} has no way back"
            event.content['message'] = content
            controller.buffers.app.put(event)
    return cleaned_circuits


# pylint: disable=too-many-return-statements
def _compare_endpoints(endpoint1, endpoint2):
    if endpoint1['dpid'] != endpoint2['dpid']:
        return False
    if (
        'in_port' not in endpoint1
        or 'out_port' not in endpoint2
        or endpoint1['in_port'] != endpoint2['out_port']
    ):
        return False
    if 'in_vlan' in endpoint1 and 'out_vlan' in endpoint2:
        if endpoint1['in_vlan'] != endpoint2['out_vlan']:
            return False
    elif 'in_vlan' in endpoint1 or 'out_vlan' in endpoint2:
        return False
    if 'out_vlan' in endpoint1 and 'in_vlan' in endpoint2:
        if endpoint1['out_vlan'] != endpoint2['in_vlan']:
            return False
    elif 'out_vlan' in endpoint1 or 'in_vlan' in endpoint2:
        return False
    return True
