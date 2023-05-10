"""Module to test the utils.py file."""
from unittest import TestCase
from unittest.mock import patch, MagicMock

from kytos.core.interface import Interface
from kytos.lib.helpers import get_controller_mock, get_link_mock
from napps.amlight.sdntrace_cp import utils, settings


# pylint: disable=too-many-public-methods, duplicate-code, protected-access
class TestUtils(TestCase):
    """Test utils.py functions."""

    @patch("requests.get")
    def test_get_stored_flows(self, get_mock):
        "Test get_stored_flows"
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"result": "ok"}
        get_mock.return_value = response

        api_url = f'{settings.FLOW_MANAGER_URL}/stored_flows/?state=installed'
        result = utils.get_stored_flows()
        get_mock.assert_called_with(api_url, timeout=20)
        assert result['result'] == "ok"

    def test_convert_list_entries(self):
        """Verify convert entries with a list of one example"""
        eth = {"dl_vlan": 100}
        dpid = {"dpid": "00:00:00:00:00:00:00:01", "in_port": 1}
        switch = {"switch": dpid, "eth": eth}
        entries = {"trace": switch}

        result = utils.convert_list_entries([entries])
        expected = [{
                "dpid": "00:00:00:00:00:00:00:01",
                "in_port": 1,
                "dl_vlan": [100],
            }]
        assert result == expected

    def test_convert_entries_vlan(self):
        """Verify convert entries with simple example with vlan."""

        eth = {"dl_vlan": 100}
        dpid = {"dpid": "00:00:00:00:00:00:00:01", "in_port": 1}
        switch = {"switch": dpid, "eth": eth}
        entries = {"trace": switch}

        result = utils.convert_entries(entries)
        expected = {
                "dpid": "00:00:00:00:00:00:00:01",
                "in_port": 1,
                "dl_vlan": [100],
            }
        assert result == expected

    def test_prepare_json(self):
        """Verify prepare json with simple tracepath result."""
        trace_result = []
        trace_step = {
            "in": {
                "dpid": "00:00:00:00:00:00:00:01",
                "port": 1,
                "time": "2022-06-01 01:01:01.100000",
                "type": "starting",
            }
        }
        trace_result.append(trace_step)

        trace_step = {
            "in": {
                "dpid": "00:00:00:00:00:00:00:03",
                "port": 3,
                "time": "2022-06-01 01:01:01.100000",
                "type": "intermediary",
                "vlan": 100,
            },
            "out": {
                "port": 1,
                "vlan": 123,
            },
        }
        trace_result.append(trace_step)

        result = utils.prepare_json(trace_result)
        expected = {
                "result": [
                    {
                        "dpid": "00:00:00:00:00:00:00:01",
                        "port": 1,
                        "time": "2022-06-01 01:01:01.100000",
                        "type": "starting",
                    },
                    {
                        "dpid": "00:00:00:00:00:00:00:03",
                        "port": 3,
                        "time": "2022-06-01 01:01:01.100000",
                        "type": "intermediary",
                        "vlan": 100,
                        "out": {"port": 1, "vlan": 123},
                    },
                ]
            }
        assert result == expected

    def test_prepare_list_json(self):
        """Verify prepare list with a simple tracepath result."""
        trace_result = []
        trace_step = {
            "in": {
                "dpid": "00:00:00:00:00:00:00:01",
                "port": 1,
                "time": "2022-06-01 01:01:01.100000",
                "type": "starting",
            }
        }
        trace_result.append(trace_step)

        trace_step = {
            "in": {
                "dpid": "00:00:00:00:00:00:00:03",
                "port": 3,
                "time": "2022-06-01 01:01:01.100000",
                "type": "intermediary",
                "vlan": 100,
            },
            "out": {
                "port": 1,
                "vlan": 123,
            },
        }
        trace_result.append(trace_step)

        result = utils._prepare_json(trace_result)
        expected = [
                    {
                        "dpid": "00:00:00:00:00:00:00:01",
                        "port": 1,
                        "time": "2022-06-01 01:01:01.100000",
                        "type": "starting",
                    },
                    {
                        "dpid": "00:00:00:00:00:00:00:03",
                        "port": 3,
                        "time": "2022-06-01 01:01:01.100000",
                        "type": "intermediary",
                        "vlan": 100,
                        "out": {"port": 1, "vlan": 123},
                    },
                ]
        assert result == expected

    def test_prepare_json_empty(self):
        """Verify prepare json with empty result."""
        trace_result = []

        result = utils.prepare_json(trace_result)

        assert result == {"result": []}

    def test_compare_endpoints1(self):
        """Test for compare endpoinst for the first internal conditional."""
        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:01",
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:02",
        }

        # Test endpoint1 dpid != endpoint2 dpid
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

    def test_compare_endpoints2(self):
        """Test for compare endpoinst for the second internal conditional."""
        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "out_port": 2,
            "out_vlan": 200,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 3,
            "in_vlan": 100,
        }

        # Test endpoint1 without in_port
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 3,
            "in_vlan": 100,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 3,
            "in_vlan": 100,
        }

        # Test endpoint2 without out_port
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 3,
            "in_vlan": 100,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "out_port": 2,
            "out_vlan": 200,
        }

        # Test endpoint1 in_port != endpoint2 out_port
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

    def test_compare_endpoints3(self):
        """Test for compare endpoinst for the third internal conditional."""
        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 3,
            "out_port": 2,
            "in_vlan": 100,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 2,
            "out_port": 3,
            "out_vlan": 200,
        }

        # Test endpoint1 in_vlan != endpoint2 out_vlan
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

    def test_compare_endpoints4(self):
        """Test for compare endpoinst for the first internal conditional."""
        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 3,
            "out_port": 2,
            "in_vlan": 100,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 2,
            "out_port": 3,
        }

        # Test endpoint1 with in_vlan and endpoint2 without out_vlan
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 3,
            "out_port": 2,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 2,
            "out_port": 3,
            "out_vlan": 200,
        }

        # Test endpoint1 without in_vlan and endpoint2 with out_vlan
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

    def test_compare_endpoints5(self):
        """Test for compare endpoinst for the fifth internal conditional."""
        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:01",
            "in_port": 3,
            "out_port": 2,
            "out_vlan": 200,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:01",
            "in_port": 2,
            "out_port": 3,
            "in_vlan": 100,
        }

        # Test endpoint1 out_vlan != endpoint2 in_vlan
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

    def test_compare_endpoints6(self):
        """Test for compare endpoinst for the fifth internal conditional."""
        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:01",
            "in_port": 3,
            "out_port": 2,
            "out_vlan": 200,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:01",
            "in_port": 2,
            "out_port": 3,
        }

        # Test endpoint1 with out_vlan and endpoint2 without in_vlan
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:01",
            "in_port": 3,
            "out_port": 2,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:01",
            "in_port": 2,
            "out_port": 3,
            "in_vlan": 100,
        }

        # Test endpoint1 without out_vlan and endpoint2 with in_vlan
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert not result

    def test_compare_endpoints(self):
        """Test for compare endpoinst for the fifth internal conditional."""
        endpoint1 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "in_port": 3,
            "in_vlan": 100,
        }
        endpoint2 = {
            "dpid": "00:00:00:00:00:00:00:03",
            "out_port": 3,
            "out_vlan": 100,
        }

        # Test endpoint1 out_vlan != endpoint2 in_vlan
        result = utils._compare_endpoints(endpoint1, endpoint2)
        assert result

    def test_find_endpoint_b(self):
        """Test find endpoint with interface equals link endpoint B."""
        port = 1

        mock_interface = Interface("interface A", port, MagicMock())
        mock_interface.address = "00:00:00:00:00:00:00:01"
        mock_interface.link = get_link_mock(
            "00:00:00:00:00:00:00:02", "00:00:00:00:00:00:00:01"
        )

        mock_switch = MagicMock()
        mock_switch.get_interface_by_port_no.return_value = mock_interface
        expected = {'endpoint': mock_interface.link.endpoint_a}
        result = utils.find_endpoint(mock_switch, port)
        assert result == expected

    def test_find_endpoint_a(self):
        """Test find endpoint with interface equals link endpoint A."""
        port = 1

        mock_interface = Interface("interface A", port, MagicMock())
        mock_interface.address = "00:00:00:00:00:00:00:01"
        mock_interface.link = get_link_mock(
            "00:00:00:00:00:00:00:01", "00:00:00:00:00:00:00:03"
        )

        mock_switch = MagicMock()
        mock_switch.get_interface_by_port_no.return_value = mock_interface
        expected = {'endpoint': mock_interface.link.endpoint_b}
        result = utils.find_endpoint(mock_switch, port)
        assert result == expected

    def test_find_endpoint_link_none(self):
        """Test find endpoint without link."""
        port = 1

        mock_interface = Interface("interface A", port, MagicMock())
        mock_interface.address = "00:00:00:00:00:00:00:01"

        mock_switch = MagicMock()
        mock_switch.get_interface_by_port_no.return_value = mock_interface

        result = utils.find_endpoint(mock_switch, port)
        assert 'endpoint' in result
        assert result['endpoint'] is None

    def test_convert_vlan(self):
        """Test convert_vlan function"""
        value = 100
        result = utils.convert_vlan(value)
        assert result[0] == 100

        value = "4096/4096"
        result = utils.convert_vlan(value)
        assert result[0] == 4096
        assert result[1] == 4096

    def test_match_field_dl_vlan(self):
        """Test match_field_dl_vlan"""

        result = utils.match_field_dl_vlan(None, 0)
        assert result
        result = utils.match_field_dl_vlan(None, 10)
        assert not result
        result = utils.match_field_dl_vlan(None, "4096/4096")
        assert not result
        result = utils.match_field_dl_vlan([10], 0)
        assert not result
        result = utils.match_field_dl_vlan([10], 10)
        assert result
        result = utils.match_field_dl_vlan([10], "4096/4096")
        assert result
        result = utils.match_field_dl_vlan([10], 11)
        assert not result
        result = utils.match_field_dl_vlan([3], "5/1")
        assert result
        result = utils.match_field_dl_vlan([2], "5/1")
        assert not result

    def test_match_field_ip(self):
        """Test match_field_ip"""
        # IPv4 cases
        result = utils.match_field_ip('192.168.20.21', '192.168.20.21')
        assert result
        result = utils.match_field_ip('192.168.20.21', '192.168.20.21/10')
        assert result
        result = utils.match_field_ip('192.168.20.21', '192.168.20.21/32')
        assert result
        result = utils.match_field_ip(
                                        '192.168.20.21',
                                        '192.168.20.21/255.255.255.255'
                                    )
        assert result
        result = utils.match_field_ip('192.168.20.30', '192.168.20.21')
        assert not result
        result = utils.match_field_ip('192.200.20.30', '192.168.20.21/10')
        assert not result

        # IPv6 cases
        result = utils.match_field_ip(
                                        '2002:db8::8a3f:362:7897',
                                        '2002:db8::8a3f:362:7897'
                                    )
        assert result
        result = utils.match_field_ip(
                                        '2002:db8::8a3f:362:7897',
                                        '2002:db8::8a3f:362:7897/10'
                                    )
        assert result
        result = utils.match_field_ip(
                                        '2002:db8::8a3f:362:7897',
                                        '2002:db8::8a3f:362:7897/128'
                                    )
        assert result
        result = utils.match_field_ip(
                                        '2002:db8::8a3f:362:7',
                                        '2002:db8::8a3f:362:7897'
                                    )
        assert not result
        result = utils.match_field_ip(
                                        '3002:db8::9a3f:362:7897',
                                        '2002:db8::8a3f:362:7897/10'
                                    )
        assert not result


# pylint: disable=too-many-public-methods, too-many-lines
class TestUtilsWithController(TestCase):
    """Test utils.py."""

    def setUp(self):
        # The decorator run_on_thread is patched, so methods that listen
        # for events do not run on threads while tested.
        # Decorators have to be patched before the methods that are
        # decorated with them are imported.
        patch("kytos.core.helpers.run_on_thread", lambda x: x).start()

        self.controller = get_controller_mock()

        self.addCleanup(patch.stopall)
