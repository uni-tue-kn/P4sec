/* -*- P4_16 -*- */
#ifndef EGRESS_P4_ID124FJE
#define EGRESS_P4_ID124FJE

#include "externs.p4"
#include "constants.p4"
#include "../cpu/config.p4"
#include "../cpu/util.p4"
#include "key-state.p4"

control MacsecProtect(
		inout headers hdr,
		inout metadata meta,
		inout standard_metadata_t standard_metadata
	) {
	IndexController() controller;

	register<KeyState>(MACSEC_MAX_CONNECTIONS) key_states;
	register<bit<32>>(MACSEC_MAX_CONNECTIONS) packet_counters;

	register<bit<32>>(MACSEC_MAX_CONNECTIONS) soft_packet_limits;
	register<bit<32>>(MACSEC_MAX_CONNECTIONS) hard_packet_limits;

	bit<128> SAK1 = 0;
	bit<128> SAK2 = 0;
	bit<48>  SYSTEM_ID = 0;
	bit<32>  REGISTER_INDEX = 0;

	action protect_packet(
			bit<128> key1,
			bit<128> key2,
			bit<48> system_id,
			bit<32> register_index
		) {
		SAK1 = key1;
		SAK2 = key2;
		SYSTEM_ID = system_id;
		REGISTER_INDEX = register_index;
	}

	table targets {
		key = {
			standard_metadata.egress_spec: exact;
		}
		actions = {
			protect_packet;
			NoAction;
		}
		size = MACSEC_MAX_CONNECTIONS;
		default_action = NoAction;
	}

	apply {

		// receive config message
		if(hdr.cpu.config.isValid()) {
			if(hdr.cpu.config.type == ConfigType.MACSEC_SET_SOFT_PACKET_LIMIT) {
				soft_packet_limits.write(hdr.cpu.config.index, hdr.cpu.config.value);
			} else if(hdr.cpu.config.type == ConfigType.MACSEC_SET_HARD_PACKET_LIMIT) {
				hard_packet_limits.write(hdr.cpu.config.index, hdr.cpu.config.value);
			}
			return;
		}

		if(hdr.ethernet.etherType != TYPE_BDDP && targets.apply().hit){
			bit<32> PN;
			bit<128> SAK;

			//get the PN from the corresponding counter
			packet_counters.read(PN, REGISTER_INDEX);
			packet_counters.write(REGISTER_INDEX, PN + 1);

			bit<32> soft_packet_limit;
			soft_packet_limits.read(soft_packet_limit, REGISTER_INDEX);

			bit<32> hard_packet_limit;
			hard_packet_limits.read(hard_packet_limit, REGISTER_INDEX);

			KeyState key_state;
			key_states.read(key_state, REGISTER_INDEX);

			if(PN == soft_packet_limit) {
				controller.apply(hdr, standard_metadata,
						NotificationType.MACSEC_SOFT_PACKET_LIMIT,
						REGISTER_INDEX);
				return;
			} else if(PN > soft_packet_limit) {
				PN = PN - 1;
			}

			if(PN == hard_packet_limit) {
				//reset counter
				controller.apply(hdr, standard_metadata,
						NotificationType.MACSEC_HARD_PACKET_LIMIT,
						REGISTER_INDEX);
				return;
			} else if(PN > hard_packet_limit) {
				@atomic {
					packet_counters.write(REGISTER_INDEX, 0);
					key_states.write(REGISTER_INDEX, key_state == KeyState.KEY1 ?
							KeyState.KEY2 : KeyState.KEY1);
				}
			}

			SAK = key_state == KeyState.KEY1 ? SAK1 : SAK2;

			//combine the System and Port Id to get the SCI
			bit<64> SCI = SYSTEM_ID ++ (bit<16>) standard_metadata.egress_spec;

			//set the macsec Header fragments to valid
			hdr.sectag.setValid();

			//set the neccesary data for the sectag and the new ethertype
			hdr.sectag.tci_v = 0;
			hdr.sectag.tci_es = 0;
			hdr.sectag.tci_sc = 1;
			hdr.sectag.tci_scb = 0;
			hdr.sectag.tci_e = 1;
			hdr.sectag.tci_c = 1;
			hdr.sectag.an = 0;
			if(hdr.ethernet.etherType == TYPE_ARP) {
				hdr.sectag.sl = 30;
			} else {
				hdr.sectag.sl = 0;
			}
			hdr.sectag.pn = PN;
			hdr.sectag.sci = SCI;
			bit<128> sectag = TYPE_MACSEC
				++ hdr.sectag.tci_v
				++ hdr.sectag.tci_es
				++ hdr.sectag.tci_sc
				++ hdr.sectag.tci_scb
				++ hdr.sectag.tci_e
				++ hdr.sectag.tci_c
				++ hdr.sectag.an
				++ hdr.sectag.sl
				++ hdr.sectag.pn
				++ hdr.sectag.sci;

			bit<8> prepend_ipv4 = 0x46;
			bit<160> ipv4 = 0;
			if (hdr.ipv4.isValid()) {
				prepend_ipv4 = 0x54;
				ipv4 = hdr.ipv4.version ++ hdr.ipv4.ihl ++ hdr.ipv4.diffserv ++ hdr.ipv4.totalLen ++ hdr.ipv4.identification ++ hdr.ipv4.flags ++ hdr.ipv4.fragOffset ++ hdr.ipv4.ttl ++ hdr.ipv4.protocol ++ hdr.ipv4.hdrChecksum ++ hdr.ipv4.srcAddr ++ hdr.ipv4.dstAddr;
				hdr.ipv4.setInvalid();
			}

			crypt.protect(SAK, SCI, PN, hdr.ethernet.srcAddr, hdr.ethernet.dstAddr, sectag, hdr.ethernet.etherType, prepend_ipv4, ipv4);

			hdr.ethernet.etherType = TYPE_MACSEC;

		}
	}
}

#endif /* end of include guard: EGRESS_P4_ID124FJE */
