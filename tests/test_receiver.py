from unittest.mock import patch

import hidapi
from logitech_receiver import base
from logitech_receiver.base import request


@patch.object(hidapi.udev._os, "write", new=lambda x, y: len(y))
@patch.object(hidapi.udev, "_select", new=lambda x, y, z, t: (x, [], []))
@patch.object(base, "_skip_incoming", new=lambda x, y, z: None)
class TestRequest:
    def test_receiver_info(self):
        with patch.object(
            hidapi.udev._os,
            "read",
            return_value=b"\x11\xff\x83\xb5\x03ia\x98`\x04\x06\t\x00\x00\x00\x00\x00\x00\x00\x00",
        ):
            r = request(5, 0xFF, 33717, 3)
            assert r == b"\x03ia\x98`\x04\x06\t\x00\x00\x00\x00\x00\x00\x00\x00"

    def test_receiver_info_packet(self):
        with patch.object(
            hidapi.udev._os, "read", return_value=b"\x10\xff\x81\xf1\x02\x000"
        ):
            r = request(5, 255, 33265, 2)
            assert r == b'\x02\x000'
