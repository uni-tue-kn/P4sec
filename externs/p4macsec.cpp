#include "./p4macsec.hpp"

#include <bm/bm_sim/parser.h>
#include <bm/bm_sim/tables.h>
#include <bm/bm_sim/logger.h>

#include <openssl/aes.h>
#include <openssl/evp.h>
#include <openssl/rand.h>

#include <assert.h>

using namespace bm;
using bm::p4macsec::ExternCrypt;


void ExternCrypt::init() { }

namespace std {
std::ostream& operator<<(std::ostream& out, const std::vector<unsigned char>& data) {
	for(const auto& x : data) {
		out << std::hex << std::setfill('0') << std::setw(2) << (int) x;
	}
	return out;
}
template<std::size_t N>
std::ostream& operator<<(std::ostream& out, const std::array<unsigned char, N>& data) {
	for(const auto& x : data) {
		out << std::hex << std::setfill('0') << std::setw(2) << (int) x;
	}
	return out;
}
}

using sak_t = std::array<unsigned char, SAK_SIZE>;

template<typename T>
std::array<unsigned char, sizeof(T)> get(const Data& data) {
	std::array<unsigned char, sizeof(T)> result { };
	const auto data_string = data.get_string();

	assert(data_string.size() <= sizeof(T));

	std::copy(data_string.begin(), data_string.end(), result.end() - data_string.size());

	return result;
}


void ExternCrypt::protect(
		const Data &in_sak,
		const Data &in_sci,
		const Data &in_pn,
		const Data &in_src_addr,
		const Data &in_dst_addr,
		const Data &in_sectag,
		const Data &in_ethertype,
		const Data &in_prepend_ipv4_hdr,
		const Data &in_ipv4_hdr
	) {
	std::cout << "[p4sec] begin protect" << std::endl;

	auto secure_association_key = get<sak_t>(in_sak);
	std::cout << "[p4sec] secure_association_key: " << secure_association_key << std::endl;

	auto secure_channel_identifier = get<sci_t>(in_sci);
	std::cout << "[p4sec] secure_channel_identifier: " << secure_channel_identifier
		<< std::endl;

	auto packet_number = get<pn_t>(in_pn);
	std::cout << "[p4sec] packet_number: " << packet_number << std::endl;

	auto source_mac_address = get<mac_t>(in_src_addr);
	std::cout << "[p4sec] source_mac_address: " << source_mac_address << std::endl;

	auto destionation_mac_address = get<mac_t>(in_dst_addr);
	std::cout << "[p4sec] destionation_mac_address: " << destionation_mac_address << std::endl;

	auto security_tag = get<sectag_t>(in_sectag);
	std::cout << "[p4sec] security_tag: " << security_tag << std::endl;

	auto ethertype = get<ethertype_t>(in_ethertype);
	std::cout << "[p4sec] EtherType: " << ethertype << std::endl;

	auto prepend_ipv4 = false;
	// must pass byte to external function
	// use 0x54 T as true
	// use 0x46 F as false
	//cout << "[p4sec] prepend IPv4 Header ? " << in_prepend_ipv4_hdr.get_string() << std::endl;
	if (in_prepend_ipv4_hdr.get_string().compare("T") == 0) {
		prepend_ipv4 = true;
		//cout << "[p4sec] prepend IPv4 Header" << std::endl;
	}
	else{
		//cout << "[p4sec] do not prepend IPv4 Header" << std::endl;
	}

	ipv4_hdr_t ipv4_hdr { };
	if (prepend_ipv4) {
		ipv4_hdr = get<ipv4_hdr_t>(in_ipv4_hdr);
		//cout << "[p4sec] IPv4 Header" << std::endl;
		//hexdump((char*)&ipv4_hdr[0], ipv4_hdr.size());
	}


	std::vector<unsigned char> raw_packet_data;
	// calculate secure data length
	int raw_packet_size = get_packet().get_data_size() + ETHERTYPE_SIZE;
	if (prepend_ipv4) {
		raw_packet_size += IPV4_HDR_SIZE;
	}
	raw_packet_data.resize(raw_packet_size, '\0');
	// copy EtherType
	auto copy_pointer = raw_packet_data.begin();
	std::copy(ethertype.data(), ethertype.data() + ETHERTYPE_SIZE, copy_pointer);
	copy_pointer += ETHERTYPE_SIZE;
	// copy IPv4 Header if necessary
	if (prepend_ipv4) {
		std::copy(ipv4_hdr.data(), ipv4_hdr.data() + IPV4_HDR_SIZE, copy_pointer);
		copy_pointer += IPV4_HDR_SIZE;
	}
	// copy payload
	std::copy(get_packet().data(), get_packet().data() + get_packet().get_data_size(),
			copy_pointer);

	std::vector<unsigned char> secure_data;
	icv_t integrity_check_value { };

	this->protection_function(secure_association_key, secure_channel_identifier,
			packet_number, destionation_mac_address, source_mac_address,
			security_tag, raw_packet_data, secure_data, integrity_check_value);

	assert(secure_data.size() == raw_packet_data.size());

	std::cout << "[p4sec] Encrypted Data: " << secure_data << std::endl;
	std::cout << "[p4sec] ICV: " << integrity_check_value << std::endl;

	//replace payload
	//first, remove all the data
	get_packet().remove(get_packet().get_data_size());
	//make room for the ciphertext and write the ciphertext in it
	char *payload_start = get_packet().prepend(
		(unsigned long int) (secure_data.size() + integrity_check_value.size()));
	for (uint i = 0; i < secure_data.size(); i++) {
		payload_start[i] = secure_data[i];
	}
	for (uint i = 0; i < integrity_check_value.size(); i++) {
		payload_start[i + secure_data.size()] = integrity_check_value[i];
	}
}

