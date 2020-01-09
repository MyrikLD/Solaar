from logitech_receiver.common import NamedInts


class ReportType(NamedInts):
    ALL = 0x00  # Reserved
    KEYBOARD = 0x01  # Standard-keyboard keys
    MOUSE = 0x02  # Mouse
    CONSUMER_KEYS = 0x03  # Consumer control keys
    POWER = 0x04  # Power keys
    MEDIACENTER = 0x08  # Microsoft MediaCenter keys (vendor specific)
    HIDPP_SHORT = 0x10  # Short HID++ messages (7 bytes)
    HIDPP_LONG = 0x11  # Long HID++ messages (20 bytes)
    HIDPP_VERY_LONG = 0x12  # Very-long HID++ messages (64 bytes)
    HIDPP_EXTRA_LONG = 0x13  # Extra-long HID++ messages (111 bytes)
    DJ_BUS_ENUM_SHORT = 0x20  # DJ bus enumerator short messages
    DJ_BUS_ENUM_LONG = 0x21
