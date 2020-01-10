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

from enum import Enum
from logging import DEBUG as _DEBUG, getLogger
from time import time as _timestamp

from . import hidpp10 as _hidpp10, hidpp20 as _hidpp20
from .i18n import _, ngettext

_log = getLogger(__name__)
del getLogger
_R = _hidpp10.Registers

#
#
#


class ALERT(int, Enum):
    NONE = 0x00
    NOTIFICATION = 0x01
    SHOW_WINDOW = 0x02
    ATTENTION = 0x04
    ALL = 0xFF


class KEYS(int, Enum):
    BATTERY_LEVEL = 1
    BATTERY_CHARGING = 2
    BATTERY_STATUS = 3
    LIGHT_LEVEL = 4
    LINK_ENCRYPTED = 5
    NOTIFICATION_FLAGS = 6
    ERROR = 7


class KEYS_MASK(int, Enum):
    SW_PRESENT_MASK = 1 << 4
    ENCRYPTED_MASK = 1 << 5
    NO_LINK_MASK = 1 << 6
    LOGITECH_MASK = 1 << 7


# If the battery charge is under this percentage, trigger an attention event
# (blink systray icon/notification/whatever).
_BATTERY_ATTENTION_LEVEL = 5

# If no updates have been receiver from the device for a while, ping the device
# and update it status accordingly.
# _STATUS_TIMEOUT = 5 * 60  # seconds
_LONG_SLEEP = 15 * 60  # seconds


#
#
#


def attach_to(device, changed_callback):
    assert device
    assert changed_callback

    if not hasattr(device, "status") or device.status is None:
        if device.kind is None:
            device.status = ReceiverStatus(device, changed_callback)
        else:
            device.status = DeviceStatus(device, changed_callback)


#
#
#


class ReceiverStatus(dict):
    """The 'runtime' status of a receiver, mostly about the pairing process --
    is the pairing lock open or closed, any pairing errors, etc.
    """

    def __init__(self, receiver, changed_callback):
        assert receiver
        self._receiver = receiver

        assert changed_callback
        self._changed_callback = changed_callback

        # self.updated = 0

        self.lock_open = False
        self.new_device = None

        self[KEYS.ERROR] = None

    def __str__(self):
        count = len(self._receiver)
        return (
            _("No paired devices.")
            if count == 0
            else ngettext(
                "%(count)s paired device.", "%(count)s paired devices.", count
            )
            % {"count": count}
        )

    def changed(self, alert=ALERT.NOTIFICATION, reason=None):
        # self.updated = _timestamp()
        self._changed_callback(self._receiver, alert=alert, reason=reason)


#
#
#


