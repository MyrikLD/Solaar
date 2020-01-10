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

from logging import DEBUG as _DEBUG, getLogger
from random import getrandbits as _random_bits
from time import time as _timestamp

from logitech_receiver import hidpp10, strhex
from .enums import ReportType
from .exceptions import NoSuchDevice
from .make_notification import make_notification
from .request_object import Request
from .static import PING_TIMEOUT
from .utils import read

_log = getLogger(__name__)
del getLogger


def request(handle, devnumber, request_id, *params):
    """Makes a feature call to a device and waits for a matching reply.

    This function will wait for a matching reply indefinitely.

    :param handle: an open UR handle.
    :param devnumber: attached device number.
    :param request_id: a 16-bit integer.
    :param params: parameters for the feature call, 3 to 16 bytes.
    :returns: the reply data, or ``None`` if some error occurred.
    """

    # import inspect as _inspect
    # print ('\n  '.join(str(s) for s in _inspect.stack()))

    r = Request(devnumber, request_id, params)
    r.write(handle)

    # we consider timeout from this point
    delta = 0

    while delta < r.timeout:
        reply = read(handle, r.timeout - delta)

        if reply:
            if reply.devnumber == devnumber and reply.data:
                try:
                    data = r.handle_reply(reply)
                    if data:
                        return data
                except Request.NotMine:
                    continue
            else:
                # a reply was received, but did not match our request in any way
                # reset the timeout starting point
                r.started = _timestamp()

            if r.notifications_hook:
                n = make_notification(reply.devnumber, reply.data)
                if n:
                    r.notifications_hook(n)

        delta = _timestamp() - r.started
    # _log.debug("(%s) still waiting for reply, delta %f", handle, delta)

    _log.warning(
        "timeout (%0.2f/%0.2f) on device %d request {%04X} params [%s]",
        delta,
        r.timeout,
        devnumber,
        request_id,
        strhex(r.params),
    )


def ping(handle, devnumber):
    """Check if a device is connected to the receiver.

    :returns: The HID protocol supported by the device, as a floating point number, if the device is active.
    """
    _log.debug("(%s) pinging device %d", handle, devnumber)

    # import inspect as _inspect
    # print ('\n  '.join(str(s) for s in _inspect.stack()))

    assert devnumber != 0xFF
    assert 0x00 < devnumber < 0x0F

    # randomize the SoftwareId and mark byte to be able to identify the ping
    # reply, and set most significant (0x8) bit in SoftwareId so that the reply
    # is always distinguishable from notifications
    r = Request(devnumber, 0x0010, (0, 0, _random_bits(8)))
    r.write(handle)

    # we consider timeout from this point
    delta = 0

    while delta < PING_TIMEOUT:
        reply = read(handle, PING_TIMEOUT - delta)

        if reply:
            if reply.devnumber == devnumber:
                if reply.data[:2] == r.id_bytes and reply.data[4] == r.request_data[-1]:
                    # HID++ 2.0+ device, currently connected
                    return reply.data[2] + reply.data[3] / 10.0

                if (
                    reply.report_type == ReportType.HIDPP_SHORT
                    and reply.data[0] == 0x8F
                    and reply.data[1:3] == r.id_bytes
                ):
                    assert reply.data[-1] == 0x00
                    error = reply.data[3]

                    if error == hidpp10.Error.invalid_SubID__command:
                        # a valid reply from a HID++ 1.0 device
                        return 1.0

                    if error == hidpp10.Error.resource_error:
                        # device unreachable
                        return

                    if error == hidpp10.Error.unknown_device:
                        # no paired device with that number
                        _log.error(
                            "(%s) device %d error on ping request: unknown device",
                            handle,
                            devnumber,
                        )
                        raise NoSuchDevice(number=devnumber, request=r.id)

            if r.notifications_hook:
                n = make_notification(reply.devnumber, reply.data)
                if n:
                    r.notifications_hook(n)

        delta = _timestamp() - r.started

    _log.warning(
        "(%s) timeout (%0.2f/%0.2f) on device %d ping",
        handle,
        delta,
        PING_TIMEOUT,
        devnumber,
    )
