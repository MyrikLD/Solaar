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

from typing import NamedTuple

from logitech_receiver.common import strhex
from logitech_receiver.hidpp10.enums import SubId


class RawPacket(NamedTuple):
    report_id: int
    devnumber: int
    data: bytes


class HIDPP_Notification(NamedTuple):
    devnumber: int
    sub_id: SubId
    address: int
    data: bytes

    def __str__(self):
        return "Notification(%d,%02X,%02X,%s)" % (
            self.devnumber,
            self.sub_id,
            self.address,
            strhex(self.data),
        )
