"""Utility functions to be used in this Napp"""
# pylint: disable=consider-using-join
import ipaddress

import requests
from kytos.core.retry import before_sleep
from napps.amlight.sdntrace_cp import settings
from requests.exceptions import Timeout
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_random)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random(min=0.1, max=0.2),
    before_sleep=before_sleep,
    retry=retry_if_exception_type((Timeout, ConnectionError)))
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
    result = requests.get(api_url, timeout=20)
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
    if not interface:
        return None
    if interface and interface.link:
        if interface == interface.link.endpoint_a:
            return {'endpoint': interface.link.endpoint_b}
        return {'endpoint': interface.link.endpoint_a}
    return {'endpoint': None}


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


def convert_vlan(value):
    """Auxiliar function to calculate dl_vlan"""
    if isinstance(value, int):
        return value, 4095
    value, mask = map(int, value.split('/'))
    return value, mask


def match_field_dl_vlan(value, field_flow):
    """ Verify match in dl_vlan.
    value only takes an int in range [1,4095].
    0 is not allowed for value. """
    if not value:
        return field_flow == 0
    value = value[-1]
    value_flow, mask_flow = convert_vlan(field_flow)
    return value & (mask_flow & 4095) == value_flow & (mask_flow & 4095)


def match_field_ip(field, field_flow):
    "Verify match in ip fields"
    packet_address = ipaddress.ip_address(field)
    flow_network = ipaddress.ip_network(field_flow, strict=False)
    return packet_address in flow_network
