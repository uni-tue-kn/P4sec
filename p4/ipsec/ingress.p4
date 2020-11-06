/* -*- P4_16 -*- */
#ifndef INGRESS_P4_5LBW3HEK
#define INGRESS_P4_5LBW3HEK

#include "core.p4"
#include "../constants.p4"
#include "../headers.p4"
#include "../cpu/util.p4"

extern ipsec_crypt {
	ipsec_crypt();
	void decrypt_aes_ctr(inout ipv4_t ipv4, inout esp_t esp, inout standard_metadata_t standard_metadata, in bit<160> key, in bit<128> key_hmac);
	void encrypt_aes_ctr(inout ipv4_t ipv4, inout esp_t esp, in bit<160> key, in bit<128> key_hmac);
}

ipsec_crypt() ipsecCrypt;  // instantiation

control IpsecIngress(
			inout headers hdr,
			inout metadata meta,
			inout standard_metadata_t standard_metadata
		) {

	Controller() controller;
	register<bit<32>>(1024) counters;

	bool notify_soft = false;
	bool notify_hard = false;
	bool do_drop = false;
	bit<32> current_register = 0;

	action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
		standard_metadata.egress_spec = port;
		hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
		hdr.ethernet.dstAddr = dstAddr;
		hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
	}

	action esp_decrypt(bit<160> key, bit<128> key_hmac, bit<32> register_index) {
		ipsecCrypt.decrypt_aes_ctr(hdr.ipv4, hdr.esp, standard_metadata, key, key_hmac);
		hdr.esp.setInvalid();

		bit<32> tmp;
		counters.read(tmp, register_index);
		counters.write(register_index, tmp + 1);
	}

	action esp_encrypt(
			bit<160> key,
			bit<128> key_hmac,
			bit<32> spi,
			ip4Addr_t src,
			ip4Addr_t dst,
			bit<32> register_index,
			bit<32> soft_packet_limit,
			bit<32> hard_packet_limit
		) {

		bit<32> tmp;
		counters.read(tmp, register_index);

		hdr.esp.setValid();
		hdr.esp.spi = spi;
		hdr.esp.sequenceNumber = tmp + 1;
		ipsecCrypt.encrypt_aes_ctr(hdr.ipv4, hdr.esp, key, key_hmac); //encrypts and sets ipv4 header length
		//hdr.ipv4.totalLen = meta.esp_meta.payloadLength + 28;
		hdr.ipv4.identification = 1;
		hdr.ipv4.flags = 2;
		hdr.ipv4.fragOffset = 0;
		hdr.ipv4.ttl = 64;
		hdr.ipv4.protocol = PROTOCOL_ESP;
		hdr.ipv4.srcAddr = src;
		hdr.ipv4.dstAddr = dst;

		counters.write(register_index, tmp + 1);

		
		notify_soft = soft_packet_limit == tmp;
		notify_hard = hard_packet_limit == tmp;
		do_drop = tmp > hard_packet_limit;
		current_register = register_index;
	}

	table decrypt {
		key = {
			hdr.ipv4.srcAddr: exact;
			hdr.ipv4.dstAddr: exact;
			hdr.esp.spi:	  exact;
		}
		actions = {
			NoAction;
			esp_decrypt;
		}
		size = 1024;
		default_action = NoAction();
	}

	table encrypt {
		key = {
			hdr.ipv4.dstAddr: lpm;
		}
		actions = {
			NoAction;
			esp_encrypt;
		}
		size = 1024;
		default_action = NoAction();
	}

	apply {
		if(hdr.cpu.config.isValid() && hdr.cpu.config.type == ConfigType.IPSEC_RESET_COUNTER) {
			counters.write(hdr.cpu.config.index, 0);
			exit;
		}

		if (hdr.esp.isValid()) { //message from client
			//decrypt the package
			decrypt.apply();
		} else if(hdr.ipv4.isValid()) {
			//try to encrypt
			//when no match is found -> do not encrypt
			encrypt.apply();
		}

		if(do_drop) {
			mark_to_drop(standard_metadata);
			exit;
		} else if(notify_soft) {
			controller.apply(hdr, standard_metadata, NotificationType.IPSEC_SOFT_PACKET_LIMIT);
			exit;
		} else if(notify_hard) {
			controller.apply(hdr, standard_metadata, NotificationType.IPSEC_HARD_PACKET_LIMIT);
			exit;
		}
	}
}

#endif /* end of include guard: INGRESS_P4_5LBW3HEK */
