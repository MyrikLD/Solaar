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

from logitech_receiver.common import NamedInts


#
# Constants - most of them as defined by the official Logitech HID++ 1.0
# documentation, some of them guessed.
#


class DeviceKind(NamedInts):
    keyboard = 0x01
    mouse = 0x02
    numpad = 0x03
    presenter = 0x04
    headset = 0x05  # Headset (Trifecta, Reg. HIDPP_REG_CURRENT_DEVICE)
    speaker_phone = 0x06  # Speaker phone (2Face, Reg. HIDPP_REG_CURRENT_DEVICE)
    remote_control = 0x07
    trackball = 0x08
    touchpad = 0x09  # Touchpad (relative displacement)
    tablet = 0x0A
    gamepad = 0x0B
    joystick = 0x0C

    @classmethod
    def from_name(cls, name: str):
        for k, v in cls._mapping().items():
            if k in name:
                return v

    @classmethod
    def _mapping(cls):
        return {
            "Mouse": cls.mouse,
            "Keyboard": cls.keyboard,
            "Number Pad": cls.numpad,
            "Touchpad": cls.touchpad,
            "Trackball": cls.trackball,
        }


class PowerSwitchLocation(NamedInts):
    base = 0x01
    top_case = 0x02
    edge_of_top_right_corner = 0x03
    top_left_corner = 0x05
    bottom_left_corner = 0x06
    top_right_corner = 0x07
    bottom_right_corner = 0x08
    top_edge = 0x09
    right_edge = 0x0A
    left_edge = 0x0B
    bottom_edge = 0x0C


# Some flags are used both by devices and receivers. The Logitech documentation
# mentions that the first and last (third) byte are used for devices while the
# second is used for the receiver. In practise, the second byte is also used for
# some device-specific notifications (keyboard illumination level). Do not
# simply set all notification bits if the software does not support it. For
# example, enabling keyboard_sleep_raw makes the Sleep key a no-operation unless
# the software is updated to handle that event.
# Observations:
# - wireless and software present were seen on receivers, reserved_r1b4 as well
# - the rest work only on devices as far as we can tell right now
# In the future would be useful to have separate enums for receiver and device notification flags,
# but right now we don't know enough.
class NotificateionFlag(NamedInts):
    battery_status = 0x100000  # send battery charge notifications (0x07 or 0x0D)
    keyboard_sleep_raw = 0x020000  # system control keys such as Sleep
    keyboard_multimedia_raw = 0x010000  # consumer controls such as Mute and Calculator
    # reserved_r1b4 = 0x001000  # unknown seen on a unifying receiver
    software_present = 0x000800  # .. no idea
    keyboard_illumination = (
        0x000200  # illumination brightness level changes (by pressing keys)
    )
    wireless = 0x000100  # notify when the device wireless goes on/off-line


class Error(NamedInts):
    INVALID_SUBID = 0x01  # Invalid sub-identifier / command
    INVALID_ADDRESS = 0x02  # Invalid address
    INVALID_VALUE = 0x03  # Invalid value
    CONNECT_FAIL = 0x04  # Connection request failed (receiver)
    TOO_MANY_DEVICES = 0x05  # Too many devices connected (receiver)
    ALREADY_EXISTS = 0x06  # Already exists (receiver)
    BUSY = 0x07  # Busy (receiver)
    UNKNOWN_DEVICE = 0x08  # Unknown device (receiver)
    RESOURCE_ERROR = 0x09  # Resource error (receiver)
    INVALID_STATE = 0x0A  # Request not valid in current state
    INVALID_PARAM = 0x0B  # Invalid parameter(s)
    WRONG_PIN_CODE = 0x0C


class PairingErrors(NamedInts):
    device_timeout = 0x01
    device_not_supported = 0x02
    too_many_devices = 0x03
    sequence_timeout = 0x06


class BatteryAppox(NamedInts):
    empty = 0
    critical = 5
    low = 20
    good = 50
    full = 90


