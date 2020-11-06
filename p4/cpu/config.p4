/* -*- P4_16 -*- */
#ifndef CONFIG_P4_3JFYKE0Q
#define CONFIG_P4_3JFYKE0Q

enum bit<8> ConfigType {
	MACSEC_RESET_COUNTER = 1,
	MACSEC_SET_SOFT_PACKET_LIMIT = 2,
	MACSEC_SET_HARD_PACKET_LIMIT = 3,
	IPSEC_RESET_COUNTER = 4
}

header config_t {
	ConfigType type;
	bit<32>    index;
	bit<32>    value;
}

#endif /* end of include guard: CONFIG_P4_3JFYKE0Q */
