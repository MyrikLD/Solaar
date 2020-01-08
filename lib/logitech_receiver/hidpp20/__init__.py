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

from .enums import (
    ERROR,
    BATTERY_STATUS,
    DEVICE_KIND,
    FEATURE,
    FEATURE_FLAG,
    FIRMWARE_KIND,
)
from .exceptions import FeatureCallError, FeatureNotSupported
from .arrays import FeaturesArray, KeysArray
from .utils import (
    feature_request,
    get_firmware,
    get_kind,
    get_name,
    get_battery,
    get_keys,
    get_mouse_pointer_info,
    get_vertical_scrolling_info,
    get_hi_res_scrolling_info,
    get_pointer_speed_info,
    get_lowres_wheel_status,
    get_hires_wheel,
)
