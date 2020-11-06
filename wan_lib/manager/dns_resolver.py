# common
from common_lib.ipaddress import Address

# other
from ipaddress import ip_address

class DNSResolver:
    def __init__(self) -> None:
        self._dns_mapping = {
            "test-1.dns-test.p4-vpn.haeberle.me": ip_address("10.0.1.1"),
            "test-2.dns-test.p4-vpn.haeberle.me": ip_address("10.0.2.2"),
            "test-3.dns-test.p4-vpn.haeberle.me": ip_address("10.0.3.3")
        }

    def resolve(self, address: str) -> Address:
        return self._dns_mapping[address[:-1]]
