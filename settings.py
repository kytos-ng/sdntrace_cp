# Schedule automatic traces
SCHEDULE_TRIGGER = 'interval'
SCHEDULE_ARGS = {'seconds': 40}

IMPORTANT_CIRCUITS = [{
    'dpid_a': '00:00:00:00:00:00:00:01',
    'port_a': 1,
    'vlan_a': 100,
    'dpid_z': '00:00:00:00:00:00:00:06',
    'port_z': 1,
    'vlan_z': 100,
}]
IMPORTANT_CIRCUITS_TRIGGER = 'interval'
IMPORTANT_CIRCUITS_ARGS = {'seconds': 20}
