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

# Handles incoming events from the receiver/devices, updating the related
# status object as appropriate.

from logging import DEBUG as _DEBUG, INFO as _INFO, getLogger

from . import hidpp10, hidpp20
from .base.enums import ProtocolType
from .common import strhex as _strhex, unpack as _unpack
from .hidpp10 import Registers
from .hidpp10.enums import SubId
from .hidpp20 import Feature
from .i18n import _
from .status import ALERT, KEYS, KEYS_MASK

_log = getLogger(__name__)
del getLogger


def process(device, notification):
    assert device
    assert notification

    assert hasattr(device, "status")
    status = device.status
    assert status is not None

    if device.kind is None:
        return _process_receiver_notification(device, status, notification)

    return _process_device_notification(device, status, notification)


def _process_receiver_notification(receiver, status, n):
    # supposedly only 0x4x notifications arrive for the receiver
    assert n.sub_id & 0x40 == 0x40

    # pairing lock notification
    if n.sub_id == SubId.QUAD_LOCKING_INFO:
        status.lock_open = bool(n.address & 0x01)
        reason = (
            _("pairing lock is open")
            if status.lock_open
            else _("pairing lock is closed")
        )
        _log.info("%s: %s", receiver, reason)

        status[KEYS.ERROR] = None
        if status.lock_open:
            status.new_device = None

        pair_error = n.data[0]
        if pair_error:
            status[KEYS.ERROR] = error_string = hidpp10.PairingErrors(pair_error)
            status.new_device = None
            _log.warning("pairing error %s: %s", pair_error, error_string)

        status.changed(reason=reason)
        return True

    _log.warning("%s: unhandled notification %s", receiver, n)


#
#
#


def _process_device_notification(device, status, n):
    # incoming packets with SubId >= 0x80 are supposedly replies from
    # HID++ 1.0 requests, should never get here
    assert n.sub_id & 0x80 == 0

    # 0x40 to 0x7F appear to be HID++ 1.0 notifications
    if n.sub_id >= 0x40:
        return _process_hidpp10_notification(device, status, n)

    # At this point, we need to know the device's protocol, otherwise it's
    # possible to not know how to handle it.
    assert device.protocol is not None

    # some custom battery events for HID++ 1.0 devices
    if device.protocol < 2.0:
        return _process_hidpp10_custom_notification(device, status, n)

    # assuming 0x00 to 0x3F are feature (HID++ 2.0) notifications
    assert device.features
    try:
        feature = device.features[n.sub_id]
    except IndexError:
        _log.warning(
            f"{device}: notification from invalid feature index {n.sub_id}: {n}"
        )
        return False

    return _process_feature_notification(device, status, n, feature)


def _process_hidpp10_custom_notification(device, status, n):
    _log.debug("%s (%s) custom notification %s", device, device.protocol, n)

    if n.sub_id in (Registers.BATTERY_STATUS, Registers.BATTERY_MILEAGE):
        # message layout: 10 ix <register> <xx> <yy> <zz> <00>
        assert n.data[-1:] == b"\x00"
        data = chr(n.address).encode() + n.data
        charge, status_text = hidpp10.parse_battery_status(n.sub_id, data)
        status.set_battery_info(charge, status_text)
        return True

    if n.sub_id == Registers.LCD_BACKLIGHT:
        # message layout: 10 ix 17("address")  <??> <?> <??> <light level 1=off..5=max>
        # TODO anything we can do with this?
        _log.info("illumination event: %s", n)
        return True

    _log.debug("%s: unrecognized %s", device, n)


def _process_hidpp10_notification(device, status, n):
    # unpair notification
    if n.sub_id == SubId.DEVICE_DISCONNECT:
        if n.address == 0x02:
            # device un-paired
            status.clear()
            device.wpid = None
            device.status = None
            if device.number in device.receiver:
                del device.receiver[device.number]
            status.changed(active=False, alert=ALERT.ALL, reason=_("unpaired"))
        else:
            _log.warning(
                f"{device}: disconnection with unknown type {n.address:02X}: {n}"
            )
        return True

    # wireless link notification
    if n.sub_id == SubId.DEVICE_CONNECT:
        protocol_name = ProtocolType(n.address)
        if protocol_name:
            if _log.isEnabledFor(_DEBUG):
                wpid = _strhex(n.data[2:3] + n.data[1:2])
                assert wpid == device.wpid, f"{device} wpid mismatch, got {wpid}"

            flags = n.data[0] & 0xF0
            link_encrypted = bool(flags & KEYS_MASK.ENCRYPTED_MASK)
            link_established = not (flags & KEYS_MASK.NO_LINK_MASK)
            if _log.isEnabledFor(_DEBUG):
                sw_present = bool(flags & KEYS_MASK.SW_PRESENT_MASK)
                has_payload = bool(flags & KEYS_MASK.LOGITECH_MASK)
                _log.debug(
                    f"{device}: {protocol_name} connection notification: "
                    f"software={sw_present}, "
                    f"encrypted={link_encrypted}, "
                    f"link={link_established}, "
                    f"payload={has_payload}",
                )
            status[KEYS.LINK_ENCRYPTED] = link_encrypted
            status.changed(active=link_established)
        else:
            _log.warning(
                f"{device.number}: connection notification with unknown protocol {n.address:02X}: {n}"
            )

        return True

    if n.sub_id == SubId.LINK_QUALITY_INFO:
        # raw input event? just ignore it
        # if n.address == 0x01, no idea what it is, but they keep on coming
        # if n.address == 0x03, appears to be an actual input event,
        #     because they only come when input happents
        return True

    # power notification
    if n.sub_id == SubId.WL_DEV_CHANGE_INFO:
        if n.address == 0x01:
            _log.debug("%s: device powered on", device)
            reason = status.to_string() or _("powered on")
            status.changed(active=True, alert=ALERT.NOTIFICATION, reason=reason)
        else:
            _log.warning("%s: unknown %s", device, n)
        return True

    _log.debug("%s: unrecognized %s", device, n)


