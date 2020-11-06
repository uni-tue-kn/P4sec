/* -*- P4_16 -*- */
#ifndef DEPARSER_P4_BG9ECLTI
#define DEPARSER_P4_BG9ECLTI

control deparser(packet_out packet, in headers hdr) {
	apply {
		packet.emit(hdr.cpu.base);
		packet.emit(hdr.cpu.config);
		packet.emit(hdr.cpu.notification);
		packet.emit(hdr.ethernet);
		packet.emit(hdr.eapol);
		packet.emit(hdr.eap);
		packet.emit(hdr.eap_type);
		packet.emit(hdr.sectag);
		packet.emit(hdr.ipv4);
		packet.emit(hdr.esp);
	}
}

#endif /* end of include guard: DEPARSER_P4_BG9ECLTI */
