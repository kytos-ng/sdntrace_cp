"""Module to test the main napp file."""
import json
from unittest import TestCase
from unittest.mock import patch, MagicMock

from kytos.core.interface import Interface
from kytos.lib.helpers import (
    get_interface_mock,
    get_switch_mock,
    get_controller_mock,
    get_link_mock,
    get_test_client,
)


# pylint: disable=too-many-public-methods, too-many-lines
class TestMain(TestCase):
    """Test the Main class."""

    def setUp(self):
        """Execute steps before each tests.

        Set the server_name_url_url from amlight/sdntrace_cp
        """
        self.server_name_url = "http://localhost:8181/api/amlight/sdntrace_cp"

        # The decorator run_on_thread is patched, so methods that listen
        # for events do not run on threads while tested.
        # Decorators have to be patched before the methods that are
        # decorated with them are imported.
        patch("kytos.core.helpers.run_on_thread", lambda x: x).start()
        # pylint: disable=import-outside-toplevel
        from napps.amlight.sdntrace_cp.main import Main

        self.napp = Main(get_controller_mock())

    @staticmethod
    def get_napp_urls(napp):
        """Return the amlight/sdntrace_cp urls.

        The urls will be like:

        urls = [
            (options, methods, url)
        ]

        """
        controller = napp.controller
        controller.api_server.register_napp_endpoints(napp)

        urls = []
        for rule in controller.api_server.app.url_map.iter_rules():
            options = {}
            for arg in rule.arguments:
                options[arg] = f"[{0}]".format(arg)

            if f"{napp.username}/{napp.name}" in str(rule):
                urls.append((options, rule.methods, f"{str(rule)}"))

        return urls

    def test_verify_api_urls(self):
        """Verify all APIs registered."""

        expected_urls = [
            (
                {},
                {"OPTIONS", "HEAD", "PUT"},
                "/api/amlight/sdntrace_cp/trace/ ",
            ),
        ]
        urls = self.get_napp_urls(self.napp)
        self.assertEqual(len(expected_urls), len(urls))

    @patch("napps.amlight.flow_stats.main.Main.match_and_apply")
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

        result = self.napp.trace_step(switch, entries)

        mock_flow_match.assert_called_once()
        self.assertEqual(
            result,
            {
                "dpid": "00:00:00:00:00:00:00:01",
                "in_port": 2,
                "out_port": 1,
                "entries": ["entries"],
            },
        )

    @patch("napps.amlight.flow_stats.main.Main.match_and_apply")
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

        result = self.napp.trace_step(switch, entries)

        mock_flow_match.assert_called_once()
        self.assertEqual(result, {"entries": ["entries"], "out_port": 1})

    def test_trace_step__no_flow(self):
        """Test trace_step without flows for the switch."""
        switch = get_switch_mock("00:00:00:00:00:00:00:01")
        entries = MagicMock()

        result = self.napp.trace_step(switch, entries)
        self.assertIsNone(result)

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

        result = self.napp.tracepath(entries)

        self.assertEqual(result[0]["in"]["dpid"], "00:00:00:00:00:00:00:01")
        self.assertEqual(result[0]["in"]["port"], 1)
        self.assertEqual(result[0]["in"]["type"], "starting")
        self.assertEqual(result[0]["in"]["vlan"], 100)
        self.assertEqual(result[0]["out"]["port"], 3)

        self.assertEqual(result[1]["in"]["dpid"], "00:00:00:00:00:00:00:02")
        self.assertEqual(result[1]["in"]["port"], 2)
        self.assertEqual(result[1]["in"]["type"], "trace")
        self.assertEqual(result[0]["out"]["port"], 3)

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

        self.assertTrue(result)

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

        self.assertFalse(result)

    @patch("napps.amlight.sdntrace_cp.main.settings")
    def test_update_circuits(self, mock_settings):
        """Test update_circuits event listener with success."""
        mock_settings.FIND_CIRCUITS_IN_FLOWS = True

        self.napp.automate = MagicMock()
        self.napp.automate.find_circuits = MagicMock()

        event = MagicMock()
        self.napp.update_circuits(event)

        self.napp.automate.find_circuits.assert_called_once()

    @patch("napps.amlight.sdntrace_cp.main.settings")
    def test_update_circuits__no_settings(self, mock_settings):
        """Test update_circuits event listener without
        settings option enabled."""
        mock_settings.FIND_CIRCUITS_IN_FLOWS = False

        self.napp.automate = MagicMock()
        self.napp.automate.find_circuits = MagicMock()

        event = MagicMock()
        self.napp.update_circuits(event)

        self.napp.automate.find_circuits.assert_not_called()

    def test_trace(self):
        """Test trace rest call."""
        api = get_test_client(get_controller_mock(), self.napp)
        url = f"{self.server_name_url}/trace/"

        payload = {
            "trace": {
                "switch": {"dpid": "00:00:00:00:00:00:00:01", "in_port": 1},
                "eth": {"dl_vlan": 100},
            }
        }

        response = api.put(
            url, data=json.dumps(payload), content_type="application/json"
        )
        current_data = json.loads(response.data)
        result = current_data["result"]

        self.assertEqual(result[0]["dpid"], "00:00:00:00:00:00:00:01")
        self.assertEqual(result[0]["port"], 1)
        self.assertEqual(result[0]["type"], "starting")
        self.assertEqual(result[0]["vlan"], 100)
