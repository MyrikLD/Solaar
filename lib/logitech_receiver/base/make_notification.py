## Copyright (C) 2012-2013  Daniel Pavel
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program; if not, write to the Free Software Foundation, Inc.,
## 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from logitech_receiver.hidpp10.enums import SubId
from .schemes import HIDPP_Notification


def make_notification(devnumber, data):
    """Guess if this is a notification (and not just a request reply), and
    return a Notification tuple if it is."""
    sub_id = SubId(data[0])
    if sub_id & 0x80 == 0x80:
        # this is either a HID++1.0 register r/w, or an error reply
        return

    address = data[1]
    if (
        # standard HID++ 1.0 notification, SubId may be 0x40 - 0x7F
        (sub_id >= 0x40)
        or
        # custom HID++1.0 battery events, where SubId is 0x07/0x0D
        (
            sub_id in (SubId.BATTERY_STATUS, SubId.BATTERY_MILEAGE)
            and len(data) == 5
            and data[4:5] == b"\x00"
        )
        or
        # custom HID++1.0 illumination event, where SubId is 0x17
        (sub_id == SubId.BACKLIGHT_DURATION and len(data) == 5)
        or
        # HID++ 2.0 feature notifications have the SoftwareID 0
        (address & 0x0F == 0x00)
    ):
        return HIDPP_Notification(devnumber, sub_id, address, data[2:])
