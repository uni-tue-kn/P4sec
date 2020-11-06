/* -*- P4_16 -*- */
#ifndef HEADERS_P4_LOMSSHTV
#define HEADERS_P4_LOMSSHTV

#include <core.p4>
#include <v1model.p4>

#include "constants.p4"
#include "cpu/header.p4"
#include "eap/headers.p4"

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;


header ethernet_t {
	macAddr_t dstAddr;
	macAddr_t srcAddr;
	bit<16>   etherType;
}

header ipv4_t {
	bit<4>		version;
	bit<4>		ihl;
	bit<8>		diffserv;
	bit<16>		totalLen;
	bit<16>		identification;
	bit<3>		flags;
	bit<13>		fragOffset;
	bit<8>		ttl;
	bit<8>		protocol;
	bit<16>		hdrChecksum;
	ip4Addr_t	srcAddr;
	ip4Addr_t	dstAddr;
}

header sectag_t {
	bit<1>		tci_v;
	bit<1>		tci_es;
	bit<1>		tci_sc;
	bit<1>		tci_scb;
	bit<1>		tci_e;
	bit<1>		tci_c;
	bit<2>		an;
	bit<8>		sl;
	bit<32>		pn;
	bit<64>		sci;
}

struct user_metadata_t {
	bit<48>         src_mac_timeout;
	egressSpec_t    src_mac_table_port;
	bit<8>          switched_mac_src_with_dst;
	bit<8>          flooded;
}

header esp_t {
	bit<32> spi;
	bit<32> sequenceNumber;
}

struct intrinsic_metadata_t {
	bit<48> ingress_global_timestamp;
}

struct esp_metadata_t {
	bit<16> payloadLength;
}

struct metadata {
	@metadata @name("intrinsic_metadata")
	intrinsic_metadata_t 	intrinsic_metadata;
	user_metadata_t	  		user_metadata;
	esp_metadata_t 			esp_meta;
}

struct headers {
	cpu_t         cpu;
	ethernet_t    ethernet;
	eapol_t       eapol;
	eap_t         eap;
	eap_type_t    eap_type;
	sectag_t      sectag;
	ipv4_t        ipv4;
	esp_t         esp;
}

#endif /* end of include guard: HEADERS_P4_LOMSSHTV */