void ExternCrypt::validate(
		const Data &in_sak,
		const Data &in_sci,
		const Data &in_pn,
		const Data &in_src_addr,
		const Data &in_dst_addr,
		const Data &in_sectag,
		Data &out_valid,
		Data &out_ethertype
	) {

	std::cout << "[p4sec] begin validate" << std::endl;

	auto secure_association_key = get<sak_t>(in_sak);
	std::cout << "[p4sec] secure_association_key: " << secure_association_key << std::endl;

	auto secure_channel_identifier = get<sci_t>(in_sci);
	std::cout << "[p4sec] secure_channel_identifier: " << secure_channel_identifier << std::endl;

	auto packet_number = get<pn_t>(in_pn);
	std::cout << "[p4sec] packet_number: " << packet_number << std::endl;

	auto source_mac_address = get<mac_t>(in_src_addr);
	std::cout << "[p4sec] source_mac_address: " << source_mac_address << std::endl;

	auto destionation_mac_address = get<mac_t>(in_dst_addr);
	std::cout << "[p4sec] destionation_mac_address: " << destionation_mac_address << std::endl;

	auto security_tag = get<sectag_t>(in_sectag);
	std::cout << "[p4sec] security_tag: " << security_tag << std::endl;

	data_t secure_data {
		get_packet().data(),
		get_packet().data() + get_packet().get_data_size() - sizeof(icv_t)
	};
	// copy secure data
	//std::copy(get_packet().data(),
	//		get_packet().data() + get_packet().get_data_size() - ICV_SIZE,
	//		secure_data.begin());

	std::cout << "[p4sec] encrypted data: " << secure_data << std::endl;

	// calculate secure data length
	//auto secure_data_size = get_packet().get_data_size() - ICV_SIZE;
	//secure_data.resize(secure_data_size, '\0');

	icv_t integrity_check_value;
	//integrity_check_value.resize(ICV_SIZE, '\0');

	// copy ICV
	std::copy(get_packet().data() + get_packet().get_data_size() - ICV_SIZE,
			get_packet().data() + get_packet().get_data_size(),
			integrity_check_value.begin());

	std::cout << "[p4sec] integrity_check_value: " << integrity_check_value << std::endl;

	data_t user_data { };
	//std::vector<unsigned char> user_data;
	//user_data.reserve(secure_data_size);

	auto valid = validation_function(secure_association_key, secure_channel_identifier,
			packet_number, destionation_mac_address, source_mac_address,
			security_tag, secure_data, integrity_check_value, user_data);

	assert(user_data.size() == secure_data.size());


	std::cout << "[p4sec] decrypted data: " << user_data << std::endl;
	//hexdump((char*)&user_data[0], user_data.size());

	//cout << "[p4sec] Ethertype" << std::endl;
	//hexdump((char*)&user_data[0], ETHERTYPE_SIZE);

	//cout << "[p4sec] decrypted payload" << std::endl;
	//hexdump((char*)&user_data[ETHERTYPE_SIZE], user_data.size() - ETHERTYPE_SIZE);

	//replace payload
	//first, remove all the data
	get_packet().remove(get_packet().get_data_size());
	//make room for the ciphertext and write the ciphertext in it
	char *payload_start = get_packet().prepend((unsigned long int) user_data.size() - ETHERTYPE_SIZE);
	for (uint i = 0; i < user_data.size() - ETHERTYPE_SIZE; i++) {
		payload_start[i] = user_data[i + ETHERTYPE_SIZE];
	}

	//copy ethertype from encrypted packet
	std::stringstream ss_ethertype;
	for(uint i=0; i<ETHERTYPE_SIZE; ++i) {
		ss_ethertype << std::setfill('0') << std::setw(2) << std::hex << (int)user_data[i];
	}
	auto ethertype_hexstr = ss_ethertype.str();

	out_ethertype.set(ethertype_hexstr);
	out_valid.set(valid);
}

