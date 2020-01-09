from logitech_receiver import hidpp10, hidpp20
from logitech_receiver.common import KwException


class NoReceiver(KwException):
    """Raised when trying to talk through a previously open handle, when the
    receiver is no longer available. Should only happen if the receiver is
    physically disconnected from the machine, or its kernel driver module is
    unloaded."""

    pass


class NoSuchDevice(KwException):
    """Raised when trying to reach a device number not paired to the receiver."""

    pass


class DeviceUnreachable(KwException):
    """Raised when a request is made to an unreachable (turned off) device."""

    pass


class ReadException(Exception):
    def __init__(self, protocol: float, code: int):
        self.protocol_version = protocol
        self.code = code
        super().__init__()

    def error(self):
        return {1.0: hidpp10, 2.0: hidpp20}[self.protocol_version].Error[self.code]

    def __str__(self):
        return f"HIDPP{self.protocol_version}0: {self.error()}"
