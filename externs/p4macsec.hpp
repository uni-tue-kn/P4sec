#ifndef P4MACSEC_HPP_7UZJGWZB
#define P4MACSEC_HPP_7UZJGWZB

#include <bm/bm_sim/extern.h>
#include <bm/bm_sim/data.h>

#include <vector>
#include <string>

#define SAK_SIZE 16
#define SCI_SIZE 8
#define PN_SIZE 4
#define ADDR_SIZE 6
#define SECTAG_SIZE 16
#define ICV_SIZE 16
#define IPV4_HDR_SIZE 20
#define ETHERTYPE_SIZE 2

#define SECURE_DATA_SIZE 123

namespace bm {
	namespace p4macsec {
		using sak_t = std::array<unsigned char, SAK_SIZE>;
		using sci_t = std::array<unsigned char, SCI_SIZE>;
		using pn_t = std::array<unsigned char, PN_SIZE>;
		using mac_t = std::array<unsigned char, ADDR_SIZE>;
		using sectag_t = std::array<unsigned char, SECTAG_SIZE>;
		using icv_t = std::array<unsigned char, ICV_SIZE>;
		using ipv4_hdr_t = std::array<unsigned char, IPV4_HDR_SIZE>;
		using ethertype_t = std::array<unsigned char, ETHERTYPE_SIZE>;
		using data_t = std::vector<unsigned char>;

		struct ExternCrypt : public bm::ExternType {
			BM_EXTERN_ATTRIBUTES { }

			virtual void init() override;

			void protect(
				const bm::Data &in_sak,
				const bm::Data &in_sci,
				const bm::Data &in_pn,
				const bm::Data &in_src_addr,
				const bm::Data &in_dst_addr,
				const bm::Data &in_sectag,
				const bm::Data &in_ethertype,
				const bm::Data &in_prepend_ipv4_hdr,
				const bm::Data &in_ipv4_hdr
			);

			void validate(
				const bm::Data &in_sak,
				const bm::Data &in_sci,
				const bm::Data &in_pn,
				const bm::Data &in_src_addr,
				const bm::Data &in_dst_addr,
				const bm::Data &in_sectag,
				bm::Data &out_valid,
				bm::Data &out_ethertype
			);

			int validation_function(
				const sak_t& secure_association_key,
				const sci_t& secure_channel_identifier,
				const pn_t& packet_number,
				const mac_t& destionation_mac_address,
				const mac_t& source_mac_address,
				const sectag_t& security_tag,
				const data_t& secure_data,
				icv_t integrity_check_value,
				data_t& out_user_data
			);


			void protection_function(
				const sak_t& secure_association_key,
				const sci_t& secure_channel_identifier,
				const pn_t& packet_number,
				const mac_t& destionation_mac_address,
				const mac_t& source_mac_address,
				const sectag_t& security_tag,
				const data_t& user_data,
				data_t& out_secure_data,
				icv_t& out_integrity_check_value
			);

			std::vector<unsigned char> get_char_vector(std::string, unsigned int);
			void hexDump(char *, int);
		};
	} // namespace p4macsec
} // namespace bm

#endif /* end of include guard: P4MACSEC_HPP_7UZJGWZB */
