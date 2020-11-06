/* -*- P4_16 -*- */
#ifndef INGRESS_P4_ELNTYARW
#define INGRESS_P4_ELNTYARW

#include "./headers.p4"
#include "./ipv4/ingress.p4"
#include "./ethernet/ingress.p4"
#include "port-authorizer.p4"

control ingress(
		inout headers hdr,
		inout metadata meta,
		inout standard_metadata_t standard_metadata
	) {

	EthernetIngress() ethernet;
	PortAuthorizer() in_port_authorizer;
	PortAuthorizer() out_port_authorizer;
	bool authorized;

	apply {
		// if packet comes from the controller
		if(hdr.cpu.base.isValid()) {
			hdr.cpu.base.setInvalid();

			//handle packets which are directly send out from the controller
			if(hdr.cpu.base.reason == CPUReason.SEND_DIRECT) {
				standard_metadata.egress_spec = (bit<9>) hdr.cpu.base.port;
				//will be caught at the ethernet level
			} else if(hdr.cpu.base.reason == CPUReason.SEND) {
				standard_metadata.ingress_port = (bit<9>) hdr.cpu.base.port;
				//goes through the full pipeline
			} else if(hdr.cpu.config.isValid()) {
				mark_to_drop(standard_metadata);
				//goes through the full pipeline
			} else if(hdr.cpu.notification.isValid()) {
				//handle recirculated notification from egress pipeline
				standard_metadata.egress_spec = CONTROLLER_PORT;
				return;
			}
		} else {
			hdr.cpu.base.reason = CPUReason.SEND;
		}

		if(hdr.ethernet.isValid() && (hdr.ethernet.etherType == TYPE_EAP
			|| hdr.ethernet.etherType == TYPE_LLDP
			|| hdr.ethernet.etherType == TYPE_BDDP)
			|| standard_metadata.ingress_port == CONTROLLER_PORT
		) {
			authorized = true;
		} else {
			in_port_authorizer.apply(
				standard_metadata.ingress_port,
				hdr.ethernet.srcAddr,
				authorized
			);
		}

		if(authorized && hdr.ethernet.isValid() || hdr.cpu.config.isValid()) {
			ethernet.apply(hdr, meta, standard_metadata);
			if(hdr.cpu.notification.isValid()) {
				return;
			}
		}

		if(hdr.ethernet.isValid() && (hdr.ethernet.etherType == TYPE_EAP
			|| hdr.ethernet.etherType == TYPE_LLDP
			|| hdr.ethernet.etherType == TYPE_BDDP)
		) {
			authorized = true;
		} else {
			out_port_authorizer.apply(
				standard_metadata.egress_spec,
				hdr.ethernet.dstAddr,
				authorized
			);
		}

		if(!authorized) {
			mark_to_drop(standard_metadata);
		}
	}
}

#endif /* end of include guard: INGRESS_P4_ELNTYARW */
