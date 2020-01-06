# -*- python-mode -*-
# -*- coding: UTF-8 -*-

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

from binascii import hexlify as _hexlify
from struct import pack, unpack

from aenum import IntEnum, extend_enum


class NamedInts(IntEnum):
    @classmethod
    def flag_names(cls, value):
        unknown_bits = value
        for k, v in cls._member_map_.items():
            assert bin(v).count("1") == 1
            if v & value == v:
                unknown_bits &= ~v
                yield k

        if unknown_bits:
            yield "unknown:%06X" % unknown_bits

    @classmethod
    def _missing_(cls, value):
        extend_enum(cls, "unknown:%04X" % value, (value,))
        return cls(value)


def strhex(x: bytes):
    assert x is not None
    """Produce a hex-string representation of a sequence of bytes."""
    return _hexlify(x).decode("ascii").upper()


def bytes2int(x):
    """Convert a bytes string to an int.
    The bytes are assumed to be in most-significant-first order.
    """
    assert isinstance(x, bytes)
    assert len(x) < 9
    qx = (b"\x00" * 8) + x
    (result,) = unpack("!Q", qx[-8:])
    # assert x == int2bytes(result, len(x))
    return result


def int2bytes(x, count=None):
    """Convert an int to a bytes representation.
    The bytes are ordered in most-significant-first order.
    If 'count' is not given, the necessary number of bytes is computed.
    """
    assert isinstance(x, int)
    result = pack("!Q", x)
    assert isinstance(result, bytes)
    # assert x == bytes2int(result)

    if count is None:
        return result.lstrip(b"\x00")

    assert isinstance(count, int)
    assert count > 0
    assert x.bit_length() <= count * 8
    return result[-count:]


class KwException(Exception):
    """An exception that remembers all arguments passed to the constructor.
    They can be later accessed by simple member access.
    """

    def __init__(self, **kwargs):
        super(KwException, self).__init__(kwargs)

    def __getattr__(self, k):
        try:
            return super(KwException, self).__getattr__(k)
        except AttributeError:
            return self.args[0][k]


from collections import namedtuple

"""Firmware information."""
FirmwareInfo = namedtuple("FirmwareInfo", ["kind", "name", "version", "extras"])

"""Reprogrammable keys information."""
ReprogrammableKeyInfo = namedtuple(
    "ReprogrammableKeyInfo", ["index", "key", "task", "flags"]
)

ReprogrammableKeyInfoV4 = namedtuple(
    "ReprogrammableKeyInfoV4",
    ["index", "key", "task", "flags", "pos", "group", "group_mask", "remapped"],
)

del namedtuple
