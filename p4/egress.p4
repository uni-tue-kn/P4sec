/* -*- P4_16 -*- */
#ifndef EGRESS_P4_NWPFYT9O
#define EGRESS_P4_NWPFYT9O

#include "ethernet/egress.p4"

control egress(inout headers hdr,
				 inout metadata meta,
				 inout standard_metadata_t standard_metadata) {

	EthernetEgress() ethernet;

	apply {
		if(hdr.cpu.base.isValid()) {
			//directly send to controller
		} else if(hdr.ethernet.isValid()) {
			ethernet.apply(hdr, meta, standard_metadata);
		}
	}
}

#endif /* end of include guard: EGRESS_P4_NWPFYT9O */
