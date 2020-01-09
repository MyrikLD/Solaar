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

from typing import List

from logitech_receiver import (
    Receiver,
    hidpp10 as _hidpp10,
    hidpp20 as _hidpp20,
    special_keys as _special_keys,
    PairedDevice,
)
from logitech_receiver.hidpp20 import BatteryStatus
from solaar.cli import find_device, find_receiver
from solaar.cli.indent_helper import Text


def _print_receiver(receiver: Receiver, text: Text):
    paired_count = receiver.count()

    text(f"Device path : {receiver.path}")
    text(f"USB id      : 046d:{receiver.product_id}")
    text(f"Serial      : {receiver.serial}")

    with text:
        for f in receiver.firmware:
            text(f"{f.kind:<11}: {f.version}")

    text(
        f"Has {paired_count} paired device(s) out of a maximum of {receiver.max_devices}."
    )

    notification_flags = _hidpp10.get_notification_flags(receiver)
    if notification_flags is not None:
        if notification_flags:
            notification_names = ", ".join(
                _hidpp10.NotificateionFlag.flag_names(notification_flags)
            )
            text(f"Notifications: {notification_names} (0x{notification_flags:06x})")
        else:
            text("Notifications: (none)")

    # This register reports the current value of up to 16 device activity counters. The receiver increments each
    # counter when the corresponding device sends any non-empty report. When the software needs activity
    # information, it polls this register at regular intervals and subtracts the previous counter values from the
    # current ones to get the number of non-empty reports received during the interval.
    # activity = receiver.read_register(hidpp10.Registers.devices_activity)
    # if activity:
    #     activity = activity[:receiver.max_devices]
    #     activity_text = (
    #         ", ".join(
    #             f"{d+1}={a}%" for d, a in enumerate(activity) if a > 0
    #         )
    #         or "(empty)"
    #     )
    #     text(f"Device activity counters: {activity_text}")


class PrintDevice:
    def __init__(self, dev: PairedDevice, text: Text):
        self.dev = dev
        self.text = text

        text(f"Codename      : {dev.codename}")
        text(f"Kind          : {dev.kind}")
        text(f"Wireless PID  : {dev.wpid}")
        if dev.protocol:
            text("Protocol      : HID++ %1.1f" % dev.protocol)
        else:
            text("Protocol      : unknown (device is offline)")

        if dev.polling_rate:
            text(
                f"Polling rate  : {dev.polling_rate}ms ({1000 // dev.polling_rate}Hz)",
            )

        text(f"Serial number : {dev.serial}")
        with text:
            for fw in dev.firmware:
                text(f"{fw.kind:10}: {fw.name} {fw.version}")

        if dev.power_switch_location:
            text(f"The power switch is located on the {dev.power_switch_location}.")

        if dev.online:
            self.print_notifications()
            if dev.features:
                self.print_features()
            if dev.keys:
                self.print_keys()

        if dev.online:
            self.print_battery()
        else:
            text("Battery: unknown (device is offline).")

    def print_notifications(self):
        notification_flags = _hidpp10.get_notification_flags(self.dev)
        if notification_flags is not None:
            if notification_flags:
                notification_names = _hidpp10.NotificateionFlag.flag_names(
                    notification_flags
                )
                self.text(
                    "Notifications: %s (0x%06X)."
                    % (", ".join(notification_names), notification_flags)
                )
            else:
                self.text("Notifications: (none).")

    def print_features(self):
        self.text(f"Supports {len(self.dev.features)} HID++ 2.0 features:")
        with self.text:
            PrintFeatures(self.dev, self.text)

    def print_keys(self):
        dev = self.dev
        text = self.text

        text(f"Has {len(dev.keys)} reprogrammable keys:")
        with text:
            for k in dev.keys:
                flags = _special_keys.KEY_FLAG.flag_names(k.flags)
                # TODO: add here additional variants for other REPROG_CONTROLS
                if dev.keys.keyversion == 1:
                    flags_text = ", ".join(flags)
                    text(f"{k.index:>2d}: {k.key:<26} => {k.task:<27}  {flags_text}")
                if dev.keys.keyversion == 4:
                    text(
                        f"{k.index:>2d}: {k.key:<26}, default: {k.task:<27} => {k.remapped:<26}"
                    )
                    with text:
                        flags_text = ", ".join(flags)
                        k_text = f"pos:{k.pos:>3}, group:{k.group:>3}, gmask:{k.group_mask:>3}"
                        text(f"{k_text}")
                        text(f"{flags_text}")

    def print_battery(self):
        battery = _hidpp20.get_battery(self.dev)
        if battery is None:
            battery = _hidpp10.get_battery(self.dev)

        if battery is not None:
            level, status = battery
            if level is not None:
                if isinstance(level, BatteryStatus):
                    level_text = level.name
                else:
                    level_text = "%d%%" % level
            else:
                level_text = "N/A"
            self.text(f"Battery: {level_text}, {status}.")
        else:
            self.text("Battery status unavailable.")


