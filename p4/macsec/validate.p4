/* -*- P4_16 -*- */
#ifndef VALIDATE_P4_W2R6NAKY
#define VALIDATE_P4_W2R6NAKY

#include "externs.p4"
#include "constants.p4"
#include "key-state.p4"

control MacsecValidate(
		inout headers hdr,
		inout metadata meta,
		inout standard_metadata_t standard_metadata
	) {

	register<KeyState>(MACSEC_MAX_CONNECTIONS) key_states;
	register<bit<32>>(MACSEC_MAX_CONNECTIONS) soft_packet_limits;
	register<bit<32>>(MACSEC_MAX_CONNECTIONS) hard_packet_limits;

	bit<128> SAK1 = 0;
	bit<128> SAK2 = 0;
	bit<32> REGISTER_INDEX = 0;

	action validate_packet(bit<128> key1, bit<128> key2, bit<32> register_index) {
		SAK1 = key1;
		SAK2 = key2;
		REGISTER_INDEX = register_index;
	}

	table sources {
		key = {
			standard_metadata.ingress_port: exact;
		}
		actions = {
			NoAction;
			validate_packet;
		}
	}

	apply {
		if(hdr.cpu.config.isValid()) {
			if(hdr.cpu.config.type == ConfigType.MACSEC_SET_SOFT_PACKET_LIMIT) {
				soft_packet_limits.write(hdr.cpu.config.index, hdr.cpu.config.value);
			} else if(hdr.cpu.config.type == ConfigType.MACSEC_SET_HARD_PACKET_LIMIT) {
				hard_packet_limits.write(hdr.cpu.config.index, hdr.cpu.config.value);
			}
			return;
		} else if(sources.apply().hit) {
			// key found, decrypt the packet
			bit<64> SCI = hdr.sectag.sci;
			bit<32> PN = hdr.sectag.pn;

			bit<32> soft_packet_limit;
			soft_packet_limits.read(soft_packet_limit, REGISTER_INDEX);

			bit<32> hard_packet_limit;
			hard_packet_limits.read(hard_packet_limit, REGISTER_INDEX);

			KeyState key_state;
			key_states.read(key_state, REGISTER_INDEX);

			bit<128> SAK;
			if(key_state == KeyState.KEY1) {
				if(PN < soft_packet_limit) {
					SAK = SAK1;
				} else {
					SAK = SAK2;
				}
			} else {
				if(PN < soft_packet_limit) {
					SAK = SAK2;
				} else {
					SAK = SAK1;
				}
			}

			if(PN == soft_packet_limit) {
				key_states.write(REGISTER_INDEX, key_state == KeyState.KEY1 ?
						KeyState.KEY2 : KeyState.KEY1);
			}

			bit<128> sectag = TYPE_MACSEC ++ hdr.sectag.tci_v
						++ hdr.sectag.tci_es ++ hdr.sectag.tci_sc
						++ hdr.sectag.tci_scb ++ hdr.sectag.tci_e
						++ hdr.sectag.tci_c ++ hdr.sectag.an
						++ hdr.sectag.sl ++ hdr.sectag.pn
						++ hdr.sectag.sci;

			bit<48> src_addr = hdr.ethernet.srcAddr;
			bit<48> dst_addr = hdr.ethernet.dstAddr;

			// result flags
			bit<8> valid;
			bit<16> ethertype;

			// decrypt message
			crypt.validate(SAK, SCI, PN, src_addr, dst_addr, sectag, valid, ethertype);

			// create decrypted message
			hdr.ethernet.etherType = ethertype;
			hdr.sectag.setInvalid();

			// decrypted packets must go through the parser again.
			recirculate({ meta.intrinsic_metadata, standard_metadata, meta.user_metadata });
			exit;
		}
	}
}

#endif /* end of include guard: VALIDATE_P4_W2R6NAKY */
