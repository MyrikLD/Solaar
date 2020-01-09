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

# Translation support for the Logitech receivers library

import gettext as _gettext

_ = _gettext.gettext
ngettext = _gettext.ngettext

# A few common strings, not always accessible as such in the code.

_DUMMY = (
    # approximative battery levels
    _("empty"),
    _("critical"),
    _("low"),
    _("good"),
    _("full"),
    # battery charging statuses
    _("discharging"),
    _("recharging"),
    _("almost full"),
    _("charged"),
    _("slow recharge"),
    _("invalid battery"),
    _("thermal error"),
    # pairing errors
    _("device timeout"),
    _("device not supported"),
    _("too many devices"),
    _("sequence timeout"),
    # firmware kinds
    _("FW_VERSION"),
    _("FW_BUILD"),
    _("HW_VERSION"),
    _("BL_VERSION"),
)
