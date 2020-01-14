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
from typing import Callable, Optional

import hidapi
from logitech_receiver import strhex
from .enums import ReportType
from .exceptions import NoReceiver
from .make_notification import make_notification
from .static import (
    LONG_MESSAGE_SIZE,
    MAX_READ_SIZE,
    MEDIUM_MESSAGE_SIZE,
    SHORT_MESSAGE_SIZE,
)
from .utils import close

_log = getLogger(__name__)


def skip_incoming(handle: int, notifications_hook: Optional[Callable]):
    """Read anything already in the input buffer.

    Used by request() and ping() before their write.
    """

    while True:
        try:
            # read whatever is already in the buffer, if any
            data = hidapi.read(int(handle), MAX_READ_SIZE, 0)
        except Exception as reason:
            _log.error("read failed, assuming receiver %s no longer available", handle)
            close(handle)
            raise NoReceiver(reason=reason)

        if data:
            assert isinstance(data, bytes), (repr(data), type(data))
            report_type = ReportType(data[0])

            if _log.isEnabledFor(_DEBUG):
                assert (
                    (report_type & 0xF0 == 0)
                    or (
                        report_type == ReportType.HIDPP_SHORT
                        and len(data) == SHORT_MESSAGE_SIZE
                    )
                    or (
                        report_type == ReportType.HIDPP_LONG
                        and len(data) == LONG_MESSAGE_SIZE
                    )
                    or (
                        report_type == ReportType.DJ_BUS_ENUM_SHORT
                        and len(data) == MEDIUM_MESSAGE_SIZE
                    )
                ), f"unexpected message size: report_type {report_type} message {strhex(data)}"
            if notifications_hook and report_type & 0xF0:
                n = make_notification(data[1], data[2:])
                if n:
                    notifications_hook(n)
        else:
            # nothing in the input buffer, we're done
            return
