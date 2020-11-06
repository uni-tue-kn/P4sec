/* -*- P4_16 -*- */
#ifndef CONSTANTS_P4_YOGGKVSI
#define CONSTANTS_P4_YOGGKVSI

#define CONTROLLER_PORT 16

#include "cpu/constants.p4"
#include "macsec/constants.p4"

// Mac types
const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_ARP = 0x806;
const bit<16> TYPE_LLDP = 0x88cc;
const bit<16> TYPE_MACSEC = 0x88e5;
const bit<16> TYPE_BDDP = 0x8999;
const bit<16> TYPE_EAP = 0x888e;

// IP types
const bit<8>  PROTOCOL_ESP = 0x32;

#endif /* end of include guard: CONSTANTS_P4_YOGGKVSI */
