#include "./p4ipsec.hpp"

#include <bm/bm_sim/parser.h>
#include <bm/bm_sim/tables.h>
#include <bm/bm_sim/logger.h>

#include <openssl/hmac.h>
#include <openssl/rand.h>

#include <iostream>
#include <string>
#include <vector>

using namespace bm;
using namespace bm::ipsec;
using ipsec::ExternTest;

void ExternTest::init() {

}

void ExternTest::init_ctr(struct ctr_state *state, const unsigned char iv[16]) {
	state->num = 0;
	memset(state->ecount, 0, 16);
	memcpy(state->ivec, iv, 16);
}


void ExternTest::crypt_message(const unsigned char *src, unsigned char *dst,
      unsigned long int src_len, const AES_KEY *key, const unsigned char *iv) {
	ctr_state state;
	init_ctr(&state, iv);
	AES_ctr128_encrypt(src, dst, src_len, key, state.ivec, state.ecount, &state.num);
}

void ExternTest::decrypt_aes_ctr(bm::Header& ipv4, bm::Header& esp, bm::Header& standard_metadata, const bm::Data &key_data, const bm::Data &key_hmac_data) {
	std::cout << "[IPSEC] processing packet\n";
	std::cout << "[IPSEC] Ingress port: " << this->get_packet().get_ingress_port() << "\n";
	std::cout << "[IPSEC] Egress port: " << this->get_packet().get_egress_port() << "\n";

	auto key_nonce = key_data.get_string();
	if (key_nonce.length() < 20) {
		//CLI schneidet führende Nullen ab, also fügen wir sie wieder hinzu
		key_nonce = std::string(20 - key_nonce.length(), '\0').append(key_nonce);
	} else if (key_nonce.length() > 20) {
		//sollte nicht vorkommen, da die CLI "zu lange" Parameter verhindert
		key_nonce.resize(20);
	}

	auto hmay_key = key_hmac_data.get_string();
	if (hmay_key.length() < 16) {
		//CLI schneidet führende Nullen ab, also fügen wir sie wieder hinzu
		hmay_key = std::string(16 - hmay_key.length(), '\0').append(hmay_key);
	} else if (hmay_key.length() > 16) {
		//sollte nicht vorkommen, da die CLI "zu lange" Parameter verhindert
		hmay_key.resize(16);
	}

    //the key consists of the key used for encryption and a nonce
	auto key_string = key_nonce.substr(0, 16);
	auto nonce_string = key_nonce.substr(16, 4);

	//prepare AES key
	std::vector<unsigned char> key_vect(key_string.begin(), key_string.end());
	AES_KEY key;
	AES_set_encrypt_key(key_vect.data(), 128, &key);

	std::vector<unsigned char> raw_packet_data;
	raw_packet_data.resize(get_packet().get_data_size(), '\0');
	std::copy(get_packet().data(),
		get_packet().data() + get_packet().get_data_size(),
		raw_packet_data.begin());

	std::cout << "[IPSEC] raw packet data length: " << raw_packet_data.size()
		<< "\n";

	//check the ICV
	//ICV = 12 last octets of the ESP trailer
	std::vector<unsigned char> ICV;
	ICV.resize(12, '\0');
	std::copy(raw_packet_data.end() - 12, raw_packet_data.end(), ICV.begin());

	//concatenate ESP header, payload and ESP trailer
	std::vector<unsigned char> ICV_check;
	ICV_check.resize(raw_packet_data.size() - 12 + 8, '\0'); //-12: ICV, +8: ESP Header
	std::copy(esp[0].get_bytes().data(), esp[0].get_bytes().data() + 4,
		ICV_check.begin());
	std::copy(esp[1].get_bytes().data(), esp[1].get_bytes().data() + 4,
		ICV_check.begin() + 4);
	std::copy(raw_packet_data.begin(), raw_packet_data.end() - 12,
		ICV_check.begin() + 8);

	//compute HMAC
	std::vector<unsigned char> hmay_key_vect(hmay_key.begin(), hmay_key.end());
	unsigned char* hmac;
	unsigned int hmac_len;
	hmac = HMAC(EVP_md5(), hmay_key_vect.data(), hmay_key_vect.size(),
		ICV_check.data(), ICV_check.size(), NULL, &hmac_len);

	//drop packet if ICV and the computed hmac are not the same
	if (((hmac_len != 16) || std::memcmp(hmac, ICV.data(), ICV.size())) != 0) {
		standard_metadata
			.get_field(standard_metadata.get_header_type().get_field_offset("egress_spec"))
			.set("1FF");
		standard_metadata
			.get_field(standard_metadata.get_header_type().get_field_offset("mcast_grp"))
			.set("0");
	}

	//decryption
	//IV = first 16 Bytes of the payload
	std::vector<unsigned char> IV;
	IV.resize(8, '\0');
	std::copy(raw_packet_data.begin(), raw_packet_data.begin() + 8, IV.begin());

	//compose nonce, IV and blockcounter into the Counter Block Format (32bit, last bit 1, rest 0) (see RFC 3686)
	std::vector<unsigned char> IV_complete;
	IV_complete.resize(16, '\0');
	std::copy(nonce_string.begin(), nonce_string.end(), IV_complete.begin());
	std::copy(IV.begin(), IV.end(), IV_complete.begin() + 4);
	IV_complete[15] = (unsigned char) 1;    //block counter

	std::vector<unsigned char> encrypted;
	encrypted.resize(raw_packet_data.size() - 20, '\0');
	std::copy(raw_packet_data.begin() + 8, raw_packet_data.end() - 12,
		encrypted.begin());

	//AES_ctr128_encrypt seems not to work with char vectors -> use char array instead
	int encrypted_size = raw_packet_data.size() - 20;
	unsigned char decrypted_tmp[encrypted_size];
	memset(decrypted_tmp, 0, sizeof(decrypted_tmp));
	this->crypt_message((const unsigned char*) encrypted.data(),
		(unsigned char *) decrypted_tmp,
		(unsigned long int) raw_packet_data.size() - 20, &key,
		IV_complete.data());
	std::vector<unsigned char> decrypted(decrypted_tmp,
		decrypted_tmp + encrypted_size);

    //next header
//    char next_header = *(decrypted_tmp + encrypted_size - 1);

    //padding length
	char padding_length = *(decrypted_tmp + encrypted_size - 2);
	std::cout << "[IPSEC] padding length: " << padding_length << "\n";

	//payload
	std::vector<unsigned char> payload;
	payload.resize(encrypted_size - 2 - padding_length, '\0');
	std::copy(decrypted.begin(), decrypted.end() - 2 - padding_length,
		payload.begin());

	//prepare decrypted ipv4 header for transformation into p4 header fields
	std::vector<char> ipv4_new;
	ipv4_new.resize(20, '\0');
	std::copy(payload.begin(), payload.begin() + 20, ipv4_new.begin());

	//some header field's sizes are not a multiple of 1 byte, but bvm only supperts writing bytes to p4 header fields
	//-> bitwise magic necessary
	char version = (ipv4_new[0] >> 4) & 15;
	char ihl = ipv4_new[0] & 15;
	char flags = (ipv4_new[6] >> 5) & 7;
	std::vector<char> fragOffset;
	fragOffset.resize(2, '\0');
	fragOffset[0] = ((ipv4_new[6] & 31) << 3) | ((ipv4_new[7] >> 5) & 7);
	fragOffset[1] = ipv4_new[7] & 31;

	//write the content of the header fields into the p4 ipv4 header fields
	ipv4[0].set_bytes(&version, 1);			//version
	ipv4[1].set_bytes(&ihl, 1);				//ihl
	ipv4[2].set_bytes(&ipv4_new[1], 1);		//diffserv
	ipv4[3].set_bytes(&ipv4_new[2], 2);		//totalLen
	ipv4[4].set_bytes(&ipv4_new[4], 2);		//identification
	ipv4[5].set_bytes(&flags, 1);			//flags
	ipv4[6].set_bytes(&fragOffset[0], 2);	//fragOffset
	ipv4[7].set_bytes(&ipv4_new[8], 1);		//ttl
	ipv4[8].set_bytes(&ipv4_new[9], 1);		//protocol
	ipv4[9].set_bytes(&ipv4_new[10], 2);	//hdrChecksum
	ipv4[10].set_bytes(&ipv4_new[12], 4);	//srcAddr
	ipv4[11].set_bytes(&ipv4_new[16], 4);	//dstAddr

	//replace payload
	//first, remove all the data
	get_packet().remove(get_packet().get_data_size());
	//make room for the ciphertext and write the ciphertext in it
	char *payload_start = get_packet().prepend(
		(unsigned long int) encrypted_size - 2 - padding_length - 20); //2 = padding length, 20 = ipv4 header
	for (uint i = 0; i < (unsigned long int) encrypted_size - 2 - padding_length - 20; i++) {
		payload_start[i] = payload[i + 20];	//don't copy ipv4 header -> +20
	}
}