class PrintFeatures:
    def __init__(self, dev, text: Text):
        self.dev = dev
        self.text = text

        for index, feature in enumerate(dev.features):
            self.print_feature(index, feature)

    def print_feature(self, index, feature):
        flags = self.dev.request(0x0000, feature.to_bytes(2, byteorder="big"))
        flags = 0 if flags is None else flags[1]
        flags = _hidpp20.FeatureFlag.flag_names(flags)
        flags_text = ", ".join(flags)
        self.text(f"{index:>2d}: {feature:<23} {{{feature.value:04X}}}  {flags_text}")

        fun = getattr(self, feature.name, None)
        if fun:
            with self.text:
                fun()

    def HIRES_WHEEL(self):
        wheel = _hidpp20.get_hires_wheel(self.dev)
        if wheel:
            (multi, has_invert, has_switch, inv, res, target, ratchet) = wheel
            self.text(f"Multiplier: {multi}")
            if has_invert:
                self.text("Has invert")
                if inv:
                    self.text("Inverse wheel motion")
                else:
                    self.text("Normal wheel motion")
            if has_switch:
                self.text("Has ratchet switch")
                if ratchet:
                    self.text("Normal wheel mode")
                else:
                    self.text("Free wheel mode")
            if res:
                self.text("High resolution mode")
            else:
                self.text("Low resolution mode")
            if target:
                self.text("HID++ notification")
            else:
                self.text("HID notification")

    def MOUSE_POINTER(self):
        mouse_pointer = _hidpp20.get_mouse_pointer_info(self.dev)
        if mouse_pointer:
            self.text("DPI: %s" % mouse_pointer["dpi"])
            self.text("Acceleration: %s" % mouse_pointer["acceleration"])
            if mouse_pointer["suggest_os_ballistics"]:
                self.text("Use OS ballistics")
            else:
                self.text("Override OS ballistics")
            if mouse_pointer["suggest_vertical_orientation"]:
                self.text("Provide vertical tuning, trackball")
            else:
                self.text("No vertical tuning, standard mice")

    def VERTICAL_SCROLLING(self):
        vertical_scrolling_info = _hidpp20.get_vertical_scrolling_info(self.dev)
        if vertical_scrolling_info:
            self.text("Roller type: %s" % vertical_scrolling_info["roller"])
            self.text("Ratchet per turn: %s" % vertical_scrolling_info["ratchet"])
            self.text("Scroll lines: %s" % vertical_scrolling_info["lines"])

    def HI_RES_SCROLLING(self):
        (scrolling_mode, scrolling_resolution,) = _hidpp20.get_hi_res_scrolling_info(
            self.dev
        )
        if scrolling_mode:
            self.text("Hi-res scrolling enabled")
        else:
            self.text("Hi-res scrolling disabled")
        if scrolling_resolution:
            self.text(f"Hi-res scrolling multiplier: {scrolling_resolution}")

    def POINTER_SPEED(self):
        pointer_speed = _hidpp20.get_pointer_speed_info(self.dev)
        if pointer_speed:
            self.text(f"Pointer Speed: {pointer_speed}")

    def LOWRES_WHEEL(self):
        wheel_status = _hidpp20.get_lowres_wheel_status(self.dev)
        if wheel_status:
            self.text(f"Wheel Reports: {wheel_status}")


def run(receivers: List[Receiver], args):
    assert receivers
    assert args.device

    device_name = args.device.lower()
    text = Text()

    if device_name == "all":
        for r in receivers:
            text("Unifying Receiver")
            with text:
                _print_receiver(r, text)
                count = r.count()
                if count:
                    for dev in r:
                        dev.ping()
                        text()
                        text(f"{dev.number}: {dev.codename}")
                        with text:
                            PrintDevice(dev, text)
                        count -= 1
                        if not count:
                            break
            text()
        return

    dev = find_receiver(receivers, device_name)
    if dev:
        _print_receiver(dev, text)
        return

    dev = find_device(receivers, device_name)
    assert dev
    PrintDevice(dev, text)
