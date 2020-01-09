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

# USB ids of Logitech wireless receivers.
# Only receivers supporting the HID++ protocol can go in here.

_DRIVER = ("hid-generic", "generic-usb", "logitech-djreceiver")

# each tuple contains (vendor_id, product_id, usb interface number, hid driver)
_unifying_receiver = lambda product_id: (0x046D, product_id, 2, _DRIVER)
_nano_receiver = lambda product_id: (0x046D, product_id, 1, _DRIVER)
_lenovo_receiver = lambda product_id: (0x17EF, product_id, 1, _DRIVER)
_lightspeed_receiver = lambda product_id: (0x046D, product_id, 2, _DRIVER)

# standard Unifying receivers (marked with the orange Unifying logo)
UNIFYING_RECEIVER_C52B = _unifying_receiver(0xC52B)
UNIFYING_RECEIVER_C532 = _unifying_receiver(0xC532)

# Nano receviers that support the Unifying protocol
NANO_RECEIVER_ADVANCED = _nano_receiver(0xC52F)

# Nano receivers that don't support the Unifying protocol
NANO_RECEIVER_C517 = _nano_receiver(0xC517)
NANO_RECEIVER_C518 = _nano_receiver(0xC518)
NANO_RECEIVER_C51A = _nano_receiver(0xC51A)
NANO_RECEIVER_C51B = _nano_receiver(0xC51B)
NANO_RECEIVER_C521 = _nano_receiver(0xC521)
NANO_RECEIVER_C525 = _nano_receiver(0xC525)
NANO_RECEIVER_C526 = _nano_receiver(0xC526)
NANO_RECEIVER_C52e = _nano_receiver(0xC52E)
NANO_RECEIVER_C531 = _nano_receiver(0xC531)
NANO_RECEIVER_C534 = _nano_receiver(0xC534)
NANO_RECEIVER_6042 = _lenovo_receiver(0x6042)

# Lightspeed receivers
LIGHTSPEED_RECEIVER_C539 = _lightspeed_receiver(0xC539)
LIGHTSPEED_RECEIVER_C53a = _lightspeed_receiver(0xC53A)
LIGHTSPEED_RECEIVER_C53f = _lightspeed_receiver(0xC53F)

del _DRIVER, _unifying_receiver, _nano_receiver, _lenovo_receiver, _lightspeed_receiver

RECEIVER_USB_IDS = (
    UNIFYING_RECEIVER_C52B,
    UNIFYING_RECEIVER_C532,
    NANO_RECEIVER_ADVANCED,
    NANO_RECEIVER_C517,
    NANO_RECEIVER_C518,
    NANO_RECEIVER_C51A,
    NANO_RECEIVER_C51B,
    NANO_RECEIVER_C521,
    NANO_RECEIVER_C525,
    NANO_RECEIVER_C526,
    NANO_RECEIVER_C52e,
    NANO_RECEIVER_C531,
    NANO_RECEIVER_C534,
    NANO_RECEIVER_6042,
    LIGHTSPEED_RECEIVER_C539,
    LIGHTSPEED_RECEIVER_C53a,
    LIGHTSPEED_RECEIVER_C53f,
)