std::vector<unsigned char> ExternCrypt::get_char_vector(std::string str, unsigned int size) {
	//string fitted_str = fit_string(str, size);
	std::vector<unsigned char> vec(size,'\0');
	if (str.length() > size) {
	  //cout << "[p4sec] given string was too long" << std::endl;
	  str.resize(size);
	}
	vec.insert(vec.cend()-size, str.begin(), str.end());

	return vec;
}

void ExternCrypt::protection_function(
		const sak_t& secure_association_key,
		const sci_t& secure_channel_identifier,
		const pn_t& packet_number,
		const mac_t& destionation_mac_address,
		const mac_t& source_mac_address,
		const sectag_t& security_tag,
		const std::vector<unsigned char>& user_data,
		std::vector<unsigned char>& out_secure_data,
		icv_t& out_integrity_check_value
	) {
	//hier evtl assertions fuer die Laenge der Parameter
	//
	//std::cout << "[p4sec] secure_association_key size " << secure_association_key.size() <<  std::endl;
	//hexdump((char*)&secure_association_key[0], secure_association_key.size());

	//std::cout << "[p4sec] secure_channel_identifier size " << secure_channel_identifier.size() <<  std::endl;
	//hexdump((char*)&secure_channel_identifier[0], secure_channel_identifier.size());

	//std::cout << "[p4sec] packet_number size " << packet_number.size() <<  std::endl;
	//hexdump((char*)&packet_number[0], packet_number.size());

	//std::cout << "[p4sec] destionation_mac_address size " << destionation_mac_address.size() <<  std::endl;
	//hexdump((char*)&destionation_mac_address[0], destionation_mac_address.size());

	//std::cout << "[p4sec] source_mac_address size " << source_mac_address.size() <<  std::endl;
	//hexdump((char*)&source_mac_address[0], source_mac_address.size());

	//std::cout << "[p4sec] security_tag size " << security_tag.size() <<  std::endl;
	//hexdump((char*)&security_tag[0], security_tag.size());

	//std::cout << "[p4sec] user_data size " << user_data.size() <<  std::endl;
	//hexdump((char*)&user_data[0], user_data.size());


	//terms K, IV, A, P, C, T used in section 2.1 of the GCM specification ( GCM ) as submitted to NIST

	//std::cout << "[p4sec] K size " << K.size() <<  std::endl;
	//hexdump((char*)&K[0], K.size());

	//12 byte IV
	std::array<unsigned char, sizeof(sci_t) + sizeof(pn_t)> IV;
	//The 64 most significant bits of the 96-bit IV are the octets of the SCI, encoded as a binary number (9.1).
	std::copy(secure_channel_identifier.begin(), secure_channel_identifier.end(),
			IV.begin());
	//IV.insert( IV.cend(), secure_channel_identifier.cbegin(), secure_channel_identifier.cend() );
	//The 32 least significant bits of the 96-bit IV are the octets of the PN, encoded as a binary number
	std::copy(packet_number.begin(), packet_number.end(), IV.begin() + sizeof(sci_t));
	//IV.insert( IV.cend(), packet_number.cbegin(), packet_number.cend() );

	//std::cout << "[p4sec] IV size " << IV.size() <<  std::endl;
	//hexdump((char*)&IV[0], IV.size());


	//A is the Destination MAC Address, Source MAC Address, and the octets of the SecTAG concatenated in that order
	std::array<unsigned char, 2 * sizeof(mac_t) + sizeof(sectag_t)> A;
	std::copy(destionation_mac_address.begin(), destionation_mac_address.end(), A.begin());
	std::copy(source_mac_address.begin(), source_mac_address.end(), A.begin() + sizeof(mac_t));
	std::copy(security_tag.begin(), security_tag.end(), A.begin() + 2 * sizeof(mac_t));
	//A.insert( A.cend(), destionation_mac_address.cbegin(), destionation_mac_address.cend() );
	//A.insert( A.cend(), source_mac_address.cbegin(), source_mac_address.cend() );
	//A.insert( A.cend(), security_tag.cbegin(), security_tag.cend() );

	//P is the octets of the User Data
	std::vector<unsigned char> P;
	P.insert(P.begin(), user_data.begin(), user_data.end());


	out_secure_data.resize(P.size(), '\0');
	//out_integrity_check_value.resize(16, '\0');


	//std::cout << "[p4sec] out_secure_data size " << out_secure_data.size() <<  std::endl;
	//hexdump((char*)&out_secure_data[0], out_secure_data.size());

	//std::cout << "[p4sec] out_integrity_check_value size " << out_integrity_check_value.size() <<  std::endl;
	//hexdump((char*)&out_integrity_check_value[0], out_integrity_check_value.size());

	//std::cout << "[p4sec] initilalizing encryption" << std::endl;
	int actual_size=0, final_size=0;
	EVP_CIPHER_CTX* e_ctx = EVP_CIPHER_CTX_new();
	EVP_EncryptInit(e_ctx, EVP_aes_128_gcm(), secure_association_key.data(), IV.data());

	// Set the IV length, kann man machen, muss man aber nicht da standard 12
	//  EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, 12, NULL);
	//https://www.openssl.org/docs/man1.0.2/crypto/EVP_get_cipherbynid.html#GCM_Mode
	//To specify any additional authenticated data (AAD) a call to EVP_CipherUpdate(), EVP_EncryptUpdate() or EVP_DecryptUpdate() should be made with the output parameter out set to NULL
	EVP_EncryptUpdate(e_ctx, NULL, &actual_size, A.data(), A.size());
	EVP_EncryptUpdate(e_ctx, out_secure_data.data(), &actual_size, P.data(), P.size() );
	EVP_EncryptFinal(e_ctx, &out_secure_data[actual_size], &final_size);
	EVP_CIPHER_CTX_ctrl(e_ctx, EVP_CTRL_GCM_GET_TAG, 16, out_integrity_check_value.data());
	EVP_CIPHER_CTX_free(e_ctx);
}

