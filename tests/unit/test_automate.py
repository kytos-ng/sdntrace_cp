"""Module to test the automate.py."""
from unittest import TestCase
from unittest.mock import patch, MagicMock

from napps.amlight.sdntrace_cp.automate import Automate

from kytos.lib.helpers import get_switch_mock


# pylint: disable=too-many-public-methods, duplicate-code, protected-access
class TestAutomate(TestCase):
    """Test claas Automate."""

    @patch("napps.amlight.sdntrace_cp.automate.Automate.find_circuits")
    def test_get_circuit(self, mock_find_circuits):
        """Verify get circuit success."""
        formatted = [
            {
                "dpid": "00:00:00:00:00:00:00:01",
                "in_port": 3,
                "in_vlan": 100,
                "out_port": 2,
                "out_vlan": 200,
            },
            {
                "dpid": "00:00:00:00:00:00:00:02",
                "in_port": 3,
                "in_vlan": 200,
                "out_port": 2,
                "out_vlan": 100,
            },
            {
                "dpid": "00:00:00:00:00:00:00:03",
                "in_port": 3,
                "in_vlan": 100,
                "out_port": 2,
                "out_vlan": 200,
            },
        ]

        circuits = []
        circuits.append({"circuit": formatted, "entries": []})

        circuit = {
            "dpid_a": circuits[0]["circuit"][0]["dpid"],
            "port_a": circuits[0]["circuit"][0]["in_port"],
            "vlan_a": circuits[0]["circuit"][0]["in_vlan"],
            "dpid_z": circuits[0]["circuit"][2]["dpid"],
            "port_z": circuits[0]["circuit"][2]["out_port"],
            "vlan_z": circuits[0]["circuit"][2]["out_vlan"],
        }

        tracer = MagicMock()
        automate = Automate(tracer)
        automate._circuits = circuits

        result = automate.get_circuit(circuit)

        mock_find_circuits.assert_called_once()
        self.assertEqual(result, formatted)

    @patch("napps.amlight.sdntrace_cp.automate.Automate.find_circuits")
    def test_get_circuit_not_found(self, mock_find_circuits):
        """Verify get circuit not finding a circuit."""

        formatted = [
            {
                "dpid": "00:00:00:00:00:00:00:01",
                "in_port": 3,
                "in_vlan": 100,
                "out_port": 2,
                "out_vlan": 200,
            },
            {
                "dpid": "00:00:00:00:00:00:00:02",
                "in_port": 3,
                "in_vlan": 200,
                "out_port": 2,
                "out_vlan": 100,
            },
            {
                "dpid": "00:00:00:00:00:00:00:03",
                "in_port": 3,
                "in_vlan": 100,
                "out_port": 2,
                "out_vlan": 200,
            },
        ]

        circuits = []
        circuits.append({"circuit": formatted, "entries": []})

        circuit = {
            "dpid_a": circuits[0]["circuit"][0]["dpid"],
            "port_a": circuits[0]["circuit"][0]["in_port"],
            "vlan_a": circuits[0]["circuit"][0]["in_vlan"],
            "dpid_z": circuits[0]["circuit"][0]["dpid"],
            "port_z": circuits[0]["circuit"][0]["out_port"],
            "vlan_z": circuits[0]["circuit"][0]["out_vlan"],
        }

        tracer = MagicMock()
        automate = Automate(tracer)
        automate._circuits = circuits

        result = automate.get_circuit(circuit)

        mock_find_circuits.assert_called_once()
        self.assertIsNone(result)

    @patch("napps.amlight.sdntrace_cp.automate.Automate.find_circuits")
    def test_get_circuit_empty(self, mock_find_circuits):
        """Verify get circuit with empty circuits"""
        circuit = {
            "dpid_a": "00:00:00:00:00:00:00:01",
            "port_a": 1,
            "vlan_a": 100,
            "dpid_z": "00:00:00:00:00:00:00:03",
            "port_z": 2,
            "vlan_z": 200,
        }

        tracer = MagicMock()
        automate = Automate(tracer)
        automate._circuits = []

        result = automate.get_circuit(circuit)

        mock_find_circuits.assert_called_once()
        self.assertIsNone(result)

    def test_check_step(self):
        """Verify check_step success."""
        trace_step = {"dpid": "00:00:00:00:00:00:00:01", "port": 1}
        circuit_step = {}
        circuit_step["dpid"] = trace_step["dpid"]
        circuit_step["in_port"] = trace_step["port"]

        tracer = MagicMock()
        automate = Automate(tracer)
        result = automate.check_step(circuit_step, trace_step)

        self.assertTrue(result)

    def test_check_step_wront_dpid(self):
        """Verify if check_step fail with different dpid."""
        trace_step = {"dpid": "00:00:00:00:00:00:00:01", "port": 1}
        circuit_step = {}
        circuit_step["dpid"] = "00:00:00:00:00:00:00:02"
        circuit_step["in_port"] = trace_step["port"]

        tracer = MagicMock()
        automate = Automate(tracer)
        result = automate.check_step(circuit_step, trace_step)

        self.assertFalse(result)

    def test_check_step_wrong_port(self):
        """Verify if check_step fail with different port."""
        trace_step = {"dpid": "00:00:00:00:00:00:00:01", "port": 1}
        circuit_step = {}
        circuit_step["dpid"] = trace_step["dpid"]
        circuit_step["in_port"] = 2

        tracer = MagicMock()
        automate = Automate(tracer)
        result = automate.check_step(circuit_step, trace_step)

        self.assertFalse(result)

    @patch("napps.amlight.sdntrace_cp.automate.Automate.get_circuit")
    @patch("napps.amlight.sdntrace_cp.automate.Automate.find_circuits")
    def test_check_trace(self, mock_find_circuits, mock_get_circuit):
        """Verify _check_trace with trace finding a valid circuit."""
        circuit_steps = [
            {
                "dpid": "00:00:00:00:00:00:00:01",
                "in_port": 3,
            },
            {
                "dpid": "00:00:00:00:00:00:00:02",
                "in_port": 3,
            },
        ]
        mock_get_circuit.return_value = circuit_steps

        trace = [
            {
                "dpid": "00:00:00:00:00:00:00:01",
                "port": 3,
            },
            {
                "dpid": "00:00:00:00:00:00:00:02",
                "port": 3,
            },
            {
                "dpid": "00:00:00:00:00:00:00:03",
                "port": 3,
            },
        ]

        circuit = {
            "dpid_a": "00:00:00:00:00:00:00:01",
            "port_a": 1,
            "dpid_z": "00:00:00:00:00:00:00:03",
            "port_z": 2,
        }

        tracer = MagicMock()
        automate = Automate(tracer)
        automate._circuits = []
        result = automate._check_trace(circuit, trace)

        mock_find_circuits.assert_called_once()
        mock_get_circuit.assert_called_once()
        self.assertTrue(result)

    # pylint: disable=duplicate-code
    @patch("napps.amlight.sdntrace_cp.automate.Automate.get_circuit")
    @patch("napps.amlight.sdntrace_cp.automate.Automate.find_circuits")
    def test_check_trace__short_trace(
        self, mock_find_circuits, mock_get_circuit
    ):
        """Verify _check_trace if lenght of circuit steps is different from
        lenght of trace steps"""
        circuit_steps = [
            {
                "dpid": "00:00:00:00:00:00:00:01",
                "in_port": 3,
            },
            {
                "dpid": "00:00:00:00:00:00:00:02",
                "in_port": 3,
            },
        ]
        mock_get_circuit.return_value = circuit_steps

        trace = [
            {
                "dpid": "00:00:00:00:00:00:00:01",
                "port": 3,
            },
            {
                "dpid": "00:00:00:00:00:00:00:03",
                "port": 3,
            },
        ]

        circuit = {
            "dpid_a": "00:00:00:00:00:00:00:01",
            "port_a": 1,
            "dpid_z": "00:00:00:00:00:00:00:03",
            "port_z": 2,
        }

        tracer = MagicMock()
        automate = Automate(tracer)
        automate._circuits = []
        result = automate._check_trace(circuit, trace)

        mock_find_circuits.assert_called_once()
        mock_get_circuit.assert_called_once()
        self.assertFalse(result)

    @patch("napps.amlight.sdntrace_cp.automate.Automate.get_circuit")
    @patch("napps.amlight.sdntrace_cp.automate.Automate.find_circuits")
    def test_check_trace__wrong_steps(
        self, mock_find_circuits, mock_get_circuit
    ):
        """Verify _check_trace with circuit steps different
        from trace steps"""
        circuit_steps = [
            {
                "dpid": "00:00:00:00:00:00:00:01",
                "in_port": 3,
            },
            {
                "dpid": "00:00:00:00:00:00:00:02",
                "in_port": 3,
            },
        ]
        mock_get_circuit.return_value = circuit_steps

        trace = [
            {
                "dpid": "00:00:00:00:00:00:00:01",
                "port": 3,
            },
            {
                "dpid": "00:00:00:00:00:00:00:05",
                "port": 3,
            },
            {
                "dpid": "00:00:00:00:00:00:00:03",
                "port": 3,
            },
        ]

        circuit = {
            "dpid_a": "00:00:00:00:00:00:00:01",
            "port_a": 1,
            "dpid_z": "00:00:00:00:00:00:00:03",
            "port_z": 2,
        }

        tracer = MagicMock()
        automate = Automate(tracer)
        automate._circuits = []
        result = automate._check_trace(circuit, trace)

        mock_find_circuits.assert_called_once()
        mock_get_circuit.assert_called_once()
        self.assertFalse(result)

    @patch("napps.amlight.sdntrace_cp.automate.Automate.get_circuit")
    @patch("napps.amlight.sdntrace_cp.automate.Automate.find_circuits")
    def test_check_trace__no_steps(self, mock_find_circuits, mock_get_circuit):
        """Verify _check_trace with empty circuit steps."""
        circuit_steps = []
        mock_get_circuit.return_value = circuit_steps

        trace = MagicMock()

        circuit = {
            "dpid_a": "00:00:00:00:00:00:00:01",
            "port_a": 1,
            "dpid_z": "00:00:00:00:00:00:00:03",
            "port_z": 2,
        }

        tracer = MagicMock()
        automate = Automate(tracer)
        automate._circuits = []
        result = automate._check_trace(circuit, trace)

        mock_find_circuits.assert_called_once()
        mock_get_circuit.assert_called_once()
        self.assertFalse(result)

    def test_run_traces__empty(self):
        """Test run_traces with empty circuits."""
        tracer = MagicMock()
        automate = Automate(tracer)
        automate._circuits = []

        result = automate.run_traces()

        tracer.tracepath.assert_not_called()
        self.assertEqual(result, [])

    def test_run_traces(self):
        """Test run_traces runnin tracepaths for all circuits."""
        trace_result = [
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "port": 1,
                    "time": "2022-06-21 21:32:14.420100",
                    "type": "starting",
                }
            },
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "port": 3,
                    "time": "2022-06-21 21:32:14.420200",
                    "type": "trace",
                    "vlan": 100,
                },
                "out": {"port": 2, "vlan": 200},
            },
        ]

        tracer = MagicMock()
        tracer.tracepath.return_value = trace_result

        automate = Automate(tracer)
        automate._circuits = [
            {
                "circuit": {
                    "dpid_a": "00:00:00:00:00:00:00:01",
                    "port_a": 1,
                    "dpid_z": "00:00:00:00:00:00:00:03",
                    "port_z": 2,
                },
                "entries": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1,
                    "vlan_vid": [100],
                },
            },
            {
                "circuit": {
                    "dpid_a": "00:00:00:00:00:00:00:02",
                    "port_a": 1,
                    "dpid_z": "00:00:00:00:00:00:00:04",
                    "port_z": 2,
                },
                "entries": {
                    "dpid": "00:00:00:00:00:00:00:02",
                    "in_port": 1,
                    "vlan_vid": [100],
                },
            },
        ]

        result = automate.run_traces()

        self.assertEqual(tracer.tracepath.call_count, 2)
        self.assertEqual(result[0], automate._circuits[0])
        self.assertEqual(result[1], automate._circuits[1])

    def test_find_circuits__empty(self):
        """Test find_circuits without switches."""
        tracer = MagicMock()

        automate = Automate(tracer)
        automate.find_circuits()

        self.assertEqual(automate._circuits, [])

    def test_find_circuits(self):
        """Test find_circuits successfully finding circuits
        for all switches."""
        trace_result = [
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "port": 1,
                    "time": "2022-06-21 21:32:14.420100",
                    "type": "starting",
                }
            },
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "port": 3,
                    "time": "2022-06-21 21:32:14.420200",
                    "type": "trace",
                    "vlan": 100,
                },
                "out": {"port": 2, "vlan": 200},
            },
        ]
        tracer = MagicMock()
        tracer.tracepath.return_value = trace_result

        automate = Automate(tracer)
        switches = [
            get_switch_mock("00:00:00:00:00:00:00:01", 0x04),
            get_switch_mock("00:00:00:00:00:00:00:02", 0x04),
            get_switch_mock("00:00:00:00:00:00:00:03", 0x04),
            get_switch_mock("00:00:00:00:00:00:00:04", 0x04),
        ]
        switches_dict = {}
        for switch in switches:
            flow = MagicMock()
            in_port = MagicMock()
            in_port.value = 1
            flow.match = {"in_port": in_port}
            action = MagicMock()
            action.action_type = "output"
            action.port = 1
            flow.actions = [action]
            flows = [flow]
            switch.generic_flows = flows
            switches_dict[switch.id] = switch

        automate._tracer.controller.switches = switches_dict

        automate.find_circuits()

        self.assertIsNotNone(automate._circuits)

        self.assertEqual(len(automate._circuits), 4)
        for item in automate._circuits:
            self.assertEqual(
                item["circuit"][0]["dpid"], trace_result[0]["in"]["dpid"]
            )
            self.assertEqual(
                item["circuit"][0]["in_port"], trace_result[0]["in"]["port"]
            )
            self.assertEqual(
                item["circuit"][1]["dpid"], trace_result[1]["in"]["dpid"]
            )
            self.assertEqual(
                item["circuit"][1]["in_port"], trace_result[1]["in"]["port"]
            )
            self.assertEqual(
                item["circuit"][1]["in_vlan"], trace_result[1]["in"]["vlan"]
            )
            self.assertEqual(
                item["circuit"][1]["out_port"], trace_result[1]["out"]["port"]
            )
            self.assertEqual(
                item["circuit"][1]["out_vlan"], trace_result[1]["out"]["vlan"]
            )

        self.assertEqual(
            automate._circuits[0]["entries"]["trace"]["switch"]["dpid"],
            "00:00:00:00:00:00:00:01",
        )
        self.assertEqual(
            automate._circuits[1]["entries"]["trace"]["switch"]["dpid"],
            "00:00:00:00:00:00:00:02",
        )
        self.assertEqual(
            automate._circuits[2]["entries"]["trace"]["switch"]["dpid"],
            "00:00:00:00:00:00:00:03",
        )
        self.assertEqual(
            automate._circuits[3]["entries"]["trace"]["switch"]["dpid"],
            "00:00:00:00:00:00:00:04",
        )

    @patch("napps.amlight.sdntrace_cp.automate.requests")
    # pylint: disable=no-self-use
    def test_run_important_traces__empty(self, mock_requests):
        """Test run_important_traces with empty circuits to run."""
        tracer = MagicMock()

        automate = Automate(tracer)
        automate.run_important_traces()

        mock_requests.assert_not_called()

    @patch("napps.amlight.sdntrace_cp.automate.requests")
    @patch("napps.amlight.sdntrace_cp.automate.settings")
    def test_run_important_traces(self, mock_settings, mock_requests):
        """Test run_important_traces if control plane trace result is
        different from the data plane trace."""
        mock_settings.IMPORTANT_CIRCUITS = [
            {"dpid_a": "00:00:00:00:00:00:00:01", "port_a": 1, "vlan_a": 100}
        ]

        mock_json = MagicMock()
        mock_json.json.return_value = {
            "result": [{"type": "starting"}, {"type": "last"}]
        }
        mock_requests.get.return_value = mock_json

        def side_effect(event):
            self.assertTrue(
                event.content["message"]["source"], "amlight/sdntrace_cp"
            )
            self.assertTrue(
                event.content["message"]["m_body"],
                "Trace in data plane different from trace in control plane "
                "for circuit {'dpid_a': '00:00:00:00:00:00:00:01', "
                "'port_a': 1, 'vlan_a': 100}"
            )

        tracer = MagicMock()
        tracer.controller.buffers.app.put.side_effect = side_effect

        automate = Automate(tracer)
        automate.run_important_traces()

    @patch("napps.amlight.sdntrace_cp.automate.requests")
    @patch("napps.amlight.sdntrace_cp.automate.settings")
    @patch("napps.amlight.sdntrace_cp.automate.Automate._check_trace")
    # pylint: disable=no-self-use
    def test_run_important_traces__success(
        self, mock_check_trace, mock_settings, mock_requests
    ):
        """Verify run_important_traces if control plane trace result
        is the same result from the data plane trace."""
        # Patch to check trace with stored circuit
        mock_check_trace.return_value = True

        mock_settings.IMPORTANT_CIRCUITS = [
            {
                "dpid_a": "00:00:00:00:00:00:00:01",
                "port_a": 1,
                "vlan_a": 100,
                "dpid_z": "00:00:00:00:00:00:00:02",
                "port_z": 2,
                "vlan_z": 100,
            },
        ]

        mock_json = MagicMock()
        mock_json.json.return_value = {
            "result": [
                {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "port": 1,
                    "type": "starting",
                },
                {"dpid": "00:00:00:00:00:00:00:03", "port": 1, "type": "last"},
            ]
        }
        mock_requests.get.return_value = mock_json

        tracer = MagicMock()
        tracer.controller.buffers.app.put.side_effect = None

        automate = Automate(tracer)
        automate.run_important_traces()

        # Check if important trace dont trigger the event
        # It means that the CP trace is the same to the DP trace
        tracer.controller.buffers.app.put.assert_not_called()
