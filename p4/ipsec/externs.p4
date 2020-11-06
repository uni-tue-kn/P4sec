/* -*- P4_16 -*- */
#ifndef EXTERNS_P4_R2IFQCGC
#define EXTERNS_P4_R2IFQCGC

extern ipsec_crypt {
	ipsec_crypt();
	void decrypt_aes_ctr(in bit<160> key, in bit<128> key_hmac);
	void encrypt_aes_ctr(in bit<160> key, in bit<128> key_hmac);
}


ipsec_crypt() ipsecCrypt;  // instantiation

#endif /* end of include guard: EXTERNS_P4_R2IFQCGC */
