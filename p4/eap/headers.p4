/* -*- P4_16 -*- */
#ifndef EAP_P4_F3QLZUGV
#define EAP_P4_F3QLZUGV

// types
typedef bit<8>  eap_code_t;
typedef bit<8>  eap_identifier_t;
typedef bit<16> eap_length_t;
typedef bit<8>  eap_type_value_t;
typedef bit<8>  eapol_type_t;
typedef bit<8>  eapol_version_t;

// use constants because enums are causing compile error
const eap_code_t EAP_CODE_REQUEST  = 1;
const eap_code_t EAP_CODE_RESPONSE = 2;
const eap_code_t EAP_CODE_SUCCESS  = 3;
const eap_code_t EAP_CODE_FAILURE  = 4;

const eap_type_value_t EAP_TYPE_IDENTITY           = 1;
const eap_type_value_t EAP_TYPE_NOTIFICATION       = 2;
const eap_type_value_t EAP_TYPE_NAK                = 3;
const eap_type_value_t EAP_TYPE_MD5_CHALLENGE      = 4;

const eapol_type_t EAPOL_TYPE_PACKET = 0;
const eapol_type_t EAPOL_TYPE_START  = 1;
const eapol_type_t EAPOL_TYPE_LOGOFF = 2;
const eapol_type_t EAPOL_TYPE_KEY    = 3;

header eap_type_t {
	eap_type_value_t value;
}

header eap_t {
	eap_code_t       code;
	eap_identifier_t identifier;
	eap_length_t     length;
}

header eapol_t {
	eapol_version_t version;
	eapol_type_t    type;
	eap_length_t    length;
}

#endif /* end of include guard: EAP_P4_F3QLZUGV */
