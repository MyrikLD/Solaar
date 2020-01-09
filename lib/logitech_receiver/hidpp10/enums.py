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
    headset = 0x05  # Headset (Trifecta, Reg. HIDPP_REG_CURRENT_DEVICE)
    speaker_phone = 0x06  # Speaker phone (2Face, Reg. HIDPP_REG_CURRENT_DEVICE)
    remote_control = 0x07
    trackball = 0x08
    touchpad = 0x09  # Touchpad (relative displacement)
    tablet = 0x0A
    gamepad = 0x0B
    joystick = 0x0C

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


class SubId(NamedInts):
    # HID++ notifications (0x00 .. 0x7F)
    ALL = 0x00  # Reserved
    KEYBOARD = 0x01  # Reserved for standard-keyboard keys
    MOUSE = 0x02  # Reserved for mouse
    CONSUMER_KEYS = 0x03  # Consumer control keys
    POWER = 0x04  # Power keys
    ROLLER = 0x05  # Roller
    MOUSE_EXTRA_BT = 0x06  # Mouse extra buttons
    BATTERY_STATUS = 0x07  # Battery status
    UI_EVENT = 0x08  # User interface events
    F_LOCK = 0x09  # F-Lock status
    CALC_RESULT = 0x0A  # Calculator result {long}
    MENU_ENTER = 0x0B  # Navigation menu enter
    FN_PLUS_ALPHANUMKEY = 0x0C  # Fn + alpha-numeric key
    BATTERY_MILEAGE = 0x0D  # Battery mileage
    UART_RX = 0x0E  # UART received string {very-long}
    BACKLIGHT_DURATION = 0x17  # Backlight duration update
    DEVICE_DISCONNECT = 0x40  # Device disconnection
    DEVICE_CONNECT = 0x41  # Device connection
    DEVICE_DISCOVERY = 0x42  # Device discovery (BT) {long}
    PIN_CODE_REQ = 0x43  # PIN code request
    RCV_WORKING_MODE = 0x44  # Receiver working mode (BT)
    NOTIFICATION_ERROR = 0x45  # Error notification
    RFLINK_CHANGE = 0x46  # RF link change (27 MHz)
    ENCRYPTION_KEY = 0x47  # Encryption key (27 MHz Quad) {long}
    HCI_NOTIFICATION = 0x48  # HCI notification (BT) {long very-long}
    LINK_QUALITY_INFO = 0x49  # Link quality information (eQuad) {short long}
    QUAD_LOCKING_INFO = 0x4A  # Quad locking change information (Quad eQuad)
    WL_DEV_CHANGE_INFO = 0x4B  # Wireless device change information
    HOT_NOTIFICATION = 0x50  # HOT/SYNERGY notification
    ACL_NOTIFICATION = 0x51  # ACL notification {very-long}
    VOIP_TELEPHONY_EVENT = 0x5B  # VoIP telephony event
    LED_NOTIFICATION = 0x60  # LED notification
    GEST_NOTIFICATION = 0x65  # Gesture and air feature notification
    MULTI_TOUCH_NOTIFICATION = 0x66  # Touchpad multi-touch notification {long}
    TRACEABILITY_NOTIFICATION = 0x78  # Traceability notification

    # HID++ register access (0x80 .. 0x8F)
    SET_REGISTER = 0x80  # Set short register (short request/short response)
    GET_REGISTER = 0x81  # Get short register (short request/short response)
    SET_LONG_REGISTER = 0x82  # Set long register (long request/short response) {long}
    GET_LONG_REGISTER = 0x83  # Get long register (short request/long response) {long}
    SET_VERY_LONG_REGISTER = (
        0x84  # Set very-long register (very-long request/short response) {very-long}
    )
    GET_VERY_LONG_REGISTER = (
        0x85  # Get very-long register (short request/very-long response) {very-long}
    )
    ERROR_MSG_REGISTER = 0x8F  # Error message

    # HOT (0x90 .. 0xFF)
    TRANS_INIT_ASYN = (
        0x90  # First asynchronous payload packet in a HOT stream {long very-long}
    )
    TRANS_CONT_ASYN = (
        0x91  # Next asynchronous payload packet in a HOT stream {long very-long}
    )
    TRANS_INIT_SYN = (
        0x92  # First synchronous payload packet in a HOT stream {long very-long}
    )
    TRANS_CONT_SYN = (
        0x93  # Next synchronous payload packet in a HOT stream {long very-long}
    )
    RETRY_INIT_ASYN = 0x94  # First asynchronous payload packet in a HOT stream re-sent {long very-long}
    RETRY_CONT_ASYN = 0x95  # Next asynchronous payload packet in a HOT stream re-sent {long very-long}
    RETRY_INIT_SYN = 0x96  # First synchronous payload packet in a HOT stream re-sent {long very-long}
    RETRY_CONT_SYN = (
        0x97  # Next synchronous payload packet in a HOT stream re-sent {long very-long}
    )
    SYNC = 0xFF
