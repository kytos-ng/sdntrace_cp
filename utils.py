"""Utility functions to be used in this Napp"""

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
            new_result.update({'vlan': step['out']['vlan']})
        result.append(new_result)
    return result

def clean_circuits(circuits):
    """Remove sub-circuits."""
    cleaned_circuits = []
    for circuit in circuits:
        for other in circuits:
            if circuit == other:
                continue
            sub = True
            for step in circuit:
                if step not in other:
                    sub = False
                    break
            if sub:
                break
        if not sub:
            cleaned_circuits.append(circuit)
    return cleaned_circuits
