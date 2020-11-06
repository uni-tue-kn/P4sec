/* -*- P4_16 -*- */
#ifndef EXTERNS_P4_VZCRTVT5
#define EXTERNS_P4_VZCRTVT5

extern ExternCrypt {
	ExternCrypt();
	void protect(in bit<128> SAK,
				in bit<64> SCI,
				in bit<32> PN,
				in bit<48> src_addr,
				in bit<48> dst_addr,
				in bit<128> sectag,
				in bit<16> ethertype,
				in bit<8> prepend_ipv4_hdr,
				in bit<160> ipv4_hdr);
	void validate(in bit<128> SAK,
				in bit<64> SCI,
				in bit<32> PN,
				in bit<48> src_addr,
				in bit<48> dst_addr,
				in bit<128> sectag,
				out bit<8> valid,
				out bit<16> ethertype);
}

ExternCrypt() crypt;

#endif /* end of include guard: EXTERNS_P4_VZCRTVT5 */