class Registers(NamedInts):
    """Known registers.
    Devices usually have a (small) sub-set of these. Some registers are only
    applicable to certain device kinds (e.g. smooth_scroll only applies to mice."""

    HIDPP_REPORTING = 0x00  # Enable HID++ reporting
    # only apply to devices
    mouse_button_flags = 0x01
    keyboard_hand_detection = 0x01
    FEATURES = 0x01  # Enable individual features
    # only apply to receivers
    CONNECTION_STATE = 0x02  # Connection state
    SW_UPDATE_PENDING = 0x03  # Software update pending
    # only apply to devices
    BATTERY_STATUS = 0x07  # Battery status
    UI_EVENT = 0x08  # User interface event and status {read-only}
    # only apply to devices
    F_LOCK = 0x09  # F-Lock status
    # only apply to devices
    BATTERY_MILEAGE = 0x0D  # Battery mileage {read-only}
    FEATURES_CONT = 0x0E  # Enable individual features (extension to Reg. 0x01)
    PROFILE_MGT = 0x0F  # Profile management
    LCD_MODE = 0x10  # LCD mode {write-only}
    LCD_ICONS = (
        0x11  # LCD notification icons {long} (obsolete use \ref HIDPP_REG_UI_NOTIF)
    )
    LCD_CMD = 0x12  # LCD command {write-only}
    LCD_DESCR = 0x13  # LCD descriptor {long} (obsolete)
    LCD_FW_VERSION = 0x14  # LCD FW_VERSION version {long} {read-only} (obsolete)
    LCD_CONTRAST = 0x15  # LCD contrast (obsolete)
    # only apply to devices
    LCD_BACKLIGHT = 0x17  # LCD backlight
    LCD_DATAL1B0 = 0x20  # LCD content line 1 buffer 0 {long}
    LCD_DATAL1B1 = 0x21  # LCD content line 1 buffer 1 {long}
    LCD_DATAL1B2 = 0x22  # LCD content line 1 buffer 2 {long}
    LCD_DATAL2B0 = 0x23  # LCD content line 2 buffer 0 {long}
    LCD_DATAL2B1 = 0x24  # LCD content line 2 buffer 1 {long}
    LCD_DATAL2B2 = 0x25  # LCD content line 2 buffer 2 {long}
    LCD_DATAL3B0 = 0x26  # LCD content line 3 buffer 0 {long}
    LCD_DATAL3B1 = 0x27  # LCD content line 3 buffer 1 {long}
    LCD_DATAL3B2 = 0x28  # LCD content line 3 buffer 2 {long}
    TIME_FORMAT = 0x30  # Time and date format
    TIME_VALUE = 0x31  # Time value
    DATE_VALUE_MDW = 0x32  # Date value= month day and week
    DATE_VALUE_Y = 0x33  # Date value= year
    USER_NAME = 0x34  # User name {long}
    CALC_FORMAT = 0x35  # Calculator format
    LOC_WRITE_CONTROL = 0x40  # Localization write control (status) {read-only}
    LOC_MONTH_NAME_00_0F = (
        0x41  # Localized month names non-volatile memory addresses 0x00 .. 0x0F {long}
    )
    LOC_MONTH_NAME_10_1F = (
        0x42  # Localized month names non-volatile memory addresses 0x10 .. 0x1F {long}
    )
    LOC_MONTH_NAME_20_2F = (
        0x43  # Localized month names non-volatile memory addresses 0x20 .. 0x2F {long}
    )
    LOC_MONTH_NAME_30_3B = (
        0x44  # Localized month names non-volatile memory addresses 0x30 .. 0x3B {long}
    )
    LOC_STRING_CONNECTING = 0x45  # Localized string "Connecting" {long}
    LOC_STRING_NOT_AVAILABLE = 0x46  # Localized string "Not available" {long}
    LOC_STRING_CONNECTED = 0x47  # Localized string "Connected" {long}
    LOC_STRING_FAILED = 0x48  # Localized string "Failed" {long}
    UI_ACTION = 0x50  # User interface action
    # only apply to devices
    UI_LEDS = 0x51  # User interface LEDs
    UI_NOTIF = 0x52  # User interface notification icons {short long}
    TOUCHPAD_SETTINGS = 0x53  # Touchpad settings
    LED_INTENSITY = 0x54  # LED intensity
    AIR_FEATURE = 0x55  # Air feature (3D movement)
    THREEG_ROLLER_CONTROL = 0x56  # 3G roller control
    LED_RGB_CONTROL = 0x57  # LED RGB color control
    DAC_CODEC = 0x59  # Dedicated audio controls= CODEC
    DAC_PARAM = 0x5A  # Dedicated audio controls= parameters
    VOIP_STATUS = 0x5C  # VoIP call and audio status
    SENSOR_SETTINGS = 0x60  # Optical sensor configuration settings
    SENSOR_RAW_DATA = 0x61  # Optical sensor raw data
    SENSOR_PROCESS_DATA = 0x62  # Optical sensor processed data {read-only}
    # only apply to devices
    SENSOR_RESOLUTION = 0x63  # Optical sensor resolution and frame rate {short long}
    TIME_BETWEEN_REPORT = 0x64  # Time between report
    SENSOR_RES_TOGGLE = 0x65  # Optical sensor resolution toggle
    GESTURE_CONTROL = 0x68  # Gesture control
    BIRKIN_CONTROL = 0x69  # Birkin control {long} {read-only}
    RX0_RADIO_LINK_CONTROL = 0x70  # Receiver 0 radio link control
    RX1_RADIO_LINK_CONTROL = 0x71  # Receiver 1 radio link control
    TX_RADIO_LINK_CONTROL = 0x72  # Transmitter radio link control
    RECEIVER_SETTINGS = 0x73  # Receiver scan settings
    TRACEABILITY_ACCESS = 0x78  # Traceability access {short long} {read-only}
    RECEIVER_MODE = 0x80  # Receiver mode
    DISCOVER_DEVICE = 0x81  # Device discovery
    CONNECT_DEVICE = 0x82  # Device connection & deconnection
    CURRENT_DEVICE = 0x83  # Current active device {long}
    LEDS_ALL_ON = 0x84  # LED blinking pattern for connection {write-only}
    VIRTUAL_CABLE_KBD = 0x85  # Virtual cable information for keyboard {long}
    VIRTUAL_CABLE_MSE = 0x86  # Virtual cable information for mouse {long}
    VIRTUAL_CABLE_NUM = 0x87  # Virtual cable information for numeric pad {long}
    PIN_CODE = (
        0x88  # Current device (see \ref HIDPP_REG_CURRENT_DEVICE) PIN code (BT) {long}
    )
    DEVICE_CONNECTIVITY = 0x89  # Device connectivity control {write-only}
    RFID_PAIRING_INFO = 0x8A  # RFID pairing information (BT) {long} {read-only}
    DEVICE_DESCR = 0x90  # Current device (see \ref HIDPP_REG_CURRENT_DEVICE) SDP information (BT) {long} {read-only}
    DEVICE_NAME_1 = 0x91  # Current device (see \ref HIDPP_REG_CURRENT_DEVICE) name part 1 (bytes 1 to 16) (BT) {long} {read-only}
    DEVICE_NAME_2 = 0x92  # Current device (see \ref HIDPP_REG_CURRENT_DEVICE) name part 2 (bytes 17 to 32) (BT) {long} {read-only}
    SIGNAL_QUALITY = 0x93  # Signal quality (BT) {read-only}
    BQB = 0x99  # Current device (see \ref HIDPP_REG_CURRENT_DEVICE) BQB test command (BT) {short long}
    MEMORY_MGT = 0xA0  # Memory management {long} {write-only}
    HOT_SYNERGY = 0xA1  # HOT/SYNERGY command
    READ_SECTOR = 0xA2  # Read sector {long} {read-only}
    LINK_QUALITY_INFO = 0xB0  # Link quality information (Quad) {read-only}
    FORCE_QUAD_CHANNEL = 0xB1  # Force Quad channel / disable agility (Quad)
    # only apply to receivers
    QUAD_CONNECT_DEVICE = (
        0xB2  # Quad device connection and disconnection (Quad eQuad) {write-only}
    )
    DEVICE_ACTIVITY = 0xB3  # Device activity (eQuad) {long} {read-only}
    NV_PAIRING_INFO = 0xB5  # Non-volatile and pairing information (Quad eQuad) {long}
    TESTMODE_CONTROL = 0xD0  # Test mode control
    RF_REGISTER = 0xD1  # RF register access {short long}
    RAM_SINGLE = 0xD2  # RAM access (single-byte)
    RAM_MULTI = 0xD3  # RAM access (multi-bytes) {long}
    EEPROM_SINGLE = 0xD4  # Non-volatile memory (EEPROM) access (single-byte)
    EEPROM_MULTI = 0xD5  # Non-volatile memory (EEPROM) access (multi-bytes) {long}
    EEPROM_SECURED = 0xD6  # Non-volatile memory (EEPROM) secured access
    EEPROM_OPERATION = 0xD7  # Non-volatile memory (EEPROM) operation {write-only}
    EEPROM_CHECKSUM = 0xD8  # Non-volatile memory (EEPROM) checksum {read-only}
    UI = 0xD9  # User interface
    SPI = 0xDA  # SPI access
    MOUSE_SENSOR = 0xDB  # Optical mouse sensor {long} {read-only}
    PAIRING_INFORMATION = (
        0xDC  # Device pairing information in non-volatile memory and RAM
    )
    POWER_MODE = 0xDD  # Power mode {write-only}
    SPI_CS = 0xDE  # SPI chip select
    MANUFACTURING_PARAM = (
        0xDF  # Manufacturing parameters (device-dependent) {read-only}
    )
    SET_HCI = 0xE1  # Send an HCI request {long very-long} {write-only}
    SET_ACL = 0xE2  # Send an ACL request {long very-long} {write-only}
    DFU_LITE_DATA = 0xE2  # DFU Lite data {long}
    RFID = 0xE3  # RFID access {long}
    HW_STATE = 0xE4  # Hardware state {read-only}
    UART_TX = 0xE5  # UART transmitted string {very-long} {write-only}
    ENCRYPT_ERR_COUNTER = (
        0xE6  # Encryption rejected-frame counter (eQuad debug) {read-only}
    )
    USB_ICP = 0xF0  # Enter USB ICP/DFU/OTA DFU programming mode
    FW_VERSION = 0xF1  # Firmware version {read-only}
    RESET = 0xF2  # Reset {write-only}
    DEBUG_MODE = 0xF3  # Debug mode (eQuad)
    FW_DEBUG = 0xFD  # General-purpose FW_VERSION debug (device-dependent) {short, long}

    # only apply to receivers
    devices_activity = 0x2B3
    receiver_info = 0x2B5


