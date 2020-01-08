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

from . import hidpp10 as _hidpp10, hidpp20 as _hidpp20
from .common import strhex as _strhex, unpack as _unpack
from .i18n import _
from .status import ALERT as _ALERT, KEYS as _K

_log = getLogger(__name__)
del getLogger
_R = _hidpp10.REGISTERS
_F = _hidpp20.FEATURE


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
    if n.sub_id == 0x4A:
        status.lock_open = bool(n.address & 0x01)
        reason = (
            _("pairing lock is open")
            if status.lock_open
            else _("pairing lock is closed")
        )
        if _log.isEnabledFor(_INFO):
            _log.info(f"{receiver}: {reason}")

        status[_K.ERROR] = None
        if status.lock_open:
            status.new_device = None

        pair_error = n.data[0]
        if pair_error:
            status[_K.ERROR] = error_string = _hidpp10.PAIRING_ERRORS[pair_error]
            status.new_device = None
            _log.warning(f"pairing error {pair_error}: {error_string}")

        status.changed(reason=reason)
        return True

    _log.warning(f"{receiver}: unhandled notification {n}")


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
            f"{device}: notification from invalid feature index {n.sub_id:02X}: {n}"
        )
        return False

    return _process_feature_notification(device, status, n, feature)


def _process_hidpp10_custom_notification(device, status, n):
    if _log.isEnabledFor(_DEBUG):
        _log.debug("%s (%s) custom notification %s", device, device.protocol, n)

    if n.sub_id in (_R.battery_status, _R.battery_charge):
        # message layout: 10 ix <register> <xx> <yy> <zz> <00>
        assert n.data[-1:] == b"\x00"
        data = chr(n.address).encode() + n.data
        charge, status_text = _hidpp10.parse_battery_status(n.sub_id, data)
        status.set_battery_info(charge, status_text)
        return True

    if n.sub_id == _R.keyboard_illumination:
        # message layout: 10 ix 17("address")  <??> <?> <??> <light level 1=off..5=max>
        # TODO anything we can do with this?
        if _log.isEnabledFor(_INFO):
            _log.info(f"illumination event: {n}")
        return True

    _log.warning(f"{device}: unrecognized {n}")


def _process_hidpp10_notification(device, status, n):
    # unpair notification
    if n.sub_id == 0x40:
        if n.address == 0x02:
            # device un-paired
            status.clear()
            device.wpid = None
            device.status = None
            if device.number in device.receiver:
                del device.receiver[device.number]
            status.changed(active=False, alert=_ALERT.ALL, reason=_("unpaired"))
        else:
            _log.warning(
                "%s: disconnection with unknown type %02X: %s", device, n.address, n
            )
        return True

    # wireless link notification
    if n.sub_id == 0x41:
        protocol_names = {
            0x01: "Bluetooth",
            0x02: "27 MHz",
            0x03: "QUAD or eQUAD",
            0x04: "eQUAD step 4 DJ",
            0x05: "DFU Lite",
            0x06: "eQUAD step 4 Lite",
            0x07: "eQUAD step 4 Gaming",
            0x08: "eQUAD step 4 for gamepads",
            0x0A: "eQUAD nano Lite",
            0x0C: "Lightspeed 1",
            0x0D: "Lightspeed 1_1",
        }
        protocol_name = protocol_names.get(n.address)
        if protocol_name:
            if _log.isEnabledFor(_DEBUG):
                wpid = _strhex(n.data[2:3] + n.data[1:2])
                assert wpid == device.wpid, f"{device} wpid mismatch, got {wpid}"

            flags = n.data[0] & 0xF0
            link_encrypted = bool(flags & 0x20)
            link_established = not (flags & 0x40)
            if _log.isEnabledFor(_DEBUG):
                sw_present = bool(flags & 0x10)
                has_payload = bool(flags & 0x80)
                _log.debug(
                    f"{device}: {protocol_name} connection notification: "
                    f"software={sw_present}, "
                    f"encrypted={link_encrypted}, "
                    f"link={link_established}, "
                    f"payload={has_payload}",
                )
            status[_K.LINK_ENCRYPTED] = link_encrypted
            status.changed(active=link_established)
        else:
            _log.warning(
                f"{device.number}: connection notification with unknown protocol {n.address:02X}: {n}"
            )

        return True

    if n.sub_id == 0x49:
        # raw input event? just ignore it
        # if n.address == 0x01, no idea what it is, but they keep on coming
        # if n.address == 0x03, appears to be an actual input event,
        #     because they only come when input happents
        return True

    # power notification
    if n.sub_id == 0x4B:
        if n.address == 0x01:
            if _log.isEnabledFor(_DEBUG):
                _log.debug(f"{device}: device powered on")
            reason = status.to_string() or _("powered on")
            status.changed(active=True, alert=_ALERT.NOTIFICATION, reason=reason)
        else:
            _log.warning(f"{device}: unknown {n}")
        return True

    _log.warning(f"{device}: unrecognized {n}")


