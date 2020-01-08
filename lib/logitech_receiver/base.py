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

# Base low-level functions used by the API proper.
# Unlikely to be used directly unless you're expanding the API.

from logging import DEBUG as _DEBUG, getLogger
from random import getrandbits as _random_bits
from time import time as _timestamp
from typing import Callable, NamedTuple, Optional

import hidapi as _hid
from . import hidpp10, hidpp20
from .common import KwException as _KwException, pack as _pack, strhex as _strhex

_log = getLogger(__name__)
del getLogger
#
#
#

_SHORT_MESSAGE_SIZE = 7
_LONG_MESSAGE_SIZE = 20
_MEDIUM_MESSAGE_SIZE = 15
_MAX_READ_SIZE = 32

"""Default timeout on read (in seconds)."""
DEFAULT_TIMEOUT = 4
# the receiver itself should reply very fast, within 500ms
_RECEIVER_REQUEST_TIMEOUT = 0.9
# devices may reply a lot slower, as the call has to go wireless to them and come back
_DEVICE_REQUEST_TIMEOUT = DEFAULT_TIMEOUT
# when pinging, be extra patient
_PING_TIMEOUT = DEFAULT_TIMEOUT * 2


#
# Exceptions that may be raised by this API.
#


class NoReceiver(_KwException):
    """Raised when trying to talk through a previously open handle, when the
    receiver is no longer available. Should only happen if the receiver is
    physically disconnected from the machine, or its kernel driver module is
    unloaded."""

    pass


class NoSuchDevice(_KwException):
    """Raised when trying to reach a device number not paired to the receiver."""

    pass


class DeviceUnreachable(_KwException):
    """Raised when a request is made to an unreachable (turned off) device."""

    pass


#
#
#

from .base_usb import ALL as _RECEIVER_USB_IDS


def receivers():
    """List all the Linux devices exposed by the UR attached to the machine."""
    for receiver_usb_id in _RECEIVER_USB_IDS:
        for d in _hid.enumerate(*receiver_usb_id):
            yield d


def notify_on_receivers_glib(callback):
    """Watch for matching devices and notifies the callback on the GLib thread."""
    _hid.monitor_glib(callback, *_RECEIVER_USB_IDS)


#
#
#


def open_path(path):
    """Checks if the given Linux device path points to the right UR device.

    :param path: the Linux device path.

    The UR physical device may expose multiple linux devices with the same
    interface, so we have to check for the right one. At this moment the only
    way to distinguish betheen them is to do a test ping on an invalid
    (attached) device number (i.e., 0), expecting a 'ping failed' reply.

    :returns: an open receiver handle if this is the right Linux device, or
    ``None``.
    """
    return _hid.open_path(path)


def open():
    """Opens the first Logitech Unifying Receiver found attached to the machine.

    :returns: An open file handle for the found receiver, or ``None``.
    """
    for rawdevice in receivers():
        handle = open_path(rawdevice.path)
        if handle:
            return handle


def close(handle: int):
    """Closes a HID device handle."""
    if handle:
        try:
            if isinstance(handle, int):
                _hid.close(handle)
            else:
                handle.close()
            # _log.info("closed receiver handle %r", handle)
            return True
        except:
            # _log.exception("closing receiver handle %r", handle)
            pass

    return False


def write(handle: int, devnumber, data):
    """Writes some data to the receiver, addressed to a certain device.

    :param handle: an open UR handle.
    :param devnumber: attached device number.
    :param data: data to send, up to 5 bytes.

    The first two (required) bytes of data must be the SubId and address.

    :raises NoReceiver: if the receiver is no longer available, i.e. has
    been physically removed from the machine, or the kernel driver has been
    unloaded. The handle will be closed automatically.
    """
    # the data is padded to either 5 or 18 bytes
    assert data is not None
    assert isinstance(data, bytes), (repr(data), type(data))

    if len(data) > _SHORT_MESSAGE_SIZE - 2 or data[:1] == b"\x82":
        wdata = _pack("!BB18s", 0x11, devnumber, data)
    else:
        wdata = _pack("!BB5s", 0x10, devnumber, data)
    if _log.isEnabledFor(_DEBUG):
        _log.debug(
            "(%s) <= w[%02X %02X %s %s]",
            handle,
            wdata[0],
            devnumber,
            _strhex(wdata[2:4]),
            _strhex(wdata[4:]),
        )

    try:
        _hid.write(int(handle), wdata)
    except Exception as reason:
        _log.error("write failed, assuming handle %r no longer available", handle)
        close(handle)
        raise NoReceiver(reason=reason)


