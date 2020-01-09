from typing import NamedTuple

from logitech_receiver.common import strhex
from logitech_receiver.hidpp10.enums import SubId


class RawPacket(NamedTuple):
    report_id: int
    devnumber: int
    data: bytes


class HIDPP_Notification(NamedTuple):
    devnumber: int
    sub_id: SubId
    address: int
    data: bytes

    def __str__(self):
        return "Notification(%d,%02X,%02X,%s)" % (
            self.devnumber,
            self.sub_id,
            self.address,
            strhex(self.data),
        )
