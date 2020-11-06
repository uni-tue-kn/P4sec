/* -*- P$_16 -*- */

#include "parser.p4"
#include "checksum.p4"
#include "ingress.p4"
#include "egress.p4"
#include "deparser.p4"

V1Switch(
	packetParser(),
	verifyChecksum(),
	ingress(),
	egress(),
	computeChecksum(),
	deparser()
) main;
