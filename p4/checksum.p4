/* -*- P4_16 -*- */
#ifndef CHECKSUM_P4_A91WDM3Z
#define CHECKSUM_P4_A91WDM3Z

#include <core.p4>
#include <v1model.p4>

control verifyChecksum(inout headers hdr, inout metadata meta) {
	apply {  }
}

control computeChecksum(inout headers  hdr, inout metadata meta) {
	apply {
		update_checksum(
			hdr.ipv4.isValid(),
			{
				hdr.ipv4.version,
				hdr.ipv4.ihl,
				hdr.ipv4.diffserv,
				hdr.ipv4.totalLen,
				hdr.ipv4.identification,
				hdr.ipv4.flags,
				hdr.ipv4.fragOffset,
				hdr.ipv4.ttl,
				hdr.ipv4.protocol,
				hdr.ipv4.srcAddr,
				hdr.ipv4.dstAddr
			},
			hdr.ipv4.hdrChecksum,
			HashAlgorithm.csum16
		);
	}
}

#endif /* end of include guard: CHECKSUM_P4_A91WDM3Z */
