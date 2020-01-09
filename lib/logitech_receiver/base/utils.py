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
from struct import pack
from typing import Optional

import hidapi
from logitech_receiver import strhex
from logitech_receiver.base_usb import RECEIVER_USB_IDS
from .enums import ReportType
from .exceptions import NoReceiver
from .schemes import RawPacket
from .static import (
    DEFAULT_TIMEOUT,
    LONG_MESSAGE_SIZE,
    MAX_READ_SIZE,
    MEDIUM_MESSAGE_SIZE,
    SHORT_MESSAGE_SIZE,
)

_log = getLogger(__name__)
del getLogger


def receivers():
    """List all the Linux devices exposed by the UR attached to the machine."""
    for receiver_usb_id in RECEIVER_USB_IDS:
        for d in hidapi.enumerate(*receiver_usb_id):
            yield d


def notify_on_receivers_glib(callback):
    """Watch for matching devices and notifies the callback on the GLib thread."""
    hidapi.monitor_glib(callback, *RECEIVER_USB_IDS)


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
    return hidapi.open_path(path)


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
                hidapi.close(handle)
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

    if len(data) > SHORT_MESSAGE_SIZE - 2 or data[:1] == b"\x82":
        wdata = pack("!BB18s", 0x11, devnumber, data)
    else:
        wdata = pack("!BB5s", 0x10, devnumber, data)
    if _log.isEnabledFor(_DEBUG):
        _log.debug(
            "(%s) <= w[%02X %02X %s %s]",
            handle,
            wdata[0],
            devnumber,
            strhex(wdata[2:4]),
            strhex(wdata[4:]),
        )

    try:
        hidapi.write(int(handle), wdata)
    except Exception as reason:
        _log.error("write failed, assuming handle %r no longer available", handle)
        close(handle)
        raise NoReceiver(reason=reason)


def read(handle, timeout=DEFAULT_TIMEOUT) -> Optional[RawPacket]:
    """Read an incoming packet from the receiver.

    :returns: a tuple of (report_id, devnumber, data), or `None`.

    :raises NoReceiver: if the receiver is no longer available, i.e. has
    been physically removed from the machine, or the kernel driver has been
    unloaded. The handle will be closed automatically.
    """
    try:
        # convert timeout to milliseconds, the hidapi expects it
        timeout = int(timeout * 1000)
        data = hidapi.read(int(handle), MAX_READ_SIZE, timeout)
    except Exception as reason:
        _log.error("read failed, assuming handle %r no longer available", handle)
        close(handle)
        raise NoReceiver(reason=reason)

    if data:
        assert isinstance(data, bytes), (repr(data), type(data))
        report_type = ReportType(data[0])

        assert (
            (report_type & 0xF0 == 0)
            or (
                report_type == ReportType.HIDPP_SHORT
                and len(data) == SHORT_MESSAGE_SIZE
            )
            or (report_type == ReportType.HIDPP_LONG and len(data) == LONG_MESSAGE_SIZE)
            or (
                report_type == ReportType.DJ_BUS_ENUM_SHORT
                and len(data) == MEDIUM_MESSAGE_SIZE
            )
        ), (
            "unexpected message size: report_id %02X message %s"
            % (report_type, strhex(data))
        )
        if report_type & 0xF0 == 0x00:
            # These all should be normal HID reports that shouldn't really be reported in debugging
            # 			if _log.isEnabledFor(_DEBUG):
            # 				_log.debug("(%s) => r[%02X %s] ignoring unknown report", handle, report_id, strhex(data[1:]))
            return
        devnumber = data[1]

        if _log.isEnabledFor(_DEBUG):
            _log.debug(
                "(%s) => r[%02X %02X %s %s]",
                handle,
                report_type,
                devnumber,
                strhex(data[2:4]),
                strhex(data[4:]),
            )

        return RawPacket(report_type, devnumber, data[2:])
