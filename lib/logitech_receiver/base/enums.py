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


class LogitechProductCategory(NamedInts):
    Other = 0

    VirtualUsbGameController = 1
    UsbScanner = 2
    UsbCamera = 3
    UsbAudio = 4
    UsbHub = 5
    UsbSpecial = 6

    BluetoothMouse = 7
    BluetoothKeyboard = 8
    BluetoothNumpad = 9
    BluetoothRemoteControl = 10
    BluetoothReserved = 11
    BluetoothAudio = 12

    UsbBluetoothReceiver = 13
    UsbReceiver = 14

    UsbMouse = 15
    UsbRemoteControl = 16
    UsbPcGamingDevice = 17
    UsbKeyboard = 18
    UsbTrackBall = 19
    Usb3dControlDevice = 20
    UsbOtherPointingDevice = 21
    UsbConsoleGamingDevice = 22
    UsbToolsOther = 23
    UsbToolsCorded = 24
    UsbToolsTransceiver = 25

    QuadMouse = 26
    QuadKeyboard = 27
    QuadGamingDevice = 28
    QuadFapDevice = 29
    QuadMouseTransceiver = 30
    QuadDesktopTransceiver = 31
    QuadGamingTransceiver = 32

    @classmethod
    def from_pid(cls, pid: str):
        pid = int(pid, 16)

        def in_range(_id, _min, _max):
            return _min < _id < _max

        if in_range(pid, 0x0000, 0x00FF):
            return cls.VirtualUsbGameController

        if in_range(pid, 0x0400, 0x040F):
            return cls.UsbScanner

        if in_range(pid, 0x0800, 0x08FF):
            return cls.UsbCamera

        if in_range(pid, 0x0900, 0x09FF):
            return cls.UsbCamera

        if in_range(pid, 0xD000, 0xD00F):
            return cls.UsbCamera

        if in_range(pid, 0x8900, 0x89FF):
            return cls.UsbCamera

        if in_range(pid, 0x9900, 0x99FF):
            return cls.UsbCamera

        if in_range(pid, 0x0A00, 0x0AFF):
            return cls.UsbAudio

        if in_range(pid, 0x0B00, 0x0BFF):
            return cls.UsbHub

        if in_range(pid, 0x5000, 0x5FFF):
            return cls.UsbToolsTransceiver

        if in_range(pid, 0xA000, 0xAFFF):
            return cls.UsbSpecial

        if in_range(pid, 0xB000, 0xB0FF):
            return cls.BluetoothMouse

        if in_range(pid, 0xB300, 0xB3DF):
            return cls.BluetoothKeyboard

        if in_range(pid, 0xB3E0, 0xB4FF):
            return cls.BluetoothNumpad

        if in_range(pid, 0xB400, 0xB4FF):
            return cls.BluetoothRemoteControl

        if in_range(pid, 0xB500, 0xB5FF):
            return cls.BluetoothReserved

        if in_range(pid, 0xBA00, 0xBAFF):
            return cls.BluetoothAudio

        if in_range(pid, 0xC700, 0xC7FF):
            return cls.UsbBluetoothReceiver

        if in_range(pid, 0xC000, 0xC0FF):
            return cls.UsbMouse

        if in_range(pid, 0xC100, 0xC1FF):
            return cls.UsbRemoteControl

        if in_range(pid, 0xC200, 0xC2FF):
            return cls.UsbPcGamingDevice

        if in_range(pid, 0xC300, 0xC3FF):
            return cls.UsbKeyboard

        if in_range(pid, 0xC400, 0xC4FF):
            return cls.UsbTrackBall

        if in_range(pid, 0xC500, 0xC5FF):
            return cls.UsbReceiver

        if in_range(pid, 0xC600, 0xC6FF):
            return cls.Usb3dControlDevice

        if in_range(pid, 0xC800, 0xC8FF):
            return cls.UsbOtherPointingDevice

        if in_range(pid, 0xCA00, 0xCCFF):
            return cls.UsbConsoleGamingDevice

        if pid == 0xF010:
            return cls.UsbToolsCorded

        if in_range(pid, 0xF000, 0xFFFF):
            return cls.UsbToolsTransceiver

        if in_range(pid, 0x1000, 0x1FFF):
            return cls.QuadMouse

        if in_range(pid, 0x2000, 0x2FFF):
            return cls.QuadKeyboard

        if in_range(pid, 0x3000, 0x3FFF):
            return cls.QuadGamingDevice

        if in_range(pid, 0x4000, 0x4FFF):
            return cls.QuadFapDevice

        if in_range(pid, 0x8000, 0x87FF):
            return cls.QuadMouseTransceiver

        if in_range(pid, 0x8800, 0x8FFF):
            return cls.QuadDesktopTransceiver

        if in_range(pid, 0x9000, 0x9FFF):
            return cls.QuadGamingTransceiver

        return cls.Other