def _process_feature_notification(device, status, n, feature: Feature):
    if feature == Feature.BATTERY_STATUS:
        if n.address == 0x00:
            discharge_level = n.data[0]
            discharge_next_level = n.data[1]
            battery_status = n.data[2]
            status.set_battery_info(
                discharge_level, hidpp20.BatteryStatus(battery_status)
            )
        else:
            _log.warning("%s: unknown BATTERY %s", device, n)
        return True

    # TODO: what are REPROG_CONTROLS_V{2,3}?
    if feature == Feature.REPROG_CONTROLS:
        if n.address == 0x00:
            _log.info("%s: reprogrammable key: %s", device, n)
        else:
            _log.warning("%s: unknown REPROGRAMMABLE KEYS %s", device, n)
        return True

    if feature == Feature.WIRELESS_DEVICE_STATUS:
        if n.address == 0x00:
            _log.debug("wireless status: %s", n)
            if n.data[0:3] == b"\x01\x01\x01":
                status.changed(
                    active=True, alert=ALERT.NOTIFICATION, reason="powered on"
                )
            else:
                _log.warning("%s: unknown WIRELESS %s", device, n)
        else:
            _log.warning("%s: unknown WIRELESS %s", device, n)
        return True

    if feature == Feature.SOLAR_DASHBOARD:
        if n.data[5:9] == b"GOOD":
            charge, lux, adc = _unpack("!BHH", n.data[:5])
            # guesstimate the battery voltage, emphasis on 'guess'
            # status_text = '%1.2fV' % (adc * 2.67793237653 / 0x0672)
            status_text = hidpp20.BatteryStatus.discharging

            if n.address == 0x00:
                status[KEYS.LIGHT_LEVEL] = None
                status.set_battery_info(charge, status_text)
            elif n.address == 0x10:
                status[KEYS.LIGHT_LEVEL] = lux
                if lux > 200:
                    status_text = hidpp20.BatteryStatus.recharging
                status.set_battery_info(charge, status_text)
            elif n.address == 0x20:
                _log.debug("%s: Light Check button pressed", device)
                status.changed(alert=ALERT.SHOW_WINDOW)
                # first cancel any reporting
                # device.feature_request(Feature.SOLAR_DASHBOARD)
                # trigger a new report chain
                reports_count = 15
                reports_period = 2  # seconds
                device.feature_request(
                    Feature.SOLAR_DASHBOARD, 0x00, reports_count, reports_period
                )
            else:
                _log.warning("%s: unknown SOLAR CHARGE %s", device, n)
        else:
            _log.warning("%s: SOLAR CHARGE not GOOD? %s", device, n)
        return True

    if feature == Feature.TOUCHMOUSE_RAW_POINTS:
        if n.address == 0x00:
            _log.info("%s: TOUCH MOUSE points %s", device, n)
        elif n.address == 0x10:
            touch = n.data[0]
            button_down = bool(touch & 0x02)
            mouse_lifted = bool(touch & 0x01)
            _log.info(
                "%s: TOUCH MOUSE status: button_down=%s mouse_lifted=%s",
                device,
                button_down,
                mouse_lifted,
            )
        else:
            _log.warning("%s: unknown TOUCH MOUSE %s", device, n)
        return True

    if feature == Feature.HIRES_WHEEL:
        if n.address == 0x00:
            if _log.isEnabledFor(_INFO):
                flags, delta_v = _unpack(">bh", n.data[:3])
                high_res = (flags & 0x10) != 0
                periods = flags & 0x0F
                _log.info(
                    f"{device}: WHEEL: res: {high_res} periods: {periods} delta V:{delta_v:<3}"
                )
            return True
        elif n.address == 0x10:
            if _log.isEnabledFor(_INFO):
                flags = n.data[0]
                ratchet = flags & 0x01
                _log.info("%s: WHEEL: ratchet: %s", device, ratchet)
            return True
        else:
            _log.warning("%s: unknown WHEEL %s", device, n)
        return True

    _log.debug(f"{device}: unrecognized {n} for feature {feature} (index {n.sub_id})")