class RawPacket(NamedTuple):
    report_id: int
    devnumber: int
    data: bytes


def read(handle, timeout=DEFAULT_TIMEOUT):
    """Read some data from the receiver. Usually called after a write (feature
    call), to get the reply.

    :param: handle open handle to the receiver
    :param: timeout how long to wait for a reply, in seconds

    :returns: a tuple of (devnumber, message data), or `None`

    :raises NoReceiver: if the receiver is no longer available, i.e. has
    been physically removed from the machine, or the kernel driver has been
    unloaded. The handle will be closed automatically.
    """
    reply = _read(handle, timeout)
    if reply:
        return reply[1:]


def _read(handle, timeout) -> Optional[RawPacket]:
    """Read an incoming packet from the receiver.

    :returns: a tuple of (report_id, devnumber, data), or `None`.

    :raises NoReceiver: if the receiver is no longer available, i.e. has
    been physically removed from the machine, or the kernel driver has been
    unloaded. The handle will be closed automatically.
    """
    try:
        # convert timeout to milliseconds, the hidapi expects it
        timeout = int(timeout * 1000)
        data = _hid.read(int(handle), _MAX_READ_SIZE, timeout)
    except Exception as reason:
        _log.error("read failed, assuming handle %r no longer available", handle)
        close(handle)
        raise NoReceiver(reason=reason)

    if data:
        assert isinstance(data, bytes), (repr(data), type(data))
        report_id = data[0]
        assert (
            (report_id & 0xF0 == 0)
            or (report_id == 0x10 and len(data) == _SHORT_MESSAGE_SIZE)
            or (report_id == 0x11 and len(data) == _LONG_MESSAGE_SIZE)
            or (report_id == 0x20 and len(data) == _MEDIUM_MESSAGE_SIZE)
        ), (
            "unexpected message size: report_id %02X message %s"
            % (report_id, _strhex(data))
        )
        if report_id & 0xF0 == 0x00:
            # These all should be normal HID reports that shouldn't really be reported in debugging
            # 			if _log.isEnabledFor(_DEBUG):
            # 				_log.debug("(%s) => r[%02X %s] ignoring unknown report", handle, report_id, strhex(data[1:]))
            return
        devnumber = data[1]

        if _log.isEnabledFor(_DEBUG):
            _log.debug(
                "(%s) => r[%02X %02X %s %s]",
                handle,
                report_id,
                devnumber,
                _strhex(data[2:4]),
                _strhex(data[4:]),
            )

        return RawPacket(report_id, devnumber, data[2:])


#
#
#


def _skip_incoming(handle: int, notifications_hook: Optional[Callable]):
    """Read anything already in the input buffer.

    Used by request() and ping() before their write.
    """

    while True:
        try:
            # read whatever is already in the buffer, if any
            data = _hid.read(int(handle), _MAX_READ_SIZE, 0)
        except Exception as reason:
            _log.error("read failed, assuming receiver %s no longer available", handle)
            close(handle)
            raise NoReceiver(reason=reason)

        if data:
            assert isinstance(data, bytes), (repr(data), type(data))
            report_id = data[0]
            if _log.isEnabledFor(_DEBUG):
                assert (
                    (report_id & 0xF0 == 0)
                    or (report_id == 0x10 and len(data) == _SHORT_MESSAGE_SIZE)
                    or (report_id == 0x11 and len(data) == _LONG_MESSAGE_SIZE)
                    or (report_id == 0x20 and len(data) == _MEDIUM_MESSAGE_SIZE)
                ), (
                    "unexpected message size: report_id %02X message %s"
                    % (report_id, _strhex(data))
                )
            if notifications_hook and report_id & 0xF0:
                n = make_notification(data[1], data[2:])
                if n:
                    notifications_hook(n)
        else:
            # nothing in the input buffer, we're done
            return


