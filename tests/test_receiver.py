import pytest

from logitech_receiver import hidpp10
from logitech_receiver.base import request, ReadException


class TestReq:
    def test_receiver_info(self, mock_os, mock_skip_incoming):
        mock_os.input = b"\x10\xff\x83\xb5\x03\x00\x00"
        mock_os.output = (
            b"\x11\xff\x83\xb5\x03ia\x98`\x04\x06\t\x00\x00\x00\x00\x00\x00\x00\x00"
        )

        r = request(5, 0xFF, 33717, 3)
        assert r == b"\x03ia\x98`\x04\x06\t\x00\x00\x00\x00\x00\x00\x00\x00"

    def test_receiver_info_packet(self, mock_os, mock_skip_incoming):
        mock_os.output = b"\x10\xff\x81\xf1\x02\x000"

        r = request(5, 0xFF, 33265, 2)
        assert r == b"\x02\x000"

    def test_receiver_without_unpairing(self, mock_os, mock_skip_incoming):
        mock_os.input = b"\x10\xff\x80\xb2\x00\x00\x00"
        mock_os.output = b"\x10\xff\x8f\x80\xb2\x03\x00"

        class Device:
            handle = 5

            def request(self, request_id, *params):
                return request(self.handle, 0xFF, request_id, *params)

        with pytest.raises(ReadException) as excinfo:
            hidpp10.write_register(Device(), hidpp10.Registers.receiver_pairing)

            assert excinfo.code == hidpp10.Error.invalid_value
            assert excinfo.protocol_version == 1
