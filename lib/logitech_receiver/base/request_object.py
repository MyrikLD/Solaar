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

from random import getrandbits as _random_bits
from struct import pack
from time import time as _timestamp
from typing import Callable, Optional

from .exceptions import ReadException
from .schemes import RawPacket
from .skip_incoming import skip_incoming
from .static import DEVICE_REQUEST_TIMEOUT, RECEIVER_REQUEST_TIMEOUT
from .utils import write


class Request:
    id: int
    id_bytes: bytes

    devnumber: int

    timeout: int
    params: bytes = b""
    notifications_hook: Optional[Callable] = None

    started = 0

    class NotMine(Exception):
        pass

    def __init__(self, devnumber: int, request_id: int, params):
        self.devnumber = devnumber

        if devnumber != 0xFF and request_id < 0x8000:
            # For HID++ 2.0 feature requests, randomize the SoftwareId to make it
            # easier to recognize the reply for this request. also, always set the
            # most significant bit (8) in SoftwareId, to make notifications easier
            # to distinguish from request replies.
            # This only applies to peripheral requests, ofc.
            request_id = (request_id & 0xFFF0) | 0x08 | _random_bits(3)

        self.id = request_id
        self.id_bytes = pack("!H", request_id)

        timeout = (
            RECEIVER_REQUEST_TIMEOUT if devnumber == 0xFF else DEVICE_REQUEST_TIMEOUT
        )
        # be extra patient on long register read
        if request_id & 0xFF00 == 0x8300:
            timeout *= 2
        self.timeout = timeout

        if params:
            self.params = b"".join(
                pack("B", p) if isinstance(p, int) else p for p in params
            )

    @property
    def request_data(self) -> bytes:
        return self.id_bytes + self.params

    def write(self, handle: int):
        self.notifications_hook = getattr(handle, "notifications_hook", None)
        skip_incoming(handle, self.notifications_hook)
        write(int(handle), self.devnumber, self.request_data)

        self.started = _timestamp()

    def handle_reply(self, reply: RawPacket):
        exception = self.v1_exception(reply)
        if exception:
            raise ReadException(protocol=1.0, code=exception)

        exception = self.v2_exception(reply)
        if exception:
            raise ReadException(protocol=2.0, code=exception)

        return self.get_data(reply)

    def v2_exception(self, reply: RawPacket) -> int:
        if reply.data[0] == 0xFF and reply.data[1:3] == self.id_bytes:
            error = reply.data[3]
            return error

    def v1_exception(self, reply: RawPacket) -> int:
        if (
                reply.report_id == 0x10
                and reply.data[0] == 0x8F
                and reply.data[1:3] == self.id_bytes
        ):
            error = reply.data[3]
            return error

    def get_data(self, reply: RawPacket) -> bytes:
        if reply.data[:2] == self.id_bytes:
            if self.id & 0xFE00 == 0x8200:
                # long registry r/w should return a long reply
                assert reply.report_id == 0x11
            elif self.id & 0xFE00 == 0x8000:
                # short registry r/w should return a short reply
                assert reply.report_id == 0x10

            if self.devnumber == 0xFF and (self.id in (0x83B5, 0x81F1)):
                # these replies have to match the first parameter as well
                if reply.data[2] == self.params[0]:
                    return reply.data[2:]
                else:
                    # hm, not matching my request, and certainly not a notification
                    raise self.NotMine()

            return reply.data[2:]
