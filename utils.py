"""Utility functions to be used in this Napp"""

from kytos.core import log
from kytos.core import KytosEvent, KytosNApp

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


def convert_entries(entries):
    """ Transform entries dictionary in a plain dictionary suitable for
        matching

    :param entries: dict
    :return: plain dict
    """
    new_entries = {}
    for entry in entries['trace'].values():
        for field, value in entry.items():
            if field in TRANSLATE_NAMES:
                new_entries[TRANSLATE_NAMES[field]] = value
            else:
                new_entries[field] = value
    if 'vlan_vid' in new_entries:
        new_entries['vlan_vid'] = [new_entries['vlan_vid']]
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


def prepare_json(trace_result):
    """Prepare return json for REST call."""
    result = []
    for trace_step in trace_result:
        result.append(trace_step['in'])
    return {'result': result}


def format_result(trace):
    """Format the result for automate circuit finding"""
    result = []
    for step in trace:
        new_result = {'dpid': step['in']['dpid'],
                      'in_port': step['in']['port'],
                      'out_port': step['out']['port']}
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
        'channel': 'tests',
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
            if compare_endpoints(circuit['circuit'][0],
                                 other['circuit'][-1]) \
                    and compare_endpoints(circuit['circuit'][-1],
                                          other['circuit'][0]):
                has_return = True
        if not has_return:
            content['m_body'] = \
                'Circuit %s has no way back' % circuit['circuit']
            event.content['message'] = content
            controller.buffers.app.put(event)
    return cleaned_circuits


def compare_endpoints(endpoint1, endpoint2):
    if endpoint1['dpid'] != endpoint2['dpid']:
        return False
    if endpoint1['in_port'] != endpoint2['out_port']:
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
