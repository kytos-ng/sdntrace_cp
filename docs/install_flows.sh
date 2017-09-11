#!/bin/bash

# Mininet
# mn --topo=linear,4 --controller=remote,ip=192.168.99.1

# Set to OpenFlow 1.0
ovs-vsctl set Bridge s1 protocols=OpenFlow10
ovs-vsctl set Bridge s2 protocols=OpenFlow10
ovs-vsctl set Bridge s3 protocols=OpenFlow10
ovs-vsctl set Bridge s4 protocols=OpenFlow10

# Clear Flows
ovs-ofctl del-flows s1
ovs-ofctl del-flows s2
ovs-ofctl del-flows s3
ovs-ofctl del-flows s4

# Default actions
ovs-ofctl add-flow s1 "priority=1 actions=drop"
ovs-ofctl add-flow s2 "priority=1 actions=drop"
ovs-ofctl add-flow s3 "priority=1 actions=drop"
ovs-ofctl add-flow s4 "priority=1 actions=drop"

# Default LLDP
ovs-ofctl add-flow s1 "priority=2 dl_type=0x88cc actions=output:CONTROLLER"
ovs-ofctl add-flow s2 "priority=2 dl_type=0x88cc actions=output:CONTROLLER"
ovs-ofctl add-flow s3 "priority=2 dl_type=0x88cc actions=output:CONTROLLER"
ovs-ofctl add-flow s4 "priority=2 dl_type=0x88cc actions=output:CONTROLLER"

# User flow
# h1-eth0<->s1-eth1 (OK OK)
# h4-eth0<->s4-eth1 (OK OK)

# s2-eth2<->s1-eth2 (OK OK)
# s3-eth2<->s2-eth3 (OK OK)
# s4-eth2<->s3-eth3 (OK OK)

ovs-ofctl add-flow s1 "priority=30000 in_port=1 actions=mod_vlan_vid:101,output:2"
ovs-ofctl add-flow s2 "priority=30000 in_port=2,dl_vlan=101 actions=mod_vlan_vid:102,output:3"
ovs-ofctl add-flow s3 "priority=30000 in_port=2,dl_vlan=102 actions=mod_vlan_vid:103,output:3"
#ovs-ofctl add-flow s4 "priority=30000 in_port=2,dl_vlan=103 actions=strip_vlan,output:1"
ovs-ofctl add-flow s4 "priority=30000 in_port=2,dl_vlan=103 actions=output:1"

ovs-ofctl add-flow s4 "priority=30000 in_port=1 actions=mod_vlan_vid:295,output:2"
ovs-ofctl add-flow s3 "priority=30000 in_port=3,dl_vlan=295 actions=mod_vlan_vid:296,output:2"
ovs-ofctl add-flow s2 "priority=30000 in_port=3,dl_vlan=296 actions=mod_vlan_vid:297,output:2"
ovs-ofctl add-flow s1 "priority=30000 in_port=2,dl_vlan=297 actions=output:1"
#ovs-ofctl add-flow s1 "priority=30000 in_port=2,dl_vlan=297 actions=strip_vlan,output:1"


# Tests
# template_trace_l2.json file:
# {
#    "trace" :
#    {
#        "switch": {
#            "dpid" : "00:00:00:00:00:00:00:04",
#            "in_port": 1
#        },
#        "eth" : {
#            "dl_vlan": 100,
#            "dl_type": 2048
#        }
#    }
# }
# curl -X PUT -d@template_trace_l2.json -H "Content-Type: application/json" http://192.168.99.1:8181/kytos/sdntrace/trace