class FirmwareVersionItem(NamedInts):
    FW_VERSION = 0x01  # Firmware name/number & version
    FW_BUILD = 0x02  # Firmware build number
    HW_VERSION = 0x03  # Hardware version
    BL_VERSION = 0x04  # Bootloader version & build number


class SubId(NamedInts):
    # HID++ notifications (0x00 .. 0x7F)
    ALL = 0x00  # Reserved
    KEYBOARD = 0x01  # Reserved for standard-keyboard keys
    MOUSE = 0x02  # Reserved for mouse
    CONSUMER_KEYS = 0x03  # Consumer control keys
    POWER = 0x04  # Power keys
    ROLLER = 0x05  # Roller
    MOUSE_EXTRA_BT = 0x06  # Mouse extra buttons
    BATTERY_STATUS = 0x07  # Battery status
    UI_EVENT = 0x08  # User interface events
    F_LOCK = 0x09  # F-Lock status
    CALC_RESULT = 0x0A  # Calculator result {long}
    MENU_ENTER = 0x0B  # Navigation menu enter
    FN_PLUS_ALPHANUMKEY = 0x0C  # Fn + alpha-numeric key
    BATTERY_MILEAGE = 0x0D  # Battery mileage
    UART_RX = 0x0E  # UART received string {very-long}
    BACKLIGHT_DURATION = 0x17  # Backlight duration update
    DEVICE_DISCONNECT = 0x40  # Device disconnection
    DEVICE_CONNECT = 0x41  # Device connection
    DEVICE_DISCOVERY = 0x42  # Device discovery (BT) {long}
    PIN_CODE_REQ = 0x43  # PIN code request
    RCV_WORKING_MODE = 0x44  # Receiver working mode (BT)
    NOTIFICATION_ERROR = 0x45  # Error notification
    RFLINK_CHANGE = 0x46  # RF link change (27 MHz)
    ENCRYPTION_KEY = 0x47  # Encryption key (27 MHz Quad) {long}
    HCI_NOTIFICATION = 0x48  # HCI notification (BT) {long very-long}
    LINK_QUALITY_INFO = 0x49  # Link quality information (eQuad) {short long}
    QUAD_LOCKING_INFO = 0x4A  # Quad locking change information (Quad eQuad)
    WL_DEV_CHANGE_INFO = 0x4B  # Wireless device change information
    HOT_NOTIFICATION = 0x50  # HOT/SYNERGY notification
    ACL_NOTIFICATION = 0x51  # ACL notification {very-long}
    VOIP_TELEPHONY_EVENT = 0x5B  # VoIP telephony event
    LED_NOTIFICATION = 0x60  # LED notification
    GEST_NOTIFICATION = 0x65  # Gesture and air feature notification
    MULTI_TOUCH_NOTIFICATION = 0x66  # Touchpad multi-touch notification {long}
    TRACEABILITY_NOTIFICATION = 0x78  # Traceability notification

    # HID++ register access (0x80 .. 0x8F)
    SET_REGISTER = 0x80  # Set short register (short request/short response)
    GET_REGISTER = 0x81  # Get short register (short request/short response)
    SET_LONG_REGISTER = 0x82  # Set long register (long request/short response) {long}
    GET_LONG_REGISTER = 0x83  # Get long register (short request/long response) {long}
    SET_VERY_LONG_REGISTER = (
        0x84  # Set very-long register (very-long request/short response) {very-long}
    )
    GET_VERY_LONG_REGISTER = (
        0x85  # Get very-long register (short request/very-long response) {very-long}
    )
    ERROR_MSG_REGISTER = 0x8F  # Error message

    # HOT (0x90 .. 0xFF)
    TRANS_INIT_ASYN = (
        0x90  # First asynchronous payload packet in a HOT stream {long very-long}
    )
    TRANS_CONT_ASYN = (
        0x91  # Next asynchronous payload packet in a HOT stream {long very-long}
    )
    TRANS_INIT_SYN = (
        0x92  # First synchronous payload packet in a HOT stream {long very-long}
    )
    TRANS_CONT_SYN = (
        0x93  # Next synchronous payload packet in a HOT stream {long very-long}
    )
    RETRY_INIT_ASYN = 0x94  # First asynchronous payload packet in a HOT stream re-sent {long very-long}
    RETRY_CONT_ASYN = 0x95  # Next asynchronous payload packet in a HOT stream re-sent {long very-long}
    RETRY_INIT_SYN = 0x96  # First synchronous payload packet in a HOT stream re-sent {long very-long}
    RETRY_CONT_SYN = (
        0x97  # Next synchronous payload packet in a HOT stream re-sent {long very-long}
    )
    SYNC = 0xFF
