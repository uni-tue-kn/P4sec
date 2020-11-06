/* -*- P4_16 -*- */
#ifndef UTIL_P4_4ISDU9QI
#define UTIL_P4_4ISDU9QI

#include "../headers.p4"
#include "notification.p4"

control Controller(
		inout headers hdr,
		inout standard_metadata_t standard_metadata,
		in NotificationType type
	) {

	apply {
		hdr.cpu.base.setValid();
		hdr.cpu.base.port = (bit<16>) standard_metadata.ingress_port;
		hdr.cpu.base.timestamp = standard_metadata.ingress_global_timestamp;
		hdr.cpu.base.reason = CPUReason.NOTIFICATION;
		hdr.cpu.notification.setValid();
		hdr.cpu.notification.type = type;
		standard_metadata.egress_spec = CONTROLLER_PORT;
	}
}

control IndexController(
		inout headers hdr,
		inout standard_metadata_t standard_metadata,
		in NotificationType type,
		in bit<32> index
	) {
	Controller() controller;

	apply {
		controller.apply(hdr, standard_metadata, type);
		hdr.cpu.notification.index = index;
	}
}


#endif /* end of include guard: UTIL_P4_4ISDU9QI */
