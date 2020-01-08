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

# Logitech Unifying Receiver API.


from logging import getLogger

from logitech_receiver.common import NamedInts

_log = getLogger(__name__)
del getLogger
#
#
#

# <FeaturesSupported.xml sed '/LD_FID_/{s/.*LD_FID_/\t/;s/"[ \t]*Id="/=/;s/" \/>/,/p}' | sort -t= -k2
"""Possible features available on a Logitech device.

A particular device might not support all these features, and may support other
unknown features as well.

Additional features names taken from:
https://github.com/cvuchener/hidpp
https://github.com/Logitech/cpg-docs/tree/master/hidpp20
"""


class FEATURE(NamedInts):
    ROOT = 0x0000
    FEATURE_SET = 0x0001
    FEATURE_INFO = 0x0002
    # Common
    DEVICE_FW_VERSION = 0x0003
    DEVICE_UNIT_ID = 0x0004
    DEVICE_NAME = 0x0005
    DEVICE_GROUPS = 0x0006
    DEVICE_FRIENDLY_NAME = 0x0007
    KEEP_ALIVE = 0x0008
    RESET = 0x0020  # "Config Change"
    CRYPTO_ID = 0x0021
    TARGET_SOFTWARE = 0x0030
    WIRELESS_SIGNAL_STRENGTH = 0x0080
    DFUCONTROL_LEGACY = 0x00C0
    DFUCONTROL_UNSIGNED = 0x00C1
    DFUCONTROL_SIGNED = 0x00C2
    DFU = 0x00D0
    BATTERY_STATUS = 0x1000
    BATTERY_VOLTAGE = 0x1001
    CHARGING_CONTROL = 0x1010
    LED_CONTROL = 0x1300
    GENERIC_TEST = 0x1800
    DEVICE_RESET = 0x1802
    OOBSTATE = 0x1805
    CONFIG_DEVICE_PROPS = 0x1806
    CHANGE_HOST = 0x1814
    HOSTS_INFO = 0x1815
    BACKLIGHT = 0x1981
    BACKLIGHT2 = 0x1982
    BACKLIGHT3 = 0x1983
    PRESENTER_CONTROL = 0x1A00
    SENSOR_3D = 0x1A01
    REPROG_CONTROLS = 0x1B00
    REPROG_CONTROLS_V2 = 0x1B01
    REPROG_CONTROLS_V2_2 = 0x1B02  # LogiOptions 2.10.73 features.xml
    REPROG_CONTROLS_V3 = 0x1B03
    REPROG_CONTROLS_V4 = 0x1B04
    REPORT_HID_USAGE = 0x1BC0
    PERSISTENT_REMAPPABLE_ACTION = 0x1C00
    WIRELESS_DEVICE_STATUS = 0x1D4B
    REMAINING_PAIRING = 0x1DF0
    ENABLE_HIDDEN_FEATURES = 0x1E00
    FIRMWARE_PROPERTIES = 0x1F1F
    ADC_MEASUREMENT = 0x1F20
    # Mouse
    LEFT_RIGHT_SWAP = 0x2001
    SWAP_BUTTON_CANCEL = 0x2005
    POINTER_AXIS_ORIENTATION = 0x2006
    VERTICAL_SCROLLING = 0x2100
    SMART_SHIFT = 0x2110
    HI_RES_SCROLLING = 0x2120
    HIRES_WHEEL = 0x2121
    LOWRES_WHEEL = 0x2130
    THUMB_WHEEL = 0x2150
    MOUSE_POINTER = 0x2200
    ADJUSTABLE_DPI = 0x2201
    POINTER_SPEED = 0x2205
    ANGLE_SNAPPING = 0x2230
    SURFACE_TUNING = 0x2240
    HYBRID_TRACKING = 0x2400
    # Keyboard
    FN_INVERSION = 0x40A0
    NEW_FN_INVERSION = 0x40A2
    K375S_FN_INVERSION = 0x40A3
    ENCRYPTION = 0x4100
    LOCK_KEY_STATE = 0x4220
    SOLAR_DASHBOARD = 0x4301
    KEYBOARD_LAYOUT = 0x4520
    KEYBOARD_DISABLE = 0x4521
    KEYBOARD_DISABLE_BY_USAGE = 0x4522
    DUALPLATFORM = 0x4530
    MULTIPLATFORM = 0x4531
    KEYBOARD_LAYOUT_2 = 0x4540
    CROWN = 0x4600
    # Touchpad
    TOUCHPAD_FW_ITEMS = 0x6010
    TOUCHPAD_SW_ITEMS = 0x6011
    TOUCHPAD_WIN8_FW_ITEMS = 0x6012
    TAP_ENABLE = 0x6020
    TAP_ENABLE_EXTENDED = 0x6021
    CURSOR_BALLISTIC = 0x6030
    TOUCHPAD_RESOLUTION = 0x6040
    TOUCHPAD_RAW_XY = 0x6100
    TOUCHMOUSE_RAW_POINTS = 0x6110
    TOUCHMOUSE_6120 = 0x6120
    GESTURE = 0x6500
    GESTURE_2 = 0x6501
    # Gaming Devices
    GKEY = 0x8010
    MKEYS = 0x8020
    MR = 0x8030
    BRIGHTNESS_CONTROL = 0x8040
    REPORT_RATE = 0x8060
    COLOR_LED_EFFECTS = 0x8070
    RGB_EFFECTS = 0x8071
    PER_KEY_LIGHTING = 0x8080
    PER_KEY_LIGHTING_V2 = 0x8081
    MODE_STATUS = 0x8090
    ONBOARD_PROFILES = 0x8100
    MOUSE_BUTTON_SPY = 0x8110
    LATENCY_MONITORING = 0x8111
    GAMING_ATTACHMENTS = 0x8120
    FORCE_FEEDBACK = 0x8123
    SIDETONE = 0x8300
    EQUALIZER = 0x8310
    HEADSET_OUT = 0x8320


class FEATURE_FLAG(NamedInts):
    internal = 0x20
    hidden = 0x40
    obsolete = 0x80


class DEVICE_KIND(NamedInts):
    keyboard = 0x00
    remote_control = 0x01
    numpad = 0x02
    mouse = 0x03
    touchpad = 0x04
    trackball = 0x05
    presenter = 0x06
    receiver = 0x07


class FIRMWARE_KIND(NamedInts):
    Firmware = 0x00
    Bootloader = 0x01
    Hardware = 0x02
    Other = 0x03


class BATTERY_STATUS(NamedInts):
    discharging = 0x00
    recharging = 0x01
    almost_full = 0x02
    full = 0x03
    slow_recharge = 0x04
    invalid_battery = 0x05
    thermal_error = 0x06

    @property
    def ok(self) -> bool:
        return self not in (
            BATTERY_STATUS.invalid_battery,
            BATTERY_STATUS.thermal_error,
        )


class ERROR(NamedInts):
    unknown = 0x01
    invalid_argument = 0x02
    out_of_range = 0x03
    hardware_error = 0x04
    logitech_internal = 0x05
    invalid_feature_index = 0x06
    invalid_function = 0x07
    busy = 0x08
    unsupported = 0x09
