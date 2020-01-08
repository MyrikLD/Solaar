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

from struct import unpack, pack

from logitech_receiver import special_keys
from logitech_receiver.common import ReprogrammableKeyInfoV4, ReprogrammableKeyInfo
from .utils import feature_request
from .enums import Feature
from logging import getLogger


_log = getLogger(__name__)
del getLogger


class FeaturesArray:
    """A sequence of features supported by a HID++ 2.0 device."""

    __slots__ = ("supported", "device", "features")
    assert Feature.ROOT == 0x0000

    def __init__(self, device):
        assert device is not None
        self.device = device
        self.supported = True
        self.features = None

    def __del__(self):
        self.supported = False
        self.device = None
        self.features = None

    def _check(self):
        # print (self.device, "check", self.supported, self.features, self.device.protocol)
        if self.supported:
            assert self.device
            if self.features is not None:
                return True

            if not self.device.online:
                # device is not connected right now, will have to try later
                return False

            # I _think_ this is universally true
            if self.device.protocol and self.device.protocol < 2.0:
                self.supported = False
                self.device.features = None
                self.device = None
                return False

            reply = self.device.request(0x0000, pack("!H", Feature.FEATURE_SET))
            if reply is None:
                self.supported = False
            else:
                fs_index = reply[0]
                if fs_index:
                    count = self.device.request(fs_index << 8)
                    if count is None:
                        _log.warning(
                            "FEATURE_SET found, but failed to read features count"
                        )
                        # most likely the device is unavailable
                        return False
                    else:
                        count = count[0]
                        assert count >= fs_index
                        self.features = [None] * (1 + count)
                        self.features[0] = Feature.ROOT
                        self.features[fs_index] = Feature.FEATURE_SET
                        return True
                else:
                    self.supported = False

        return False

    def __bool__(self):
        return self._check()

    def __getitem__(self, index):
        if self._check():
            if isinstance(index, int):
                if index < 0 or index >= len(self.features):
                    raise IndexError(index)

                if self.features[index] is None:
                    feature = self.device.feature_request(
                        Feature.FEATURE_SET, 0x10, index
                    )
                    if feature:
                        (feature,) = unpack("!H", feature[:2])
                        self.features[index] = Feature(feature)

                return self.features[index]

            elif isinstance(index, slice):
                indices = index.indices(len(self.features))
                return [self.__getitem__(i) for i in range(*indices)]

    def __contains__(self, feature_id):
        """Tests whether the list contains given Feature ID"""
        if self._check():
            ivalue = int(feature_id)

            may_have = False
            for f in self.features:
                if f is None:
                    may_have = True
                elif ivalue == int(f):
                    return True

            if may_have:
                reply = self.device.request(0x0000, pack("!H", ivalue))
                if reply:
                    index = reply[0]
                    if index:
                        self.features[index] = Feature(ivalue)
                        return True

    def index(self, feature_id):
        """Gets the Feature Index for a given Feature ID"""
        if self._check():
            may_have = False
            ivalue = int(feature_id)
            for index, f in enumerate(self.features):
                if f is None:
                    may_have = True
                elif ivalue == int(f):
                    return index

            if may_have:
                reply = self.device.request(0x0000, pack("!H", ivalue))
                if reply:
                    index = reply[0]
                    self.features[index] = Feature(ivalue)
                    return index

        raise ValueError("%r not in list" % feature_id)

    def __iter__(self):
        if self._check():
            yield Feature.ROOT
            index = 1
            last_index = len(self.features)
            while index < last_index:
                yield self.__getitem__(index)
                index += 1

    def __len__(self):
        return len(self.features) if self._check() else 0


class KeysArray:
    """A sequence of key mappings supported by a HID++ 2.0 device."""

    __slots__ = ("device", "keys", "keyversion")

    def __init__(self, device, count):
        assert device is not None
        self.device = device
        self.keyversion = 0
        self.keys = [None] * count

    def __getitem__(self, index):
        if isinstance(index, int):
            if index < 0 or index >= len(self.keys):
                raise IndexError(index)

            # TODO: add here additional variants for other REPROG_CONTROLS
            if self.keys[index] is None:
                keydata = feature_request(
                    self.device, Feature.REPROG_CONTROLS, 0x10, index
                )
                self.keyversion = 1
                if keydata is None:
                    keydata = feature_request(
                        self.device, Feature.REPROG_CONTROLS_V4, 0x10, index
                    )
                    self.keyversion = 4
                if keydata:
                    key, key_task, flags, pos, group, gmask = unpack(
                        "!HHBBBB", keydata[:8]
                    )
                    ctrl_id_text = special_keys.CONTROL(key)
                    ctrl_task_text = special_keys.TASK(key_task)
                    if self.keyversion == 1:
                        self.keys[index] = ReprogrammableKeyInfo(
                            index, ctrl_id_text, ctrl_task_text, flags
                        )
                    if self.keyversion == 4:
                        remapped = key

                        try:
                            mapped_data = feature_request(
                                self.device,
                                Feature.REPROG_CONTROLS_V4,
                                0x20,
                                key & 0xFF00,
                                key & 0xFF,
                            )
                            if mapped_data:
                                remap_key, remap_flag, remapped = unpack(
                                    "!HBH", mapped_data[:5]
                                )
                                # if key not mapped map it to itself for display
                                if remapped == 0:
                                    remapped = key
                        except Exception:
                            pass

                        remapped_text = special_keys.CONTROL(remapped)
                        self.keys[index] = ReprogrammableKeyInfoV4(
                            index,
                            ctrl_id_text,
                            ctrl_task_text,
                            flags,
                            pos,
                            group,
                            gmask,
                            remapped_text,
                        )

            return self.keys[index]

        elif isinstance(index, slice):
            indices = index.indices(len(self.keys))
            return [self.__getitem__(i) for i in range(*indices)]

    def index(self, value):
        for index, k in enumerate(self.keys):
            if k is not None and int(value) == int(k.key):
                return index

        for index, k in enumerate(self.keys):
            if k is None:
                k = self.__getitem__(index)
                if k is not None:
                    return index

    def __iter__(self):
        for k in range(0, len(self.keys)):
            yield self.__getitem__(k)

    def __len__(self):
        return len(self.keys)