void ExternTest::encrypt_aes_ctr(bm::Header& ipv4, bm::Header& esp, const bm::Data &key_data, const bm::Data &key_hmac_data) {
	std::cout << "[IPSEC] processing packet\n";
	std::cout << "[IPSEC] read key and hmac\n";

	auto key_nonce = key_data.get_string();
	if (key_nonce.length() < 20) {
		//CLI schneidet führende Nullen ab, also fügen wir sie wieder hinzu
		key_nonce = std::string(20 - key_nonce.length(), '\0').append(key_nonce);
	} else if (key_nonce.length() > 20) {
		//sollte nicht vorkommen, da die CLI "zu lange" Parameter verhindert
		key_nonce.resize(20);
	}

	auto hmay_key = key_hmac_data.get_string();
	if (hmay_key.length() < 16) {
		//CLI schneidet führende Nullen ab, also fügen wir sie wieder hinzu
		hmay_key = std::string(16 - hmay_key.length(), '\0').append(hmay_key);
	} else if (hmay_key.length() > 16) {
		//sollte nicht vorkommen, da die CLI "zu lange" Parameter verhindert
		hmay_key.resize(16);
	}


    //the key consists of the key used for encryption and a nonce
	auto key_string = key_nonce.substr(0, 16);
	auto nonce_string = key_nonce.substr(16, 4);

	std::cout << "[IPSEC] prepare AES key\n";
	//prepare AES key
	std::vector<unsigned char> key_vect(key_string.begin(), key_string.end());
	AES_KEY key;
	AES_set_encrypt_key(key_vect.data(), 128, &key);

	std::cout << "[IPSEC] restore ipv4 header\n";
	//restore the ipv4 header that was stripped from the packet by p4
	//std::cout << get_packet() << std::endl;
	std::vector<unsigned char> raw_packet_data;
	auto raw_packet_size = get_packet().get_data_size() + 20;
	raw_packet_data.resize(raw_packet_size, '\0');

	std::vector<char> ipv4_reassemble_tmp;
	ipv4_reassemble_tmp.resize(3, '\0');
	std::copy(ipv4[0].get_bytes().data(), ipv4[0].get_bytes().data() + 1,
		ipv4_reassemble_tmp.begin());
	std::copy(ipv4[1].get_bytes().data(), ipv4[1].get_bytes().data() + 1,
		ipv4_reassemble_tmp.begin() + 1);

	ipv4_reassemble_tmp[0] = (ipv4_reassemble_tmp[0] << 4)
		| (ipv4_reassemble_tmp[1] & 15); //merge version and ihl into one byte

	std::copy(ipv4_reassemble_tmp.data(), ipv4_reassemble_tmp.data() + 1,
		raw_packet_data.begin());         //version + ihl
	std::copy(ipv4[2].get_bytes().data(), ipv4[2].get_bytes().data() + 1,
		raw_packet_data.begin() + 1);     //diffserv
	std::copy(ipv4[3].get_bytes().data(), ipv4[3].get_bytes().data() + 2,
		raw_packet_data.begin() + 2);     //totalLen
	std::copy(ipv4[4].get_bytes().data(), ipv4[4].get_bytes().data() + 2,
		raw_packet_data.begin() + 4);     //identification

	std::copy(ipv4[5].get_bytes().data(), ipv4[5].get_bytes().data() + 1,
		ipv4_reassemble_tmp.begin());
	std::copy(ipv4[6].get_bytes().data(), ipv4[6].get_bytes().data() + 2,
		ipv4_reassemble_tmp.begin() + 1);
	ipv4_reassemble_tmp[0] = (ipv4_reassemble_tmp[0] << 5)
		| ((ipv4_reassemble_tmp[1] >> 3) & 31);
	ipv4_reassemble_tmp[1] = (ipv4_reassemble_tmp[1] << 5)
		| (ipv4_reassemble_tmp[2] >> 3 & 31);
	std::copy(ipv4_reassemble_tmp.data(), ipv4_reassemble_tmp.data() + 2,
		raw_packet_data.begin() + 6);     //fragOffset + flags

	std::copy(ipv4[7].get_bytes().data(), ipv4[7].get_bytes().data() + 1,
		raw_packet_data.begin() + 8);       //ttl
	std::copy(ipv4[8].get_bytes().data(), ipv4[8].get_bytes().data() + 1,
		raw_packet_data.begin() + 9);       //protocol
	std::copy(ipv4[9].get_bytes().data(), ipv4[9].get_bytes().data() + 2,
		raw_packet_data.begin() + 10);      //hdrChecksum
	std::copy(ipv4[10].get_bytes().data(), ipv4[10].get_bytes().data() + 4,
		raw_packet_data.begin() + 12);    //srcAddr
	std::copy(ipv4[11].get_bytes().data(), ipv4[11].get_bytes().data() + 4,
		raw_packet_data.begin() + 16);    //dstAddr

	std::cout << "[IPSEC] copy payload\n";
	//copy payload
	std::copy(get_packet().data(),
		get_packet().data() + get_packet().get_data_size(),
		raw_packet_data.begin() + 20);

	//check if we need to add padding
	char padding = 0;
	if (raw_packet_size % 16 != 0) {
		padding = 16 - (raw_packet_size % 16);
	}

	std::cout << "[IPSEC] add padding\n";
	raw_packet_size += padding + 2; //2: padding length and next header
	raw_packet_data.resize(raw_packet_size, '\0');

	//add padding length and next header
	raw_packet_data[raw_packet_size - 2] = padding;
	raw_packet_data[raw_packet_size - 1] = 4; //next header = ipv4

	std::cout << "[IPSEC] generate IV\n";
	//generate IV
	std::vector<unsigned char> IV;
	IV.resize(8, '\0');
	RAND_bytes(IV.data(), 8);

	//compose nonce, IV and blockcounter into the Counter Block Format (32bit, last bit 1, rest 0) (see RFC 3686)
	std::vector<unsigned char> IV_complete;
	IV_complete.resize(16, '\0');
	std::copy(nonce_string.begin(), nonce_string.end(), IV_complete.begin());
	std::copy(IV.begin(), IV.end(), IV_complete.begin() + 4);
	IV_complete[15] = (unsigned char) 1;    //block counter

	std::cout << "[IPSEC] encrypt\n";

	//encryption
	unsigned char encrypted[raw_packet_size];
	memset(encrypted, 0, sizeof(encrypted));
	crypt_message((const unsigned char*) raw_packet_data.data(),
		(unsigned char *) encrypted, (unsigned long int) raw_packet_size, &key,
		IV_complete.data());

	std::vector<unsigned char> payload;
	payload.resize(raw_packet_size + 8 + 12, '\0'); //8: IV, 12: ICV
	std::copy(IV.begin(), IV.end(), payload.begin());
	std::copy(encrypted, encrypted + raw_packet_size, payload.begin() + 8);

	std::cout << "[IPSEC] calculate IV\n";
	//calculate ICV
	std::vector<unsigned char> hmay_key_vect(hmay_key.begin(), hmay_key.end());
	std::vector<unsigned char> ICV_check;
	ICV_check.resize(payload.size() + 8 - 12, '\0'); //+8: ESP header, -12: ICV
	std::copy(esp[0].get_bytes().data(), esp[0].get_bytes().data() + 4,
		ICV_check.begin());
	std::copy(esp[1].get_bytes().data(), esp[1].get_bytes().data() + 4,
		ICV_check.begin() + 4);
	std::copy(payload.data(), payload.data() + payload.size() - 12,
		ICV_check.begin() + 8);
	unsigned int hmac_len;
	unsigned char* hmac = HMAC(EVP_md5(), hmay_key_vect.data(),
		hmay_key_vect.size(), ICV_check.data(), ICV_check.size(), NULL,
		&hmac_len);

	std::copy(hmac, hmac + 12, payload.end() - 12);

	std::cout << "[IPSEC] replace payload\n";
	//replace payload
	//first, remove all the data
	get_packet().remove(get_packet().get_data_size());
	//make room for the ciphertext and write the ciphertext in it
	char *payload_start = get_packet().prepend(
		(unsigned long int) payload.size());
	for (uint i = 0; i < payload.size(); i++) {
		payload_start[i] = payload[i];   //don't copy ipv4 header -> +20
	}

	std::cout << "[IPSEC] set esp.payload length meta data\n";
	//set esp payload length meta data
	std::vector<char> payload_length;
	payload_length.resize(2, '\0');
	payload_length[0] = (payload.size() >> 8) & 255;
	payload_length[1] = payload.size() & 255;

	std::cout << "[IPSEC] set header\n";
	auto& totalLen = ipv4.get_field(ipv4.get_header_type().get_field_offset("totalLen"));
	totalLen.set(payload.size() + 28);
	std::cout << "[IPSEC] finished\n";
}

BM_REGISTER_EXTERN(ExternTest);
BM_REGISTER_EXTERN_METHOD(ExternTest, decrypt_aes_ctr, Header&, Header&, Header&, const Data &, const Data &);
BM_REGISTER_EXTERN_METHOD(ExternTest, encrypt_aes_ctr, Header&, Header&, const Data &, const Data &);


BM_REGISTER_EXTERN_W_NAME(ipsec_crypt, ExternTest);
BM_REGISTER_EXTERN_W_NAME_METHOD(ipsec_crypt, ExternTest, decrypt_aes_ctr, Header&, Header&, Header&, const Data &, const Data &);
BM_REGISTER_EXTERN_W_NAME_METHOD(ipsec_crypt, ExternTest, encrypt_aes_ctr, Header&, Header&, const Data &, const Data &);
