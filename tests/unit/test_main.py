"""Module to test the main napp file."""
from unittest.mock import patch, MagicMock

from kytos.core.interface import Interface
from kytos.lib.helpers import (
    get_interface_mock,
    get_switch_mock,
    get_controller_mock,
    get_link_mock,
    get_test_client,
)
from kytos.core.rest_api import HTTPException


# pylint: disable=too-many-public-methods, too-many-lines
class TestMain:
    """Test the Main class."""

    def setup_method(self):
        """Execute steps before each tests."""
        # The decorator run_on_thread is patched, so methods that listen
        # for events do not run on threads while tested.
        # Decorators have to be patched before the methods that are
        # decorated with them are imported.
        patch("kytos.core.helpers.run_on_thread", lambda x: x).start()
        # pylint: disable=import-outside-toplevel
        from napps.amlight.sdntrace_cp.main import Main

        controller = get_controller_mock()
        self.napp = Main(controller)

        sw1 = get_switch_mock("00:00:00:00:00:00:00:01", 0x04)
        intf_sw1 = get_interface_mock("eth1", 1, sw1)
        intf_sw1.link = None
        sw1.get_interface_by_port_no.return_value = intf_sw1
        sw2 = get_switch_mock("00:00:00:00:00:00:00:02", 0x04)
        intf_sw2 = get_interface_mock("eth1", 1, sw2)
        intf_sw2.link = None
        sw2.get_interface_by_port_no.return_value = intf_sw2
        self.napp.controller.switches = {sw1.dpid: sw1, sw2.dpid: sw2}
        self.api_client = get_test_client(controller, self.napp)
        self.base_endpoint = "amlight/sdntrace_cp/v1"
        self.trace_endpoint = f"{self.base_endpoint}/trace"
        self.traces_endpoint = f"{self.base_endpoint}/traces"

    @patch("napps.amlight.sdntrace_cp.main.Main.match_and_apply")
    def test_trace_step(self, mock_flow_match):
        """Test trace_step success result."""
        mock_flow_match.return_value = ["1"], ["entries"], 1
        switch = get_switch_mock("00:00:00:00:00:00:00:01", 0x04)

        mock_interface = Interface("interface A", 1, MagicMock())
        mock_interface.address = "00:00:00:00:00:00:00:01"

        iface1 = get_interface_mock(
            "", 1, get_switch_mock("00:00:00:00:00:00:00:01")
        )
        iface2 = get_interface_mock(
            "", 2, get_switch_mock("00:00:00:00:00:00:00:02")
        )
        mock_interface.link = get_link_mock(iface1, iface2)
        mock_interface.link.endpoint_a.port_number = 1
        mock_interface.link.endpoint_a.port_number = 2

        # Patch for utils.find_endpoint
        switch.get_interface_by_port_no.return_value = mock_interface

        entries = MagicMock()

        stored_flows = {
            "flow": {
                "table_id": 0,
                "cookie": 84114964,
                "hard_timeout": 0,
                "idle_timeout": 0,
                "priority": 10,
            },
            "flow_id": 1,
            "state": "installed",
            "switch": "00:00:00:00:00:00:00:01",
        }

        stored_flows_arg = {
            "00:00:00:00:00:00:00:01": [stored_flows]
        }

        result = self.napp.trace_step(switch, entries, stored_flows_arg)

        mock_flow_match.assert_called_once()
        assert result == {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 2,
                    "out_port": 1,
                    "entries": ["entries"],
                }

    @patch("napps.amlight.sdntrace_cp.main.Main.match_and_apply")
    def test_trace_step__no_endpoint(self, mock_flow_match):
        """Test trace_step without endpoints available for switch/port."""
        mock_flow_match.return_value = ["1"], ["entries"], 1
        switch = get_switch_mock("00:00:00:00:00:00:00:01", 0x04)

        mock_interface = Interface("interface A", 1, MagicMock())
        mock_interface.address = "00:00:00:00:00:00:00:01"
        mock_interface.link = None

        # Patch for utils.find_endpoint
        switch.get_interface_by_port_no.return_value = mock_interface

        entries = MagicMock()

        stored_flows = {
            "flow": {
                "table_id": 0,
                "cookie": 84114964,
                "hard_timeout": 0,
                "idle_timeout": 0,
                "priority": 10,
            },
            "flow_id": 1,
            "state": "installed",
            "switch": "00:00:00:00:00:00:00:01",
        }

        stored_flows_arg = {
            "00:00:00:00:00:00:00:01": [stored_flows]
        }

        result = self.napp.trace_step(switch, entries, stored_flows_arg)

        mock_flow_match.assert_called_once()
        assert result == {"entries": ["entries"], "out_port": 1}

    def test_trace_step__no_flow(self):
        """Test trace_step without flows for the switch."""
        switch = get_switch_mock("00:00:00:00:00:00:00:01")
        entries = MagicMock()

        stored_flows = {
            "flow": {
                "table_id": 0,
                "cookie": 84114964,
                "hard_timeout": 0,
                "idle_timeout": 0,
                "priority": 10,
            },
            "flow_id": 1,
            "state": "installed",
            "switch": "00:00:00:00:00:00:00:01",
        }

        stored_flows_arg = {
            "00:00:00:00:00:00:00:01": [stored_flows]
        }

        result = self.napp.trace_step(switch, entries, stored_flows_arg)
        assert result is None

    @patch("napps.amlight.sdntrace_cp.main.Main.trace_step")
    def test_tracepath(self, mock_trace_step):
        """Test tracepath with success result."""
        eth = {"dl_vlan": 100}
        dpid = {"dpid": "00:00:00:00:00:00:00:01", "in_port": 1}
        switch = {"switch": dpid, "eth": eth}
        entries = {"trace": switch}
        mock_trace_step.return_value = {
            "dpid": "00:00:00:00:00:00:00:02",
            "in_port": 2,
            "out_port": 3,
            "entries": entries,
        }

        stored_flows_arg = {
            "00:00:00:00:00:00:00:01": [],
            "00:00:00:00:00:00:00:02": [],
        }

        result = self.napp.tracepath(
                                        entries["trace"]["switch"],
                                        stored_flows_arg
                                    )

        assert result[0]["in"]["dpid"] == "00:00:00:00:00:00:00:01"
        assert result[0]["in"]["port"] == 1
        assert result[0]["in"]["type"] == "starting"
        assert result[0]["out"]["port"] == 3

        assert result[1]["in"]["dpid"] == "00:00:00:00:00:00:00:02"
        assert result[1]["in"]["port"] == 2
        assert result[1]["in"]["type"] == "intermediary"
        assert result[1]["out"]["port"] == 3

    @patch("napps.amlight.sdntrace_cp.main.Main.trace_step")
    def test_tracepath_loop(self, mock_trace_step):
        """Test tracepath with success result."""
        eth = {"dl_vlan": 100}
        dpid = {"dpid": "00:00:00:00:00:00:00:01", "in_port": 1}
        switch = {"switch": dpid, "eth": eth}
        entries = {"trace": switch}
        mock_trace_step.return_value = {
            "dpid": "00:00:00:00:00:00:00:01",
            "in_port": 1,
            "out_port": 1,
            "entries": entries,
        }

        result = self.napp.tracepath(
                                        entries["trace"]["switch"],
                                        {}
                                    )
        assert len(result) == 2
        # input interface = output interface
        assert result[0]["in"]["type"] == "starting"
        assert result[1]["in"]["type"] == "loop"

    def test_has_loop(self):
        """Test has_loop to detect a tracepath with loop."""
        trace_result = [
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "port": 2,
                },
                "out": {
                    "port": 1,
                },
            },
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "port": 2,
                },
                "out": {
                    "port": 1,
                },
            },
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "port": 3,
                },
                "out": {
                    "port": 1,
                },
            },
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "port": 3,
                },
                "out": {
                    "port": 1,
                },
            },
        ]
        trace_step = {
            "dpid": "00:00:00:00:00:00:00:03",
            "port": 3,
        }

        result = self.napp.has_loop(trace_step, trace_result)
        assert result

    def test_has_loop__fail(self):
        """Test has_loop to detect a tracepath with loop."""
        trace_result = [
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "port": 2,
                },
                "out": {
                    "port": 1,
                },
            },
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:02",
                    "port": 2,
                },
                "out": {
                    "port": 1,
                },
            },
        ]
        trace_step = {
            "dpid": "00:00:00:00:00:00:00:03",
            "port": 2,
        }

        result = self.napp.has_loop(trace_step, trace_result)
        assert not result

    @patch("napps.amlight.sdntrace_cp.main.get_stored_flows")
    async def test_trace(self, mock_stored_flows, event_loop):
        """Test trace rest call."""
        self.napp.controller.loop = event_loop
        payload = {
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                    },
                "eth": {"dl_vlan": 100},
            }
        }
        stored_flows = {
                "flow": {
                    "table_id": 0,
                    "cookie": 84114964,
                    "hard_timeout": 0,
                    "idle_timeout": 0,
                    "priority": 10,
                    "match": {"dl_vlan": 100, "in_port": 1},
                    "actions": [
                        {"action_type": "push_vlan"},
                        {"action_type": "set_vlan", "vlan_id": 200},
                        {"action_type": "output", "port": 2}
                    ],
                },
                "flow_id": 1,
                "state": "installed",
                "switch": "00:00:00:00:00:00:00:01",
        }
        mock_stored_flows.return_value = {
            "00:00:00:00:00:00:00:01": [stored_flows]
        }

        resp = await self.api_client.put(self.trace_endpoint, json=payload)
        assert resp.status_code == 200
        current_data = resp.json()
        result = current_data["result"]

        assert len(result) == 1
        assert result[0]["dpid"] == "00:00:00:00:00:00:00:01"
        assert result[0]["port"] == 1
        assert result[0]["type"] == "last"
        assert result[0]["vlan"] == 100
        assert result[0]["out"] == {"port": 2, "vlan": 200}

    @patch("napps.amlight.sdntrace_cp.main.get_stored_flows")
    async def test_trace_fail(self, mock_stored_flows, event_loop):
        """Test trace with a failed dependency."""
        self.napp.controller.loop = event_loop
        mock_stored_flows.side_effect = HTTPException(424, "failed")
        payload = {
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                    },
                "eth": {"dl_vlan": 100},
            }
        }
        response = await self.api_client.put(self.trace_endpoint, json=payload)
        assert response.status_code == 424

    @patch("napps.amlight.sdntrace_cp.main.get_stored_flows")
    async def test_get_traces(self, mock_stored_flows, event_loop):
        """Test traces rest call."""
        self.napp.controller.loop = event_loop
        payload = [{
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                    },
                "eth": {"dl_vlan": 100},
            }
        }]

        stored_flow = {
            "id": 1,
            "flow": {
                "table_id": 0,
                "cookie": 84114964,
                "hard_timeout": 0,
                "idle_timeout": 0,
                "priority": 10,
                "match": {"dl_vlan": 100, "in_port": 1},
                "actions": [
                    {"action_type": "pop_vlan"},
                    {"action_type": "output", "port": 2},
                ],
            }
        }

        mock_stored_flows.return_value = {
            "00:00:00:00:00:00:00:01": [stored_flow]
        }

        resp = await self.api_client.put(self.traces_endpoint, json=payload)
        assert resp.status_code == 200
        current_data = resp.json()
        result1 = current_data["result"]

        assert len(result1) == 1
        assert len(result1[0]) == 1
        assert result1[0][0]["dpid"] == "00:00:00:00:00:00:00:01"
        assert result1[0][0]["port"] == 1
        assert result1[0][0]["type"] == "last"
        assert result1[0][0]["vlan"] == 100
        assert result1[0][0]["out"] == {"port": 2}

    @patch("napps.amlight.sdntrace_cp.main.get_stored_flows")
    async def test_traces(self, mock_stored_flows, event_loop):
        """Test traces rest call"""
        self.napp.controller.loop = event_loop
        payload = [
                    {
                        "trace": {
                            "switch": {
                                "dpid": "00:00:00:00:00:00:00:01",
                                "in_port": 1
                            },
                            "eth": {
                                "dl_vlan": 100
                            }
                        }
                    },
                    {
                        "trace": {
                            "switch": {
                                "dpid": "00:00:00:00:00:00:00:0a",
                                "in_port": 1
                            },
                            "eth": {
                                "dl_vlan": 100
                            }
                        }
                    },
                    {
                        "trace": {
                            "switch": {
                                "dpid": "00:00:00:00:00:00:00:02",
                                "in_port": 2
                            },
                            "eth": {
                                "dl_vlan": 100
                            }
                        }
                    }
                ]

        stored_flow = {
            "id": 1,
            "flow": {
                "table_id": 0,
                "cookie": 84114964,
                "hard_timeout": 0,
                "idle_timeout": 0,
                "priority": 10,
                "match": {"dl_vlan": 100, "in_port": 1},
                "actions": [{"action_type": "output", "port": 2}],
            }
        }

        mock_stored_flows.return_value = {
            "00:00:00:00:00:00:00:01": [stored_flow],
            "00:00:00:00:00:00:00:02": [stored_flow],
        }

        resp = await self.api_client.put(self.traces_endpoint, json=payload)
        assert resp.status_code == 200
        current_data = resp.json()
        result = current_data["result"]
        assert len(result) == 3

        assert result[0][0]["dpid"] == "00:00:00:00:00:00:00:01"
        assert result[0][0]["port"] == 1
        assert result[0][0]["type"] == "last"
        assert result[0][0]["vlan"] == 100
        assert result[0][0]["out"] == {"port": 2, "vlan": 100}

        assert result[1][0]["dpid"] == "00:00:00:00:00:00:00:0a"
        assert result[1][0]["port"] == 1
        assert result[1][0]["type"] == "last"
        assert result[1][0]["vlan"] == 100
        assert result[1][0]["out"] is None

        assert result[2][0]["dpid"] == "00:00:00:00:00:00:00:02"
        assert result[2][0]["port"] == 2
        assert result[2][0]["type"] == "incomplete"
        assert result[2][0]["vlan"] == 100
        assert result[2][0]["out"] is None

    @patch("napps.amlight.sdntrace_cp.main.get_stored_flows")
    async def test_traces_fail(self, mock_stored_flows, event_loop):
        """Test traces with a failed dependency."""
        self.napp.controller.loop = event_loop
        mock_stored_flows.side_effect = HTTPException(424, "failed")
        payload = [{
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                    },
                "eth": {"dl_vlan": 100},
            }
        }]
        resp = await self.api_client.put(self.traces_endpoint, json=payload)
        assert resp.status_code == 424

    @patch("napps.amlight.sdntrace_cp.main.get_stored_flows")
    async def test_traces_with_loop(self, mock_stored_flows, event_loop):
        """Test traces rest call"""
        self.napp.controller.loop = event_loop
        payload = [
                    {
                        "trace": {
                            "switch": {
                                "dpid": "00:00:00:00:00:00:00:01",
                                "in_port": 1
                            },
                            "eth": {
                                "dl_vlan": 100
                            }
                        }
                    }
                ]

        stored_flow = {
            "id": 1,
            "flow": {
                "table_id": 0,
                "cookie": 84114964,
                "hard_timeout": 0,
                "idle_timeout": 0,
                "priority": 10,
                "match": {"dl_vlan": 100, "in_port": 1},
                "actions": [{"action_type": "output", "port": 1}],
            }
        }

        mock_stored_flows.return_value = {
            "00:00:00:00:00:00:00:01": [stored_flow],
        }

        resp = await self.api_client.put(self.traces_endpoint, json=payload)
        assert resp.status_code == 200
        current_data = resp.json()
        result = current_data["result"]
        assert len(result) == 1
        assert result[0][0]["dpid"] == "00:00:00:00:00:00:00:01"
        assert result[0][0]["port"] == 1
        assert result[0][0]["type"] == "loop"
        assert result[0][0]["vlan"] == 100
        assert result[0][0]["out"] == {"port": 1, "vlan": 100}

    @patch("napps.amlight.sdntrace_cp.main.get_stored_flows")
    async def test_traces_no_action(self, mock_stored_flows, event_loop):
        """Test traces rest call for two traces with different switches."""
        self.napp.controller.loop = event_loop
        payload = [
            {
                "trace": {
                    "switch": {
                        "dpid": "00:00:00:00:00:00:00:01",
                        "in_port": 1
                        },
                    "eth": {"dl_vlan": 100},
                }
            },
            {
                "trace": {
                    "switch": {
                        "dpid": "00:00:00:00:00:00:00:02",
                        "in_port": 1},
                    "eth": {"dl_vlan": 100},
                }
            }
        ]

        stored_flow1 = {
            "id": 1,
            "flow": {
                "table_id": 0,
                "cookie": 84114964,
                "hard_timeout": 0,
                "idle_timeout": 0,
                "priority": 10,
                "match": {"dl_vlan": 100, "in_port": 1}
            }
        }
        stored_flow2 = {
            "id": 1,
            "flow": {
                "table_id": 0,
                "cookie": 84114964,
                "hard_timeout": 0,
                "idle_timeout": 0,
                "priority": 10,
                "match": {"dl_vlan": 100, "in_port": 1},
                "actions": []
            }
        }

        mock_stored_flows.return_value = {
            "00:00:00:00:00:00:00:01": [stored_flow1],
            "00:00:00:00:00:00:00:02": [stored_flow2]
        }

        resp = await self.api_client.put(self.traces_endpoint, json=payload)
        assert resp.status_code == 200
        current_data = resp.json()
        result = current_data["result"]
        assert len(result) == 2
        assert result[0][-1]['type'] == "incomplete"
        assert result[1][-1]['type'] == "incomplete"

    @patch("napps.amlight.sdntrace_cp.main.get_stored_flows")
    async def test_get_traces_untagged(self, mock_stored_flows, event_loop):
        """Test traces rest call."""
        self.napp.controller.loop = event_loop
        payload = [{
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                    },
                "eth": {"dl_vlan": 10},
            }
        }, {
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                    }
            }
        }
        ]

        stored_flow1 = {
            "flow": {
                "match": {"dl_vlan": 0, "in_port": 1},
                "actions": [
                    {"action_type": "pop_vlan"},
                    {"action_type": "output", "port": 2},
                ],
            }
        }
        stored_flow2 = {
            "flow": {
                "match": {"in_port": 1},
                "actions": [
                    {"action_type": "pop_vlan"},
                    {"action_type": "output", "port": 3},
                ],
            }
        }
        stored_flow3 = {
            "flow": {
                "match": {"dl_vlan": 10, "in_port": 1},
                "actions": [
                    {"action_type": "pop_vlan"},
                    {"action_type": "output", "port": 1},
                ],
            }
        }
        mock_stored_flows.return_value = {
            "00:00:00:00:00:00:00:01": [
                stored_flow1,
                stored_flow2,
                stored_flow3
            ]
        }

        resp = await self.api_client.put(self.traces_endpoint, json=payload)
        assert resp.status_code == 200
        current_data = resp.json()

        result = current_data["result"]
        assert result[0][0]["type"] == "last"
        assert result[0][0]["out"] == {"port": 3}
        assert result[1][0]["type"] == "last"
        assert result[1][0]["out"] == {"port": 2}

        mock_stored_flows.return_value = {
            "00:00:00:00:00:00:00:01": [
                stored_flow3,
                stored_flow2,
                stored_flow1
            ]
        }

        resp = await self.api_client.put(self.traces_endpoint, json=payload)
        assert resp.status_code == 200
        current_data = resp.json()
        result = current_data["result"]
        assert result[0][0]["type"] == "loop"
        assert result[0][0]["out"] == {"port": 1}
        assert result[1][0]["type"] == "last"
        assert result[1][0]["out"] == {"port": 3}

    @patch("napps.amlight.sdntrace_cp.main.get_stored_flows")
    async def test_get_traces_any(self, mock_stored_flows, event_loop):
        """Test traces rest call."""
        self.napp.controller.loop = event_loop
        payload = [{
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                    },
                "eth": {"dl_vlan": 10}
            }
        }, {
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                    }
            }
        }
        ]

        stored_flow1 = {
            "flow": {
                "match": {"dl_vlan": "4096/4096", "in_port": 1},
                "actions": [
                    {"action_type": "pop_vlan"},
                    {"action_type": "output", "port": 2},
                ],
            }
        }
        stored_flow2 = {
            "flow": {
                "match": {"dl_vlan": 10, "in_port": 1},
                "actions": [
                    {"action_type": "pop_vlan"},
                    {"action_type": "output", "port": 1},
                ],
            }
        }
        stored_flow3 = {
            "flow": {
                "match": {"dl_vlan": "10/10", "in_port": 1},
                "actions": [
                    {"action_type": "pop_vlan"},
                    {"action_type": "output", "port": 3},
                ],
            }
        }
        stored_flow4 = {
            "flow": {
                "match": {"dl_vlan": "20/10", "in_port": 1},
                "actions": [
                    {"action_type": "pop_vlan"},
                    {"action_type": "output", "port": 1},
                ],
            }
        }
        mock_stored_flows.return_value = {
            "00:00:00:00:00:00:00:01": [
                stored_flow1,
                stored_flow2,
                stored_flow3,
                stored_flow4
            ]
        }

        resp = await self.api_client.put(self.traces_endpoint, json=payload)
        assert resp.status_code == 200
        current_data = resp.json()
        result = current_data["result"]
        assert result[0][0]["type"] == "last"
        assert result[0][0]["out"] == {"port": 2}
        assert result[1][0]["type"] == "incomplete"
        assert result[1][0]["out"] is None

        mock_stored_flows.return_value = {
            "00:00:00:00:00:00:00:01": [
                stored_flow4,
                stored_flow3,
                stored_flow2,
                stored_flow1
            ]
        }

        resp = await self.api_client.put(self.traces_endpoint, json=payload)
        assert resp.status_code == 200
        current_data = resp.json()
        result = current_data["result"]
        assert result[0][0]["type"] == "last"
        assert result[0][0]["out"] == {"port": 3}
        assert result[1][0]["type"] == "incomplete"
        assert result[1][0]["out"] is None
