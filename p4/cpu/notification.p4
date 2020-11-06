/* -*- P4_16 -*- */
#ifndef NOTIFICATION_P4_IMQIUOWX
#define NOTIFICATION_P4_IMQIUOWX

enum bit<8> NotificationType {
    DST_MAC_UNKNOWN = 1,
    SRC_MAC_UNKNOWN = 2,
    REFRESH_L2_ENTRY = 3,
    CHANGED_L2_ENTRY = 4,
    ARP = 5,
    LLDP = 6,
    EAP = 7,
    MACSEC_SOFT_PACKET_LIMIT = 8,
    MACSEC_HARD_PACKET_LIMIT = 9,
	IPSEC_SOFT_PACKET_LIMIT = 10,
	IPSEC_HARD_PACKET_LIMIT = 11
}

header notification_t {
	NotificationType type;
	bit<32>          index;
}

#endif /* end of include guard: NOTIFICATION_P4_IMQIUOWX */
