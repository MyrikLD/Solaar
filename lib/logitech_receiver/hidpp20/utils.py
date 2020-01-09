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

from logging import DEBUG, getLogger
from struct import unpack
from typing import Tuple

from logitech_receiver.common import FirmwareInfo
from .enums import BatteryStatus, DeviceKind, Feature, FirmwareKind

if False:
    from logitech_receiver import PairedDevice

_log = getLogger(__name__)
del getLogger


def feature_request(device: "PairedDevice", feature: Feature, function=0x00, *params):
    if device.online and device.features and feature in device.features:
        feature_index = device.features.index(int(feature))
        return device.request((feature_index << 8) + (function & 0xFF), *params)


def get_firmware(device: "PairedDevice") -> Tuple[FirmwareInfo]:
    """Reads a device's firmware info.

    :returns: a list of FirmwareInfo tuples, ordered by firmware layer.
    """
    count = feature_request(device, Feature.DEVICE_FW_VERSION)
    if count:
        count = count[0]

        fw = []
        for index in range(0, count):
            fw_info = feature_request(device, Feature.DEVICE_FW_VERSION, 0x10, index)
            if fw_info:
                level = fw_info[0] & 0x0F
                if level == 0 or level == 1:
                    name, version_major, version_minor, build = unpack(
                        "!3sBBH", fw_info[1:8]
                    )
                    version = f"{version_major:02X}.{version_minor:02X}"
                    if build:
                        version += f".B{build:04X}"
                    extras = fw_info[9:].rstrip(b"\x00") or None
                    fw_info = FirmwareInfo(
                        FirmwareKind(level), name.decode("ascii"), version, extras
                    )
                elif level == FirmwareKind.HW_VERSION:
                    fw_info = FirmwareInfo(FirmwareKind.HW_VERSION, "", str(fw_info[1]))
                else:
                    fw_info = FirmwareInfo(FirmwareKind.BL_VERSION, "", "")

                fw.append(fw_info)
            # if _log.isEnabledFor(_DEBUG):
            # 	_log.debug("device %d firmware %s", devnumber, fw_info)
        return tuple(fw)


def get_kind(device: "PairedDevice"):
    """Reads a device's type.

    :see DeviceKind:
    :returns: a string describing the device type, or ``None`` if the device is
    not available or does not support the ``DEVICE_NAME`` feature.
    """
    kind = feature_request(device, Feature.DEVICE_NAME, 0x20)
    if kind:
        kind = kind[0]
        # if _log.isEnabledFor(_DEBUG):
        # 	_log.debug("device %d type %d = %s", devnumber, kind, DeviceKind[kind])
        return DeviceKind(kind)


def get_name(device: "PairedDevice"):
    """Reads a device's name.

    :returns: a string with the device name, or ``None`` if the device is not
    available or does not support the ``DEVICE_NAME`` feature.
    """
    name_length = feature_request(device, Feature.DEVICE_NAME)
    if name_length:
        name_length = name_length[0]

        name = b""
        while len(name) < name_length:
            fragment = feature_request(device, Feature.DEVICE_NAME, 0x10, len(name))
            if fragment:
                name += fragment[: name_length - len(name)]
            else:
                _log.error(
                    "failed to read whole name of %s (expected %d chars)",
                    device,
                    name_length,
                )
                return None

        return name.decode("ascii")


def get_battery(device: "PairedDevice"):
    """Reads a device's battery level.

    :raises FeatureNotSupported: if the device does not support this feature.
    """
    battery = feature_request(device, Feature.BATTERY_STATUS)
    if battery:
        discharge, discharge_next, status = unpack("!BBB", battery[:3])
        if _log.isEnabledFor(DEBUG):
            _log.debug(
                "device %d battery %d%% charged, next level %d%% charge, status %d = %s",
                device.number,
                discharge,
                discharge_next,
                status,
                BatteryStatus(status),
            )
        return discharge, BatteryStatus(status)


def get_keys(device: "PairedDevice"):
    # TODO: add here additional variants for other REPROG_CONTROLS
    count = feature_request(device, Feature.REPROG_CONTROLS)
    if count is None:
        count = feature_request(device, Feature.REPROG_CONTROLS_V4)
    if count:
        from .arrays import KeysArray

        return KeysArray(device, count[0])


def get_mouse_pointer_info(device: "PairedDevice") -> dict:
    pointer_info = feature_request(device, Feature.MOUSE_POINTER)
    if pointer_info:
        dpi, flags = unpack("!HB", pointer_info[:3])
        acceleration = ("none", "low", "med", "high")[flags & 0x3]
        suggest_os_ballistics = (flags & 0x04) != 0
        suggest_vertical_orientation = (flags & 0x08) != 0
        return {
            "dpi": dpi,
            "acceleration": acceleration,
            "suggest_os_ballistics": suggest_os_ballistics,
            "suggest_vertical_orientation": suggest_vertical_orientation,
        }


def get_vertical_scrolling_info(device: "PairedDevice") -> dict:
    vertical_scrolling_info = feature_request(device, Feature.VERTICAL_SCROLLING)
    if vertical_scrolling_info:
        roller, ratchet, lines = unpack("!BBB", vertical_scrolling_info[:3])
        roller_type = (
            "reserved",
            "standard",
            "reserved",
            "3G",
            "micro",
            "normal touch pad",
            "inverted touch pad",
            "reserved",
        )[roller]
        return {"roller": roller_type, "ratchet": ratchet, "lines": lines}


def get_hi_res_scrolling_info(device: "PairedDevice"):
    hi_res_scrolling_info = feature_request(device, Feature.HI_RES_SCROLLING)
    if hi_res_scrolling_info:
        mode, resolution = unpack("!BB", hi_res_scrolling_info[:2])
        return mode, resolution


def get_pointer_speed_info(device: "PairedDevice"):
    pointer_speed_info = feature_request(device, Feature.POINTER_SPEED)
    if pointer_speed_info:
        pointer_speed_hi, pointer_speed_lo = unpack("!BB", pointer_speed_info[:2])
        return pointer_speed_hi + pointer_speed_lo / 256


def get_lowres_wheel_status(device: "PairedDevice"):
    lowres_wheel_status = feature_request(device, Feature.LOWRES_WHEEL)
    if lowres_wheel_status:
        wheel_flag = unpack("!B", lowres_wheel_status[:1])[0]
        wheel_reporting = ("HID", "HID++")[wheel_flag & 0x01]
        return wheel_reporting


def get_hires_wheel(device: "PairedDevice"):
    caps = feature_request(device, Feature.HIRES_WHEEL, 0x00)
    mode = feature_request(device, Feature.HIRES_WHEEL, 0x10)
    ratchet = feature_request(device, Feature.HIRES_WHEEL, 0x030)

    if caps and mode and ratchet:
        # Parse caps
        multi, flags = unpack("!BB", caps[:2])

        has_invert = (flags & 0x08) != 0
        has_ratchet = (flags & 0x04) != 0

        # Parse mode
        wheel_mode, reserved = unpack("!BB", mode[:2])

        target = (wheel_mode & 0x01) != 0
        res = (wheel_mode & 0x02) != 0
        inv = (wheel_mode & 0x04) != 0

        # Parse Ratchet switch
        ratchet_mode, reserved = unpack("!BB", ratchet[:2])

        ratchet = (ratchet_mode & 0x01) != 0

        return multi, has_invert, has_ratchet, inv, res, target, ratchet
