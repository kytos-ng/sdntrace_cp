"""Module to test the utils.py file."""
import pytest
from unittest.mock import patch, MagicMock
from httpx import RequestError
from tenacity import RetryError
from kytos.core.interface import Interface
from kytos.lib.helpers import get_link_mock
from napps.amlight.sdntrace_cp import utils, settings


# pylint: disable=too-many-public-methods, duplicate-code, protected-access
class TestUtils():
    """Test utils.py functions."""

    @patch("httpx.get")
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

    @patch("time.sleep")
    @patch("httpx.get")
    def test_get_stored_flows_error(self, get_mock, _):
        """Test retries when get_stored_flows fails"""
        get_mock.side_effect = RequestError(MagicMock())
        with pytest.raises(RetryError):
            utils.get_stored_flows()
        assert get_mock.call_count == 3

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
        trace_result = [
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "port": 1,
                    "time": "2022-06-01 01:01:01.100000",
                    "type": "starting",
                }
            },
            {
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
        ]

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
        trace_result = [
            {
                "in": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "port": 1,
                    "time": "2022-06-01 01:01:01.100000",
                    "type": "starting",
                }
            },
            {
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
        ]

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

    @pytest.mark.parametrize(
        "endpoint1,endpoint2,result",
        [
            (
                {"dpid": "00:00:00:00:00:00:00:01"},
                {"dpid": "00:00:00:00:00:00:00:02"},
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "out_port": 2,
                    "out_vlan": 200,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 3,
                    "in_vlan": 100,
                },
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 3,
                    "in_vlan": 100,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 3,
                    "in_vlan": 100,
                },
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 3,
                    "in_vlan": 100,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "out_port": 2,
                    "out_vlan": 200,
                },
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 3,
                    "out_port": 2,
                    "in_vlan": 100,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 2,
                    "out_port": 3,
                    "out_vlan": 200,
                },
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 3,
                    "out_port": 2,
                    "in_vlan": 100,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 2,
                    "out_port": 3,
                },
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 3,
                    "out_port": 2,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 2,
                    "out_port": 3,
                    "out_vlan": 200,
                },
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 3,
                    "out_port": 2,
                    "out_vlan": 200,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 2,
                    "out_port": 3,
                    "in_vlan": 100,
                },
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 3,
                    "out_port": 2,
                    "out_vlan": 200,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 2,
                    "out_port": 3,
                },
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 3,
                    "out_port": 2,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 2,
                    "out_port": 3,
                    "in_vlan": 100,
                },
                False
            ),
            (
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "in_port": 3,
                    "in_vlan": 100,
                },
                {
                    "dpid": "00:00:00:00:00:00:00:03",
                    "out_port": 3,
                    "out_vlan": 100,
                },
                True
            ),
        ]
    )
    def test_compare_endpoints1(self, endpoint1, endpoint2, result):
        """Test for compare endpoinst for the internal conditional no.
        1 - first: Test endpoint1 dpid != endpoint2 dpid
        2 - second: Test endpoint1 without in_port
        3 - second: Test endpoint2 without out_port
        4 - second: Test endpoint1 in_port != endpoint2 out_port
        5 - third: Test endpoint1 in_vlan != endpoint2 out_vlan
        6 - first: Test endpoint1 with in_vlan and endpoint2 without out_vlan
        7 - first: Test endpoint1 without in_vlan and endpoint2 with out_vlan
        8 - fifth: Test endpoint1 out_vlan != endpoint2 in_vlan
        9 - fifth: Test endpoint1 with out_vlan and endpoint2 without in_vlan
        10 - fifth: Test endpoint1 without out_vlan and endpoint2 with in_vlan
        11 - fifth: Test endpoint1 out_vlan != endpoint2 in_vlan
        """
        assert utils._compare_endpoints(endpoint1, endpoint2) == result

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

    @pytest.mark.parametrize(
        "value,field_flow,result",
        [
            (None, 0, True),
            (None, 10, False),
            (None, "4096/4096", False),
            ([10], 0, False),
            ([10], 10, True),
            ([10], "4096/4096", True),
            ([10], 11, False),
            ([3], "5/1", True),
            ([2], "5/1", False),
        ]
    )
    def test_match_field_dl_vlan(self, value, field_flow, result):
        """Test match_field_dl_vlan"""
        assert utils.match_field_dl_vlan(value, field_flow) == result

    @pytest.mark.parametrize(
        "field,field_flow,result",
        [
            ('192.168.20.21', '192.168.20.21', True),
            ('192.168.20.21', '192.168.20.21/10', True),
            ('192.168.20.21', '192.168.20.21/32', True),
            ('192.168.20.21', '192.168.20.21/255.255.255.255', True),
            ('192.168.20.30', '192.168.20.21', False),
            ('192.200.20.30', '192.168.20.21/10', False),
            ('2002:db8::8a3f:362:7897', '2002:db8::8a3f:362:7897', True),
            ('2002:db8::8a3f:362:7897', '2002:db8::8a3f:362:7897/10', True),
            ('2002:db8::8a3f:362:7897', '2002:db8::8a3f:362:7897/128', True),
            ('2002:db8::8a3f:362:7', '2002:db8::8a3f:362:7897', False),
            ('3002:db8::9a3f:362:7897', '2002:db8::8a3f:362:7897/10', False),
        ],
    )
    def test_match_field_ip(self, field, field_flow, result):
        """Test match_field_ip"""
        assert utils.match_field_ip(field, field_flow) == result
