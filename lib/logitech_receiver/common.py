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

# Some common functions and types.

from __future__ import absolute_import, division, print_function, unicode_literals

from binascii import hexlify as _hexlify
from aenum import Enum, extend_enum
from struct import pack, unpack

try:
    unicode
    # if Python2, unicode_literals will mess our first (un)pack() argument
    _pack_str = pack
    _unpack_str = unpack
    pack = lambda x, *args: _pack_str(str(x), *args)
    unpack = lambda x, *args: _unpack_str(str(x), *args)

    is_string = lambda d: isinstance(d, unicode) or isinstance(d, str)
# no easy way to distinguish between b'' and '' :(
# or (isinstance(d, str) \
# 	and not any((chr(k) in d for k in range(0x00, 0x1F))) \
# 	and not any((chr(k) in d for k in range(0x80, 0xFF))) \
# 	)
except:
    # this is certanly Python 3
    # In Py3, unicode and str are equal (the unicode object does not exist)
    is_string = lambda d: isinstance(d, str)


#
#
#


class NamedInt(int):
    """An reqular Python integer with an attached name.

    Caution: comparison with strings will also match this NamedInt's name
    (case-insensitive)."""

    def __new__(cls, value, name):
        assert is_string(name)
        obj = int.__new__(cls, value)
        obj.name = str(name)
        return obj

    def bytes(self, count=2):
        return int2bytes(self, count)

    def __eq__(self, other):
        if isinstance(other, NamedInt):
            return int(self) == int(other) and self.name == other.name
        if isinstance(other, int):
            return int(self) == int(other)
        if is_string(other):
            return self.name.lower() == other.lower()
        # this should catch comparisons with bytes in Py3
        if other is not None:
            raise TypeError("Unsupported type " + str(type(other)))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return int(self)

    def __str__(self):
        return self.name

    __unicode__ = __str__

    def __repr__(self):
        return "NamedInt(%d, %r)" % (int(self), self.name)


class ReNamedInts(int, Enum):
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
        extend_enum(cls, "unknown:%04X" % value, (value, ))
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
