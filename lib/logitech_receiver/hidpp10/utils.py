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

from logging import getLogger

from logitech_receiver.common import (
    FirmwareInfo,
    bytes2int,
    int2bytes,
    strhex,
)
from .enums import Registers, BatteryAppox
from logitech_receiver.hidpp20.enums import FirmwareKind, BatteryStatus

_log = getLogger(__name__)
del getLogger


def read_register(device, register_number, *params):
    assert device, "tried to read register %02X from invalid device %s" % (
        register_number,
        device,
    )
    # support long registers by adding a 2 in front of the register number
    request_id = 0x8100 | (int(register_number) & 0x2FF)
    return device.request(request_id, *params)


def write_register(device, register_number, *value):
    assert device, "tried to write register %02X to invalid device %s" % (
        register_number,
        device,
    )
    # support long registers by adding a 2 in front of the register number
    request_id = 0x8000 | (int(register_number) & 0x2FF)
    return device.request(request_id, *value)


def get_battery(device):
    assert device
    assert device.kind is not None
    if not device.online:
        return

    """Reads a device's battery level, if provided by the HID++ 1.0 protocol."""
    if device.protocol and device.protocol >= 2.0:
        # let's just assume HID++ 2.0 devices do not provide the battery info in a register
        return

    for r in (Registers.battery_status, Registers.battery_charge):
        if r in device.registers:
            reply = read_register(device, r)
            if reply:
                return parse_battery_status(r, reply)
            return

    # the descriptor does not tell us which register this device has, try them both
    reply = read_register(device, Registers.battery_charge)
    if reply:
        # remember this for the next time
        device.registers.append(Registers.battery_charge)
        return parse_battery_status(Registers.battery_charge, reply)

    reply = read_register(device, Registers.battery_status)
    if reply:
        # remember this for the next time
        device.registers.append(Registers.battery_status)
        return parse_battery_status(Registers.battery_status, reply)


def parse_battery_status(register, reply):
    if register == Registers.battery_charge:
        charge = reply[0]
        status_byte = reply[2] & 0xF0
        statuses = {
            0x30: BatteryStatus.discharging,
            0x50: BatteryStatus.recharging,
            0x90: BatteryStatus.full,
        }

        status_text = statuses.get(status_byte)
        return charge, status_text

    if register == Registers.battery_status:
        status_byte = reply[0]
        statuses = {
            7: BatteryAppox.full,
            5: BatteryAppox.good,
            3: BatteryAppox.low,
            1: BatteryAppox.critical,
        }
        charge = statuses.get(status_byte, BatteryAppox.empty)

        charging_byte = reply[1]
        if charging_byte == 0x00:
            status_text = BatteryStatus.discharging
        elif charging_byte & 0x21 == 0x21:
            status_text = BatteryStatus.recharging
        elif charging_byte & 0x22 == 0x22:
            status_text = BatteryStatus.full
        else:
            _log.warning(
                "could not parse 0x07 battery status: %02X (level %02X)",
                charging_byte,
                status_byte,
            )
            status_text = None

        if charging_byte & 0x03 and status_byte == 0:
            # some 'charging' notifications may come with no battery level information
            charge = None

        return charge, status_text


def get_firmware(device):
    assert device

    firmware = [None, None, None]

    reply = read_register(device, Registers.firmware, 0x01)
    if not reply:
        # won't be able to read any of it now...
        return

    fw_version = strhex(reply[1:3])
    fw_version = "%s.%s" % (fw_version[0:2], fw_version[2:4])
    reply = read_register(device, Registers.firmware, 0x02)
    if reply:
        fw_version += ".B" + strhex(reply[1:3])
    fw = FirmwareInfo(FirmwareKind.FW_VERSION, "", fw_version)
    firmware[0] = fw

    reply = read_register(device, Registers.firmware, 0x04)
    if reply:
        bl_version = strhex(reply[1:3])
        bl_version = "%s.%s" % (bl_version[0:2], bl_version[2:4])
        bl = FirmwareInfo(FirmwareKind.FW_BUILD, "", bl_version)
        firmware[1] = bl

    reply = read_register(device, Registers.firmware, 0x03)
    if reply:
        o_version = strhex(reply[1:3])
        o_version = "%s.%s" % (o_version[0:2], o_version[2:4])
        o = FirmwareInfo(FirmwareKind.BL_VERSION, "", o_version)
        firmware[2] = o

    if any(firmware):
        return tuple(f for f in firmware if f)


def set_3leds(device, battery_level=None, charging=None, warning=None):
    assert device
    assert device.kind is not None
    if not device.online:
        return

    if Registers.three_leds not in device.registers:
        return

    if battery_level is not None:
        if battery_level < BatteryAppox.critical:
            # 1 orange, and force blink
            v1, v2 = 0x22, 0x00
            warning = True
        elif battery_level < BatteryAppox.low:
            # 1 orange
            v1, v2 = 0x22, 0x00
        elif battery_level < BatteryAppox.good:
            # 1 green
            v1, v2 = 0x20, 0x00
        elif battery_level < BatteryAppox.full:
            # 2 greens
            v1, v2 = 0x20, 0x02
        else:
            # all 3 green
            v1, v2 = 0x20, 0x22
        if warning:
            # set the blinking flag for the leds already set
            v1 |= v1 >> 1
            v2 |= v2 >> 1
    elif charging:
        # blink all green
        v1, v2 = 0x30, 0x33
    elif warning:
        # 1 red
        v1, v2 = 0x02, 0x00
    else:
        # turn off all leds
        v1, v2 = 0x11, 0x11

    write_register(device, Registers.three_leds, v1, v2)


def get_notification_flags(device):
    assert device

    # Avoid a call if the device is not online,
    # or the device does not support registers.
    if device.kind is not None:
        # peripherals with protocol >= 2.0 don't support registers
        if device.protocol and device.protocol >= 2.0:
            return

    flags = read_register(device, Registers.notifications)
    if flags is not None:
        assert len(flags) == 3
        return bytes2int(flags)


def set_notification_flags(device, *flag_bits):
    assert device

    # Avoid a call if the device is not online,
    # or the device does not support registers.
    if device.kind is not None:
        # peripherals with protocol >= 2.0 don't support registers
        if device.protocol and device.protocol >= 2.0:
            return

    flag_bits = sum(int(b) for b in flag_bits)
    assert flag_bits & 0x00FFFFFF == flag_bits
    result = write_register(device, Registers.notifications, int2bytes(flag_bits, 3))
    return result is not None
