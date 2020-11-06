/* -*- P4_16 -*- */
#ifndef PARSER_P4_GA7MK3QP
#define PARSER_P4_GA7MK3QP

#include "headers.p4"

parser packetParser(
			packet_in packet,
			out headers hdr,
			inout metadata meta,
			inout standard_metadata_t standard_metadata
		) {

	state start {
		transition select(standard_metadata.ingress_port) {
			CONTROLLER_PORT: parse_cpu;
			default: parse_ethernet;
		}
	}

	state parse_ethernet {
		packet.extract(hdr.ethernet);
		transition select(hdr.ethernet.etherType) {
			TYPE_IPV4: parse_ipv4;
			TYPE_MACSEC: parse_sectag;
			TYPE_EAP: parse_eapol;
			TYPE_LLDP: accept;
			TYPE_BDDP: accept;
			default: accept;
		}
	}

	state parse_ipv4 {
		packet.extract(hdr.ipv4);
		transition select(hdr.ipv4.protocol) {
			PROTOCOL_ESP: parse_esp;
			default: accept;
		}
	}

	state parse_esp {
		packet.extract(hdr.esp);
		transition accept;
	}

	state parse_cpu {
		packet.extract(hdr.cpu.base);
		transition select(hdr.cpu.base.reason) {
			CPUReason.CONFIG: parse_cpu_config;
			CPUReason.NOTIFICATION: parse_cpu_notification;
			default: parse_ethernet;
		}
	}

	state parse_cpu_config {
		packet.extract(hdr.cpu.config);
		transition accept;
	}

	state parse_cpu_notification {
		packet.extract(hdr.cpu.notification);
		transition parse_ethernet;
	}

	state parse_sectag {
		packet.extract(hdr.sectag);
		transition accept;
	}

	state parse_eapol {
		packet.extract(hdr.eapol);
		transition select(hdr.eapol.type) {
			EAPOL_TYPE_PACKET: parse_eap;
			default: accept;
		}
	}

	state parse_eap {
		packet.extract(hdr.eap);
		transition select(hdr.eap.code) {
			EAP_CODE_SUCCESS: accept;
			EAP_CODE_FAILURE: accept;
			EAP_CODE_REQUEST: parse_eap_type;
			EAP_CODE_RESPONSE: parse_eap_type;
		}
	}

	state parse_eap_type {
		packet.extract(hdr.eap_type);
		transition accept;
	}
}

#endif /* end of include guard: PARSER_P4_GA7MK3QP */