def make_notification(devnumber, data):
    """Guess if this is a notification (and not just a request reply), and
    return a Notification tuple if it is."""
    sub_id = data[0]
    if sub_id & 0x80 == 0x80:
        # this is either a HID++1.0 register r/w, or an error reply
        return

    address = data[1]
    if (
        # standard HID++ 1.0 notification, SubId may be 0x40 - 0x7F
        (sub_id >= 0x40)
        or
        # custom HID++1.0 battery events, where SubId is 0x07/0x0D
        (sub_id in (0x07, 0x0D) and len(data) == 5 and data[4:5] == b"\x00")
        or
        # custom HID++1.0 illumination event, where SubId is 0x17
        (sub_id == 0x17 and len(data) == 5)
        or
        # HID++ 2.0 feature notifications have the SoftwareID 0
        (address & 0x0F == 0x00)
    ):
        return _HIDPP_Notification(devnumber, sub_id, address, data[2:])


class _HIDPP_Notification(NamedTuple):
    devnumber: int
    sub_id: int
    address: int
    data: bytes

    def __str__(self):
        return "Notification(%d,%02X,%02X,%s)" % (
            self.devnumber,
            self.sub_id,
            self.address,
            _strhex(self.data),
        )


class ReadException(Exception):
    def __init__(self, protocol: float, code: int):
        self.protocol_version = protocol
        self.code = code
        super().__init__()

    def error(self):
        return {1.0: hidpp10, 2.0: hidpp20}[self.protocol_version].Error[self.code]

    def __str__(self):
        return f"HIDPP{self.protocol_version}0: {self.error()}"


#
#
#


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
        self.id_bytes = _pack("!H", request_id)

        timeout = (
            _RECEIVER_REQUEST_TIMEOUT if devnumber == 0xFF else _DEVICE_REQUEST_TIMEOUT
        )
        # be extra patient on long register read
        if request_id & 0xFF00 == 0x8300:
            timeout *= 2
        self.timeout = timeout

        if params:
            self.params = b"".join(
                _pack("B", p) if isinstance(p, int) else p for p in params
            )

    @property
    def request_data(self) -> bytes:
        return self.id_bytes + self.params

    def write(self, handle: int):
        self.notifications_hook = getattr(handle, "notifications_hook", None)
        _skip_incoming(handle, self.notifications_hook)
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
        reply = _read(handle, r.timeout - delta)

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
    # if _log.isEnabledFor(_DEBUG):
    # 	_log.debug("(%s) still waiting for reply, delta %f", handle, delta)

    _log.warning(
        "timeout (%0.2f/%0.2f) on device %d request {%04X} params [%s]",
        delta,
        r.timeout,
        devnumber,
        request_id,
        _strhex(r.params),
    )


def ping(handle, devnumber):
    """Check if a device is connected to the receiver.

    :returns: The HID protocol supported by the device, as a floating point number, if the device is active.
    """
    if _log.isEnabledFor(_DEBUG):
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

    while delta < _PING_TIMEOUT:
        reply = _read(handle, _PING_TIMEOUT - delta)

        if reply:
            if reply.devnumber == devnumber:
                if reply.data[:2] == r.id_bytes and reply.data[4] == r.request_data[-1]:
                    # HID++ 2.0+ device, currently connected
                    return reply.data[2] + reply.data[3] / 10.0

                if (
                    reply.report_id == 0x10
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
        _PING_TIMEOUT,
        devnumber,
    )
