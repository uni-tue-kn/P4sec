/* -*- P4_16 -*- */
#ifndef HEADER_P4_UNNY2ICH
#define HEADER_P4_UNNY2ICH

#include "config.p4"
#include "notification.p4"

enum bit<8> CPUReason {
	IGNORE = 0,
	NOTIFICATION = 1,
	CONFIG = 2,
	SEND = 3,
	SEND_DIRECT = 4
}

header cpu_header_t {
	CPUReason reason;
	bit<16> port;
	bit<48> timestamp;
	bit<8>  switched_mac_src_with_dst;
}

struct cpu_t {
	cpu_header_t   base;
	config_t       config;
	notification_t notification;
}

#endif /* end of include guard: HEADER_P4_UNNY2ICH */
