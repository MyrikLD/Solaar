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


class ReportType(NamedInts):
    ALL = 0x00  # Reserved
    KEYBOARD = 0x01  # Standard-keyboard keys
    MOUSE = 0x02  # Mouse
    CONSUMER_KEYS = 0x03  # Consumer control keys
    POWER = 0x04  # Power keys
    MEDIACENTER = 0x08  # Microsoft MediaCenter keys (vendor specific)
    HIDPP_SHORT = 0x10  # Short HID++ messages (7 bytes)
    HIDPP_LONG = 0x11  # Long HID++ messages (20 bytes)
    HIDPP_VERY_LONG = 0x12  # Very-long HID++ messages (64 bytes)
    HIDPP_EXTRA_LONG = 0x13  # Extra-long HID++ messages (111 bytes)
    DJ_BUS_ENUM_SHORT = 0x20  # DJ bus enumerator short messages
    DJ_BUS_ENUM_LONG = 0x21


class ProtocolType(NamedInts):
    BLUETOOTH = 0x01  # Bluetooth protocol
    TWENTY_SEVEN_MHZ = 0x02  # 27 MHz protocol
    QUAD = 0x03  # Quad or eQuad step 1 .. 3  protocol
    EQUAD_DJ = 0x04  # eQuad step 4 "DJ" protocol
    DFU_LITE = 0x05  # DFU Lite protocol
    EQUAD_LITE = 0x06  # eQuad step 4 Lite protocol
    EQUAD_HIGH_RPT_RATE = (
        0x07  # eQuad step 4 gaming protocol (high report-rate gaming mice/keyboard)
    )
    EQUAD_GAMEPAD = 0x08  # eQuad step 4 protocol for gamepads

    def __str__(self):
        return {
            0x01: "Bluetooth",
            0x02: "27 MHz",
            0x03: "QUAD or eQUAD step 1-3",
            0x04: "eQUAD step 4 DJ",
            0x05: "DFU Lite",
            0x06: "eQUAD step 4 Lite",
            0x07: "eQUAD step 4 Gaming",
            0x08: "eQUAD step 4 for gamepads",
            0x0A: "eQUAD nano Lite",
            0x0C: "Lightspeed 1",
            0x0D: "Lightspeed 1_1",
        }[self.value]
