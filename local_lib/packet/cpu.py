#scapy
from scapy.all import Ether, Packet, XBitField, ShortField, bind_layers, ByteField, ByteEnumField, IntField # type: ignore

#############################################################
# CPU Packet                                               #
#############################################################

cpu_reason_types = {
    0: "IGNORE",
    1: "NOTIFICATION",
    2: "CONFIG",
    3: "SEND",
    4: "SEND_DIRECT"
}

class CPUPacket(Packet):

    TYPE_BDDP = 0x8999
    TYPE_LLDP = 0x88cc
    TYPE_MACSEC = 0x88e5

    name = "CPU Packet"
    fields_desc = [
        ByteEnumField("reason", 0, cpu_reason_types),
        ShortField("port", 0),
        XBitField("timestamp", 0, size=48),
        ByteField("switched_mac_src_with_dst", 0)
    ]


config_types = {
    1: "MACSEC_RESET_COUNTER",
    2: "MACSEC_SET_SOFT_PACKET_LIMIT",
    3: "MACSEC_SET_HARD_PACKET_LIMIT",
    4: "IPSEC_RESET_COUNTER"
}

class Config(Packet):
    name = "Config"

    fields_desc = [
        ByteEnumField("type", 1, config_types),
        XBitField("index", 0, size=32),
        XBitField("value", 0, size=32)
    ]


notification_types = {
    1: "DST_MAC_UNKNOWN",
    2: "SRC_MAC_UNKNOWN",
    3: "REFRESH_L2_ENTRY",
    4: "CHANGED_L2_ENTRY",
    5: "ARP",
    6: "LLDP",
    7: "EAP",
    8: "MACSEC_SOFT_PACKET_LIMIT",
    9: "MACSEC_HARD_PACKET_LIMIT",
    10: "IPSEC_SOFT_PACKET_LIMIT",
    11: "IPSEC_HARD_PACKET_LIMIT"
}

class Notification(Packet):
    name = "Notification"

    fields_desc = [
        ByteEnumField("type", 1, notification_types),
        IntField("index", 0)
    ]

bind_layers(CPUPacket, Ether, reason=CPUPacket(reason="SEND").reason)
bind_layers(CPUPacket, Ether, reason=CPUPacket(reason="SEND_DIRECT").reason)
bind_layers(CPUPacket, Notification, reason=CPUPacket(reason="NOTIFICATION").reason)
bind_layers(CPUPacket, Config, reason=CPUPacket(reason="CONFIG").reason)
bind_layers(Notification, Ether)
