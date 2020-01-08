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

from logitech_receiver.common import NamedInts


#
# Constants - most of them as defined by the official Logitech HID++ 1.0
# documentation, some of them guessed.
#


class DeviceKind(NamedInts):
    keyboard = 0x01
    mouse = 0x02
    numpad = 0x03
    presenter = 0x04
    trackball = 0x08
    touchpad = 0x09

    @classmethod
    def from_name(cls, name: str):
        for k, v in cls._mapping().items():
            if k in name:
                return v

    @classmethod
    def _mapping(cls):
        return {
            "Mouse": cls.mouse,
            "Keyboard": cls.keyboard,
            "Number Pad": cls.numpad,
            "Touchpad": cls.touchpad,
            "Trackball": cls.trackball,
        }


class PowerSwitchLocation(NamedInts):
    base = 0x01
    top_case = 0x02
    edge_of_top_right_corner = 0x03
    top_left_corner = 0x05
    bottom_left_corner = 0x06
    top_right_corner = 0x07
    bottom_right_corner = 0x08
    top_edge = 0x09
    right_edge = 0x0A
    left_edge = 0x0B
    bottom_edge = 0x0C


# Some flags are used both by devices and receivers. The Logitech documentation
# mentions that the first and last (third) byte are used for devices while the
# second is used for the receiver. In practise, the second byte is also used for
# some device-specific notifications (keyboard illumination level). Do not
# simply set all notification bits if the software does not support it. For
# example, enabling keyboard_sleep_raw makes the Sleep key a no-operation unless
# the software is updated to handle that event.
# Observations:
# - wireless and software present were seen on receivers, reserved_r1b4 as well
# - the rest work only on devices as far as we can tell right now
# In the future would be useful to have separate enums for receiver and device notification flags,
# but right now we don't know enough.
class NotificateionFlag(NamedInts):
    battery_status = 0x100000  # send battery charge notifications (0x07 or 0x0D)
    keyboard_sleep_raw = 0x020000  # system control keys such as Sleep
    keyboard_multimedia_raw = 0x010000  # consumer controls such as Mute and Calculator
    # reserved_r1b4 = 0x001000  # unknown seen on a unifying receiver
    software_present = 0x000800  # .. no idea
    keyboard_illumination = (
        0x000200  # illumination brightness level changes (by pressing keys)
    )
    wireless = 0x000100  # notify when the device wireless goes on/off-line


class Error(NamedInts):
    invalid_SubID__command = 0x01
    invalid_address = 0x02
    invalid_value = 0x03
    connection_request_failed = 0x04
    too_many_devices = 0x05
    already_exists = 0x06
    busy = 0x07
    unknown_device = 0x08
    resource_error = 0x09
    request_unavailable = 0x0A
    unsupported_parameter_value = 0x0B
    wrong_pin_code = 0x0C


class PairingErrors(NamedInts):
    device_timeout = 0x01
    device_not_supported = 0x02
    too_many_devices = 0x03
    sequence_timeout = 0x06


class BatteryAppox(NamedInts):
    empty = 0
    critical = 5
    low = 20
    good = 50
    full = 90


class Registers(NamedInts):
    """Known registers.
    Devices usually have a (small) sub-set of these. Some registers are only
    applicable to certain device kinds (e.g. smooth_scroll only applies to mice."""

    # only apply to receivers
    receiver_connection = 0x02
    receiver_pairing = 0xB2
    devices_activity = 0x2B3
    receiver_info = 0x2B5
    # only apply to devices
    mouse_button_flags = 0x01
    keyboard_hand_detection = 0x01
    battery_status = 0x07
    keyboard_fn_swap = 0x09
    battery_charge = 0x0D
    keyboard_illumination = 0x17
    three_leds = 0x51
    mouse_dpi = 0x63
    # apply to both
    notifications = 0x00
    firmware = 0xF1
