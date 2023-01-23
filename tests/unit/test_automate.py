"""Module to test the automate.py."""
from unittest import TestCase
from unittest.mock import patch, MagicMock

from napps.amlight.sdntrace_cp.automate import Automate

from kytos.lib.helpers import get_switch_mock


# pylint: disable=too-many-public-methods, duplicate-code, protected-access
class TestAutomate(TestCase):
    """Test class Automate."""

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
        mock_find_circuits.return_value = circuits
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
    def test_check_trace(self, mock_get_circuit):
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
        result = automate._check_trace(circuit, trace)

        mock_get_circuit.assert_called_once()
        self.assertTrue(result)

    # pylint: disable=duplicate-code
    @patch("napps.amlight.sdntrace_cp.automate.Automate.get_circuit")
    def test_check_trace__short_trace(
        self, mock_get_circuit
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
        result = automate._check_trace(circuit, trace)

        mock_get_circuit.assert_called_once()
        self.assertFalse(result)

    @patch("napps.amlight.sdntrace_cp.automate.Automate.get_circuit")
    def test_check_trace__wrong_steps(
        self, mock_get_circuit
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
        result = automate._check_trace(circuit, trace)

        mock_get_circuit.assert_called_once()
        self.assertFalse(result)

    @patch("napps.amlight.sdntrace_cp.automate.Automate.get_circuit")
    def test_check_trace__no_steps(self, mock_get_circuit):
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
        result = automate._check_trace(circuit, trace)

        mock_get_circuit.assert_called_once()
        self.assertFalse(result)

    @patch("napps.amlight.sdntrace_cp.utils.requests")
    def test_run_traces__empty(self, mock_request):
        """Test run_traces with empty circuits."""
        tracer = MagicMock()
        automate = Automate(tracer)

        mock_json = MagicMock()
        mock_request.get.return_value = mock_json

        result = automate.run_traces()

        tracer.tracepath.assert_not_called()
        self.assertEqual(result, [])

    @patch("napps.amlight.sdntrace_cp.automate.Automate.find_circuits")
    def test_run_traces(self, mock_find_circuits):
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
        circuits = [
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

        mock_find_circuits.return_value = circuits
        result = automate.run_traces()

        self.assertEqual(tracer.tracepath.call_count, 2)
        self.assertEqual(result[0], circuits[0])
        self.assertEqual(result[1], circuits[1])

    @patch("napps.amlight.sdntrace_cp.utils.requests")
    def test_find_circuits(self, mock_request):
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
        stored = {}
        for switch in switches:
            flow = {'flow': {}}
            flow['flow']['match'] = {"in_port": 1}
            action = {}
            action['action_type'] = "output"
            action['port'] = 1
            flow['flow']['actions'] = [action]
            flows = [flow]
            stored[switch.dpid] = flows
            switches_dict[switch.dpid] = switch

        automate._tracer.controller.switches = switches_dict

        mock_json = MagicMock()
        mock_json.json.return_value = stored
        mock_request.get.return_value = mock_json

        circuits = automate.find_circuits()

        self.assertIsNotNone(circuits)

        self.assertEqual(len(circuits), 4)
        for item in circuits:
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
            circuits[0]["entries"]["trace"]["switch"]["dpid"],
            "00:00:00:00:00:00:00:01",
        )
        self.assertEqual(
            circuits[1]["entries"]["trace"]["switch"]["dpid"],
            "00:00:00:00:00:00:00:02",
        )
        self.assertEqual(
            circuits[2]["entries"]["trace"]["switch"]["dpid"],
            "00:00:00:00:00:00:00:03",
        )
        self.assertEqual(
            circuits[3]["entries"]["trace"]["switch"]["dpid"],
            "00:00:00:00:00:00:00:04",
        )

    @patch("napps.amlight.sdntrace_cp.utils.requests")
    def test_find_circuits__empty(self, mock_request):
        """Test find_circuits without switches."""
        tracer = MagicMock()

        automate = Automate(tracer)

        mock_json = MagicMock()
        mock_request.get.return_value = mock_json

        circuits = automate.find_circuits()

        self.assertEqual(circuits, [])

    @patch("napps.amlight.sdntrace_cp.automate.requests")
    def test_run_important_traces__empty(self, mock_requests):
        """Test run_important_traces with empty circuits to run."""
        tracer = MagicMock()

        automate = Automate(tracer)
        automate.run_important_traces()

        mock_requests.assert_not_called()

    @patch("time.sleep", return_value=None)
    @patch("napps.amlight.sdntrace_cp.automate.requests")
    @patch("napps.amlight.sdntrace_cp.automate.settings")
    @patch("napps.amlight.sdntrace_cp.utils.requests")
    def test_run_important_traces(
                                    self,
                                    mock_request_get,
                                    mock_settings,
                                    mock_requests,
                                    _
                                ):
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

        flow = {
            'flow': {
                'match': {"in_port": 1},
                'actions': [
                    {'action_type': "output", 'port': 1}
                ]
            }
        }
        stored = {
            "00:00:00:00:00:00:00:01": [flow],
            "00:00:00:00:00:00:00:02": [flow],
            "00:00:00:00:00:00:00:03": [flow],
            "00:00:00:00:00:00:00:04": [flow]
        }
        mock_json = MagicMock()
        mock_json.json.return_value = stored
        mock_request_get.get.return_value = mock_json

        automate = Automate(tracer)
        automate.run_important_traces()

    @patch("time.sleep", return_value=None)
    @patch("napps.amlight.sdntrace_cp.automate.requests")
    @patch("napps.amlight.sdntrace_cp.automate.settings")
    @patch("napps.amlight.sdntrace_cp.automate.Automate._check_trace")
    def test_run_important_traces__success(
        self, mock_check_trace, mock_settings, mock_requests, _
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

    def test_schedule_id(self):
        """Test schedule_id with proper id type"""
        tracer = MagicMock()
        automate = Automate(tracer)
        try:
            automate.schedule_id('mock_id')
            self.assertEqual(len(automate.ids), 1)
        except AttributeError:
            self.fail('schedule_id() raised an error')

    def test_schedule_id_fail(self):
        """Test schedule_id with non-string id"""
        tracer = MagicMock()
        automate = Automate(tracer)
        with self.assertRaises(AttributeError):
            automate.schedule_id(1)

    @patch("napps.amlight.sdntrace_cp.automate.settings")
    def test_schedule_traces(self, mock_settings):
        """Test schedule_traces with the arguments from settings"""
        mock_settings.TRIGGER_SCHEDULE_TRACES = True
        mock_settings.SCHEDULE_ARGS = {'seconds': 120}
        mock_settings.SCHEDULE_TRIGGER = 'interval'
        tracer = MagicMock()
        automate = Automate(tracer)
        try:
            job = automate.schedule_traces(mock_settings)
        except AttributeError:
            self.fail("automate.schedule_traces() raised an error")
        self.assertIsNotNone(job)

    @patch("napps.amlight.sdntrace_cp.automate.settings")
    def test_schedule_traces_fail(self, mock_settings):
        """Test schedule_traces with wrong arguments from settings"""
        mock_settings.TRIGGER_SCHEDULE_TRACES = True
        mock_settings.SCHEDULE_ARGS = 120
        mock_settings.SCHEDULE_TRIGGER = {'interval'}
        tracer = MagicMock()
        automate = Automate(tracer)
        with self.assertRaises(AttributeError):
            automate.schedule_traces(mock_settings)

    @patch("napps.amlight.sdntrace_cp.automate.settings")
    def test_schedule_important_traces(self, mock_settings):
        """
        Test schedule_important_traces with the arguments from settings
        """
        mock_settings.TRIGGER_IMPORTANT_CIRCUITS = True
        mock_settings.IMPORTANT_CIRCUITS_ARGS = {'seconds': 20}
        mock_settings.IMPORTANT_CIRCUITS_TRIGGER = 'interval'
        tracer = MagicMock()
        automate = Automate(tracer)
        try:
            job = automate.schedule_important_traces(mock_settings)
        except AttributeError:
            self.fail("automate.schedule_important_traces() raised an error")
        self.assertIsNotNone(job)

    @patch("napps.amlight.sdntrace_cp.automate.settings")
    def test_schedule_important_traces_fail(self, mock_settings):
        """
        Test schedule_important_traces with wrong arguments from settings
        """
        mock_settings.TRIGGER_IMPORTANT_CIRCUITS = True
        mock_settings.IMPORTANT_CIRCUITS_ARGS = 20
        mock_settings.IMPORTANT_CIRCUITS_TRIGGER = {'interval'}
        tracer = MagicMock()
        automate = Automate(tracer)
        with self.assertRaises(AttributeError):
            automate.schedule_important_traces(mock_settings)

    def test_unschedule_ids(self):
        """Test unschedule_ids with existent ids"""
        tracer = MagicMock()
        automate = Automate(tracer)
        automate.scheduler = MagicMock()
        automate.schedule_id('mock_id')
        automate.schedule_id('id_mocked')
        self.assertEqual(len(automate.ids), 2)
        id_ = {'mock_id'}
        automate.unschedule_ids(id_set=id_)
        self.assertEqual(len(automate.ids), 1)
        automate.unschedule_ids()
        self.assertEqual(len(automate.ids), 0)
