/* -*- P4_16 -*- */
#ifndef INGRESS_P4_2RKP3AM4
#define INGRESS_P4_2RKP3AM4

#include "../macsec/validate.p4"
#include "../macsec/protect.p4"
#include "../eap/ingress.p4"
#include "../cpu/util.p4"

control L2Learn(
		inout headers hdr,
		inout metadata meta,
		inout standard_metadata_t standard_metadata
	) {
	Controller() controller;

	bool refresh = false;
	bool known_source = false;
	bool ignore = false;

	action src_known(egressSpec_t port, bit<48> refresh_time) {
		meta.user_metadata.src_mac_table_port = port;
		// TODO refresh = standard_metadata.ingress_global_timestamp > refresh_time;
		known_source = true;
	}

	action ignore_source() {
		//do nothing
		known_source = true;
		ignore = true;
	}

	table mac_src {
		key = {
			hdr.ethernet.srcAddr: exact;
		}
		actions = {
			src_known;
			ignore_source;
			NoAction;
		}
		size = 1024;
		default_action = NoAction();
	}

	apply {
		//learn mac sources
		mac_src.apply();
		if(known_source) {
			if(ignore) {
				return;
			}
			//send controller a message that the l2 entry is still active
			if(refresh) {
				controller.apply(hdr, standard_metadata, NotificationType.REFRESH_L2_ENTRY);
				return;
			}

			// notify controller if the MAC has changed the port.
			if(meta.user_metadata.src_mac_table_port != standard_metadata.ingress_port) {
				controller.apply(hdr, standard_metadata, NotificationType.CHANGED_L2_ENTRY);
				return;
			}
		} else {
			controller.apply(hdr, standard_metadata, NotificationType.SRC_MAC_UNKNOWN);
			return;
		}
	}
}
control L2Forward(
		inout headers hdr,
		inout metadata meta,
		inout standard_metadata_t standard_metadata
	) {

	Controller() controller;

	bool notify_flood = false;

	action forward(egressSpec_t port) {
		standard_metadata.egress_spec = port;
	}

	action flood() {
		notify_flood = true;
	}

	table mac_dst {
		key = {
			hdr.ethernet.dstAddr: exact;
		}
		actions = {
			forward;
			flood;
		}
		size = 1024;
		default_action = flood();
	}

	apply {
		mac_dst.apply();

		if(notify_flood) {
			controller.apply(hdr, standard_metadata, NotificationType.DST_MAC_UNKNOWN);
			return;
		}

		if(standard_metadata.egress_spec == 0x1FF) {
			mark_to_drop(standard_metadata);
		}

		if(standard_metadata.egress_spec != CONTROLLER_PORT &&
			standard_metadata.egress_spec == standard_metadata.ingress_port) {
			mark_to_drop(standard_metadata);
		}
	}
}

control EthernetIngress(
		inout headers hdr,
		inout metadata meta,
		inout standard_metadata_t standard_metadata
	) {

	Controller() controller;

	Ipv4Ingress() ipv4;
	MacsecValidate() macsec_validate;
	MacsecProtect() macsec_protect;
	EAPOLIngress() eapol;

	L2Learn() learn;
	L2Forward() forward;

	apply {
		if(hdr.sectag.isValid() || hdr.cpu.config.isValid()) {
			macsec_validate.apply(hdr, meta, standard_metadata);
		}

		//prevent config messages -> only ethernet frames
		if(hdr.ethernet.isValid() && hdr.cpu.base.reason != CPUReason.SEND_DIRECT) {
			if(hdr.ethernet.etherType == TYPE_LLDP) {
				controller.apply(hdr, standard_metadata, NotificationType.LLDP);
				return;
			} else if(hdr.ethernet.etherType == TYPE_BDDP) {
				controller.apply(hdr, standard_metadata, NotificationType.LLDP);
				return;
			} else if(hdr.ethernet.etherType == TYPE_ARP) {
				controller.apply(hdr, standard_metadata, NotificationType.ARP);
				return;
			} else if(hdr.eapol.isValid()) {
				eapol.apply(hdr, standard_metadata);
				return;
			} else if(hdr.ipv4.isValid()) {
				learn.apply(hdr, meta, standard_metadata);
				if(hdr.cpu.notification.isValid()) {
					return;
				}

				ipv4.apply(hdr, meta, standard_metadata);

				forward.apply(hdr, meta, standard_metadata);
				if(hdr.cpu.notification.isValid()) {
					return;
				}
			}
		}

		macsec_protect.apply(hdr, meta, standard_metadata);
	}
}

#endif /* end of include guard: INGRESS_P4_2RKP3AM4 */
