#ifndef IPSEC_CRYPT_HPP_PTIOCPNB
#define IPSEC_CRYPT_HPP_PTIOCPNB

#include <bm/bm_sim/extern.h>
#include <bm/bm_sim/data.h>
#include <openssl/aes.h>

namespace bm {
	namespace ipsec {
		class ExternTest : public bm::ExternType {
			public:
				BM_EXTERN_ATTRIBUTES {

				}
				struct ctr_state {
					unsigned char ivec[16];
					unsigned int num;
					unsigned char ecount[16];
				};

				virtual void init() override;
				void init_ctr(struct ctr_state *, const unsigned char[16]);
				void crypt_message(const unsigned char *, unsigned char *,
						unsigned long int src_len, const AES_KEY *, const unsigned char *);
				void decrypt_aes_ctr(bm::Header&, bm::Header&, bm::Header&, const bm::Data &, const bm::Data &);
				void encrypt_aes_ctr(bm::Header&, bm::Header&, const bm::Data &, const bm::Data &);
		};
	} // namespace ipsec
} // namespace bm

#endif /* end of include guard: IPSEC_CRYPT_HPP_PTIOCPNB */