class DeviceStatus(dict):
    """Holds the 'runtime' status of a peripheral -- things like
    active/inactive, battery charge, lux, etc. It updates them mostly by
    processing incoming notification events from the device itself.
    """

    def __init__(self, device, changed_callback):
        assert device
        self._device = device

        assert changed_callback
        self._changed_callback = changed_callback

        # is the device active?
        self._active = None

        # timestamp of when this status object was last updated
        self.updated = 0

    def to_string(self):
        def _items():
            comma = False

            battery_level = self.get(KEYS.BATTERY_LEVEL)
            if battery_level is not None:
                if hasattr(battery_level, "name"):
                    yield _("Battery: %(level)s") % {"level": _(battery_level.name)}
                else:
                    yield _("Battery: %(percent)d%%") % {"percent": battery_level}

                battery_status = self.get(KEYS.BATTERY_STATUS)
                if battery_status is not None:
                    yield " (%s)" % _(str(battery_status))

                comma = True

            light_level = self.get(KEYS.LIGHT_LEVEL)
            if light_level is not None:
                if comma:
                    yield ", "
                yield _("Lighting: %(level)s lux") % {"level": light_level}

        return "".join(i for i in _items())

    def __repr__(self):
        return "{" + ", ".join("'%s': %r" % (k, v) for k, v in self.items()) + "}"

    def __bool__(self):
        return bool(self._active)

    def set_battery_info(self, level, status, timestamp=None):
        _log.debug("%s: battery %s, %s", self._device, level, status)

        if level is None:
            # Some notifications may come with no battery level info, just
            # charging state info, so assume the level is unchanged.
            level = self.get(KEYS.BATTERY_LEVEL)
        else:
            assert isinstance(level, int)

        # TODO: this is also executed when pressing Fn+F7 on K800.
        old_level, self[KEYS.BATTERY_LEVEL] = self.get(KEYS.BATTERY_LEVEL), level
        old_status, self[KEYS.BATTERY_STATUS] = self.get(KEYS.BATTERY_STATUS), status

        charging = status in (
            _hidpp20.BatteryStatus.recharging,
            _hidpp20.BatteryStatus.slow_recharge,
        )
        old_charging, self[KEYS.BATTERY_CHARGING] = (
            self.get(KEYS.BATTERY_CHARGING),
            charging,
        )

        changed = old_level != level or old_status != status or old_charging != charging
        alert, reason = ALERT.NONE, None

        if status.ok and level > _BATTERY_ATTENTION_LEVEL:
            self[KEYS.ERROR] = None
        else:
            _log.warning("%s: battery %d%%, ALERT %s", self._device, level, status)
            if self.get(KEYS.ERROR) != status:
                self[KEYS.ERROR] = status
                # only show the notification once
                alert = ALERT.NOTIFICATION | ALERT.ATTENTION
            if hasattr(level, "name"):
                reason = _("Battery: %(level)s (%(status)s)") % {
                    "level": _(level),
                    "status": _(status.name),
                }
            else:
                reason = _("Battery: %(percent)d%% (%(status)s)") % {
                    "percent": level,
                    "status": status.name,
                }

        if changed or reason:
            # update the leds on the device, if any
            _hidpp10.set_3leds(
                self._device, level, charging=charging, warning=bool(alert)
            )
            self.changed(active=True, alert=alert, reason=reason, timestamp=timestamp)

    def read_battery(self, timestamp=None):
        if self._active:
            d = self._device
            assert d

            if d.protocol < 2.0:
                battery = _hidpp10.get_battery(d)
            else:
                battery = _hidpp20.get_battery(d)

            # Really unnecessary, if the device has SOLAR_DASHBOARD it should be
            # broadcasting it's battery status anyway, it will just take a little while.
            # However, when the device has just been detected, it will not show
            # any battery status for a while (broadcasts happen every 90 seconds).
            if battery is None and _hidpp20.Feature.SOLAR_DASHBOARD in d.features:
                d.feature_request(_hidpp20.Feature.SOLAR_DASHBOARD, 0x00, 1, 1)
                return

            if battery is not None:
                level, status = battery
                self.set_battery_info(level, status)
            elif KEYS.BATTERY_STATUS in self:
                self[KEYS.BATTERY_STATUS] = None
                self[KEYS.BATTERY_CHARGING] = None
                self.changed()

    def changed(self, active=None, alert=ALERT.NONE, reason=None, timestamp=None):
        assert self._changed_callback
        d = self._device
        # assert d  # may be invalid when processing the 'unpaired' notification
        timestamp = timestamp or _timestamp()

        if active is not None:
            d.online = active
            was_active, self._active = self._active, active
            if active:
                if not was_active:
                    # Make sure to set notification flags on the device, they
                    # get cleared when the device is turned off (but not when the device
                    # goes idle, and we can't tell the difference right now).
                    if d.protocol < 2.0:
                        self[KEYS.NOTIFICATION_FLAGS] = d.enable_notifications()

                    # If we've been inactive for a long time, forget anything
                    # about the battery.
                    if self.updated > 0 and timestamp - self.updated > _LONG_SLEEP:
                        self[KEYS.BATTERY_LEVEL] = None
                        self[KEYS.BATTERY_STATUS] = None
                        self[KEYS.BATTERY_CHARGING] = None

                    # Devices lose configuration when they are turned off,
                    # make sure they're up-to-date.
                    # _log.debug("%s settings %s", d, d.settings)
                    for s in d.settings:
                        s.apply()

                    if self.get(KEYS.BATTERY_LEVEL) is None:
                        self.read_battery(timestamp)
            else:
                if was_active:
                    battery = self.get(KEYS.BATTERY_LEVEL)
                    self.clear()
                    # If we had a known battery level before, assume it's not going
                    # to change much while the device is offline.
                    if battery is not None:
                        self[KEYS.BATTERY_LEVEL] = battery

        if self.updated == 0 and active == True:
            # if the device is active on the very first status notification,
            # (meaning just when the program started or a new receiver was just
            # detected), pop-up a notification about it
            alert |= ALERT.NOTIFICATION
        self.updated = timestamp

        # _log.debug("device %d changed: active=%s %s", d.number, self._active, dict(self))
        self._changed_callback(d, alert, reason)