int ExternCrypt::validation_function(
		const sak_t& secure_association_key,
		const sci_t& secure_channel_identifier,
		const pn_t& packet_number,
		const mac_t& destionation_mac_address,
		const mac_t& source_mac_address,
		const sectag_t& security_tag,
		const data_t& secure_data,
		icv_t integrity_check_value,
		data_t& out_user_data
	) {
	//std::cout << "[p4sec] secure_association_key size " << secure_association_key.size() <<  std::endl;
	//hexdump((char*)&secure_association_key[0], secure_association_key.size());

	//std::cout << "[p4sec] secure_channel_identifier size " << secure_channel_identifier.size() <<  std::endl;
	//hexdump((char*)&secure_channel_identifier[0], secure_channel_identifier.size());

	//std::cout << "[p4sec] packet_number size " << packet_number.size() <<  std::endl;
	//hexdump((char*)&packet_number[0], packet_number.size());

	//std::cout << "[p4sec] destionation_mac_address size " << destionation_mac_address.size() <<  std::endl;
	//hexdump((char*)&destionation_mac_address[0], destionation_mac_address.size());

	//std::cout << "[p4sec] source_mac_address size " << source_mac_address.size() <<  std::endl;
	//hexdump((char*)&source_mac_address[0], source_mac_address.size());

	//std::cout << "[p4sec] security_tag size " << security_tag.size() <<  std::endl;
	//hexdump((char*)&security_tag[0], security_tag.size());

	//std::cout << "[p4sec] secure_data size " << secure_data.size() <<  std::endl;
	//hexdump((char*)&secure_data[0], secure_data.size());

	//std::cout << "[p4sec] integrity_check_value size " << integrity_check_value.size() <<  std::endl;
	//hexdump((char*)&integrity_check_value[0], integrity_check_value.size());


	//terms K, IV, A, P, C, T used in section 2.1 of the GCM specification ( GCM ) as submitted to NIST

	//128 bit key
	//std::vector<unsigned char> K;
	//K.reserve(secure_association_key.size());
	//K.insert( K.cend(), secure_association_key.cbegin(), secure_association_key.cend() );

	//std::cout << "[p4sec] K size " << K.size() <<  std::endl;
	//hexdump((char*)&K[0], K.size());

	//12 byte IV
	std::array<unsigned char, sizeof(sci_t) + sizeof(pn_t)> IV;
	//The 64 most significant bits of the 96-bit IV are the octets of the SCI, encoded as a binary number (9.1).
	std::copy(secure_channel_identifier.begin(), secure_channel_identifier.end(), IV.begin());
	//The 32 least significant bits of the 96-bit IV are the octets of the PN, encoded as a binary number
	std::copy(packet_number.begin(), packet_number.end(), IV.begin() + sizeof(sci_t));

	//std::cout << "[p4sec] IV size " << IV.size() <<  std::endl;
	//hexdump((char*)&IV[0], IV.size());


	//A is the Destination MAC Address, Source MAC Address, and the octets of the SecTAG concatenated in that order
	std::array<unsigned char, 2 * sizeof(mac_t) + sizeof(sectag_t)> A { };
	std::copy(destionation_mac_address.begin(), destionation_mac_address.end(), A.begin());
	std::copy(source_mac_address.begin(), source_mac_address.end(), A.begin() + sizeof(mac_t));
	std::copy(security_tag.begin(), security_tag.end(), A.begin() + 2*sizeof(mac_t));

	//A.reserve(destionation_mac_address.size() + source_mac_address.size() + security_tag.size());
	//A.insert( A.cend(), destionation_mac_address.cbegin(), destionation_mac_address.cend() );
	//A.insert( A.cend(), source_mac_address.cbegin(), source_mac_address.cend() );
	//A.insert( A.cend(), security_tag.cbegin(), security_tag.cend() );

	std::cout << "[p4sec] IV: " << IV << std::endl;

	out_user_data = data_t { };
	out_user_data.resize(secure_data.size(), '\0');

	int actual_size=0, final_size=0;
	EVP_CIPHER_CTX *d_ctx = EVP_CIPHER_CTX_new();
	EVP_DecryptInit(d_ctx, EVP_aes_128_gcm(), secure_association_key.data(), IV.data());

	//https://www.openssl.org/docs/man1.0.2/crypto/EVP_get_cipherbynid.html#GCM_Mode
	//To specify any additional authenticated data (AAD) a call to EVP_CipherUpdate(), EVP_EncryptUpdate() or EVP_DecryptUpdate() should be made with the output parameter out set to NULL
	EVP_DecryptUpdate(d_ctx, NULL, &actual_size, A.data(), A.size());

	EVP_DecryptUpdate(d_ctx, out_user_data.data(), &actual_size,
			secure_data.data(), secure_data.size() );
	EVP_CIPHER_CTX_ctrl(d_ctx, EVP_CTRL_GCM_SET_TAG, 16, integrity_check_value.data());
	int result = EVP_DecryptFinal(d_ctx, &out_user_data[actual_size], &final_size);

	if(result == 1) {
		//valid result
		std::cout << "[p4sec] decryption successfull." << std::endl;
	} else {
		//decryption failed
		//-> abprt/drop packet?
		std::cout << "[p4sec] decryption failed." << std::endl;
	}

	//std::cout << "result of decryption: " << result << std::endl;


	EVP_CIPHER_CTX_free(d_ctx);

	return result;
}

// do not put these inside an anonymous namespace or some compilers may complain
BM_REGISTER_EXTERN(ExternCrypt);
BM_REGISTER_EXTERN_METHOD(ExternCrypt, protect, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &);
BM_REGISTER_EXTERN_METHOD(ExternCrypt, validate, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &, Data &, Data &);

BM_REGISTER_EXTERN_W_NAME(ext_crypt, ExternCrypt);
BM_REGISTER_EXTERN_W_NAME_METHOD(ext_crypt, ExternCrypt, protect, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &);
BM_REGISTER_EXTERN_W_NAME_METHOD(ext_crypt, ExternCrypt, validate, const Data &, const Data &, const Data &, const Data &, const Data &, const Data &, Data &, Data &);
