/* -*- P4_16 -*- */
#ifndef INGRESS_P4_Y3HW5QF8
#define INGRESS_P4_Y3HW5QF8

#include "../constants.p4"
#include "../cpu/util.p4"

control EAPIngress(inout headers hdr, inout standard_metadata_t standard_metadata) {
	Controller() controller;

	apply {
		if(hdr.eap.code == EAP_CODE_RESPONSE) {
			controller.apply(hdr, standard_metadata, NotificationType.EAP);
			return;
		}
	}
}

control EAPOLIngress(inout headers hdr, inout standard_metadata_t standard_metadata) {
	Controller() controller;

	EAPIngress() eap;

	apply {
		if(hdr.eapol.type == EAPOL_TYPE_START) {
			controller.apply(hdr, standard_metadata, NotificationType.EAP);
			return;
		} else if(hdr.eapol.type == EAPOL_TYPE_LOGOFF) {
			controller.apply(hdr, standard_metadata, NotificationType.EAP);
			return;
		} else if(hdr.eapol.type == EAPOL_TYPE_PACKET) {
			eap.apply(hdr, standard_metadata);
		}
	}
}

#endif /* end of include guard: INGRESS_P4_Y3HW5QF8 */
