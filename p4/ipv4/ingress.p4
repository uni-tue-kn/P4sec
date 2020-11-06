/* -*- P4_16 -*- */
#ifndef INGRESS_P4_WI1CDD46
#define INGRESS_P4_WI1CDD46

#include "../ipsec/ingress.p4"

control Ipv4Ingress(
			inout headers hdr,
			inout metadata meta,
			inout standard_metadata_t standard_metadata
		){

	IpsecIngress() ipsec;

	action do_forward(macAddr_t dstAddr, egressSpec_t port) {
		standard_metadata.egress_spec = port;
		hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
		hdr.ethernet.dstAddr = dstAddr;
		hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
	}

	table forward {
		key = {
			hdr.ipv4.dstAddr: lpm;
			hdr.ethernet.dstAddr: exact;
		}
		actions = {
			do_forward;
			NoAction;
		}
		default_action = NoAction();
	}

	apply {
		ipsec.apply(hdr, meta, standard_metadata);
		if(forward.apply().hit) {
			recirculate({ meta.intrinsic_metadata, standard_metadata, meta.user_metadata });
			exit;
		}
	}
};

#endif /* end of include guard: INGRESS_P4_WI1CDD46 */
