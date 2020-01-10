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

from logitech_receiver import hidpp10, hidpp20
from logitech_receiver.common import KwException


class NoReceiver(KwException):
    """Raised when trying to talk through a previously open handle, when the
    receiver is no longer available. Should only happen if the receiver is
    physically disconnected from the machine, or its kernel driver module is
    unloaded."""

    pass


class NoSuchDevice(KwException):
    """Raised when trying to reach a device number not paired to the receiver."""

    pass


class DeviceUnreachable(KwException):
    """Raised when a request is made to an unreachable (turned off) device."""

    pass


class ReadException(Exception):
    def __init__(self, protocol: float, code: int):
        self.protocol_version = protocol
        self.code = code
        super().__init__()

    @property
    def protocol(self):
        return {1.0: hidpp10, 2.0: hidpp20}[self.protocol_version]

    @property
    def error(self):
        return self.protocol.Error(self.code)

    def __str__(self):
        return f"HID++ {self.protocol_version}: {self.error}"

    def __repr__(self):
        return f'ReadException[{self}]'