def _process_feature_notification(device, status, n, feature):
    if feature == _F.BATTERY_STATUS:
        if n.address == 0x00:
            discharge_level = n.data[0]
            discharge_next_level = n.data[1]
            battery_status = n.data[2]
            status.set_battery_info(
                discharge_level, _hidpp20.BATTERY_STATUS(battery_status)
            )
        else:
            _log.warning(f"{device}: unknown BATTERY {n}")
        return True

    # TODO: what are REPROG_CONTROLS_V{2,3}?
    if feature == _F.REPROG_CONTROLS:
        if n.address == 0x00:
            if _log.isEnabledFor(_INFO):
                _log.info(f"{device}: reprogrammable key: {n}")
        else:
            _log.warning(f"{device}: unknown REPROGRAMMABLE KEYS {n}")
        return True

    if feature == _F.WIRELESS_DEVICE_STATUS:
        if n.address == 0x00:
            if _log.isEnabledFor(_DEBUG):
                _log.debug(f"wireless status: {n}")
            if n.data[0:3] == b"\x01\x01\x01":
                status.changed(
                    active=True, alert=_ALERT.NOTIFICATION, reason="powered on"
                )
            else:
                _log.warning(f"{device}: unknown WIRELESS {n}")
        else:
            _log.warning(f"{device}: unknown WIRELESS {n}")
        return True

    if feature == _F.SOLAR_DASHBOARD:
        if n.data[5:9] == b"GOOD":
            charge, lux, adc = _unpack("!BHH", n.data[:5])
            # guesstimate the battery voltage, emphasis on 'guess'
            # status_text = '%1.2fV' % (adc * 2.67793237653 / 0x0672)
            status_text = _hidpp20.BATTERY_STATUS.discharging

            if n.address == 0x00:
                status[_K.LIGHT_LEVEL] = None
                status.set_battery_info(charge, status_text)
            elif n.address == 0x10:
                status[_K.LIGHT_LEVEL] = lux
                if lux > 200:
                    status_text = _hidpp20.BATTERY_STATUS.recharging
                status.set_battery_info(charge, status_text)
            elif n.address == 0x20:
                if _log.isEnabledFor(_DEBUG):
                    _log.debug(f"{device}: Light Check button pressed")
                status.changed(alert=_ALERT.SHOW_WINDOW)
                # first cancel any reporting
                # device.feature_request(_F.SOLAR_DASHBOARD)
                # trigger a new report chain
                reports_count = 15
                reports_period = 2  # seconds
                device.feature_request(
                    _F.SOLAR_DASHBOARD, 0x00, reports_count, reports_period
                )
            else:
                _log.warning(f"{device}: unknown SOLAR CHARGE {n}")
        else:
            _log.warning(f"{device}: SOLAR CHARGE not GOOD? {n}")
        return True

    if feature == _F.TOUCHMOUSE_RAW_POINTS:
        if n.address == 0x00:
            if _log.isEnabledFor(_INFO):
                _log.info("%s: TOUCH MOUSE points %s", device, n)
        elif n.address == 0x10:
            touch = n.data[0]
            button_down = bool(touch & 0x02)
            mouse_lifted = bool(touch & 0x01)
            if _log.isEnabledFor(_INFO):
                _log.info(
                    f"{device}: TOUCH MOUSE status: button_down={button_down} mouse_lifted={mouse_lifted}"
                )
        else:
            _log.warning(f"{device}: unknown TOUCH MOUSE {n}")
        return True

    if feature == _F.HIRES_WHEEL:
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
                _log.info(f"{device}: WHEEL: ratchet: {ratchet}")
            return True
        else:
            _log.warning(f"{device}: unknown WHEEL {n}")
        return True

    _log.warning(
        f"{device}: unrecognized {n} for feature {feature} (index {n.sub_id:02X})"
    )
