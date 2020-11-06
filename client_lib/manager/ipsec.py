# common
from common_lib.ipsec import Tunnel, Connection, Endpoint
from common_lib.logger import Logger
from common_lib.stub import StubController

# client
from client_lib.wan import WanController
from client_lib.settings import Settings

# other
from typing import cast, Tuple
from os import system

state_template = "ip xfrm state add src {0} dst {1} proto esp spi 0x{2} mode tunnel reqid 0x{2} auth \"{3}\" 0x{4} enc \"{5}\" 0x{6} limit packet-soft {7} limit time-soft {8}"
state_del_template = 'ip xfrm state del src {0} dst {1} proto esp spi 0x{2}'

policy_template = "ip xfrm policy add src {0} dst {1} dir {2} tmpl src {3} dst {4} proto esp reqid 0x{5} mode tunnel"
policy_del_template = "ip xfrm policy delete src {0} dst {1} dir {2}"

route_template = "ip route add {0} dev {1} src {2}"
route_del_template = "ip route delete {0} src {1}"

state_flush = "ip xfrm state flush"
policy_flush = "ip xfrm policy flush"

class IpsecManager:
    """ Global Ipsec manager which forwards all tunnels to the local ipsec manager. """

    def __init__(self,
            logger: Logger,
            settings: Settings,
            wan_controller: WanController
        ) -> None:
        self._logger = logger
        self._settings = settings
        self._wan_controller = wan_controller

    def _algo_to_xfrm(self, x):
        """takes algorithm from controller response and returns equivalent representation for ip xfrm

        :param x: algorithm in IPsec-Tools format
        :return: algorithm in xfrm format
        """
        return {
            "aes-ctr": "rfc3686(ctr(aes))",
            "AES-GCM": "rfc4106(gcm(aes))",
            "hmac-md5": "hmac(md5)",
            "hmac-sha256": "hmac(sha256)",
            "null": "ecb(cipher_null)",
            "null-auth": "digest_null"
        }[x]


    def _install_rule(self, rule) -> None:
        self._logger.debug("rule: " + rule, 2)
        status = system(rule)
        if status is not 0:
            self._logger.error("Could not install rule.")

    def _write_out_state(self,
            tunnel: Tunnel,
            source: Endpoint, target: Endpoint,
            connection: Connection) -> None:
        rule = state_template.format(
            str(source.get_address()), str(target.get_address()),
            connection.get_spi().hex(),
            self._algo_to_xfrm(connection.get_authentication().get_type().value), connection.get_authentication().get_key().hex(),
            self._algo_to_xfrm(connection.get_encryption().get_type().value), connection.get_encryption().get_key().hex(),
            tunnel.get_soft_packet_limit(),
            int(tunnel.get_soft_time_limit().total_seconds())
        )
        self._install_rule(rule)

    def _write_out_policy(self, source: Endpoint, target: Endpoint, connection: Connection) -> None:
        for subnet1 in source.get_subnets():
            for subnet2 in target.get_subnets():
                rule = policy_template.format(
                    str(subnet1), str(subnet2), "out",
                    str(source.get_address()), str(target.get_address()),
                    connection.get_spi().hex()
                )
                self._install_rule(rule)

    def _write_in_state(self,
            tunnel: Tunnel,
            source: Endpoint, target: Endpoint,
            connection: Connection) -> None:
        rule = state_template.format(
            str(source.get_address()), str(target.get_address()),
            connection.get_spi().hex(),
            self._algo_to_xfrm(connection.get_authentication().get_type().value), connection.get_authentication().get_key().hex(),
            self._algo_to_xfrm(connection.get_encryption().get_type().value), connection.get_encryption().get_key().hex(),
            tunnel.get_soft_packet_limit(),
            int(tunnel.get_soft_time_limit().total_seconds())
        )
        self._install_rule(rule)

    def _write_in_policy(self, source: Endpoint, target: Endpoint, connection: Connection) -> None:
        for subnet1 in source.get_subnets():
            for subnet2 in target.get_subnets():
                rule = policy_template.format(
                    str(subnet1), str(subnet2), "in",
                    str(source.get_address()), str(target.get_address()),
                    connection.get_spi().hex()
                )
                self._install_rule(rule)

    def _write_route(self, source: Endpoint, target: Endpoint) -> None:
        for subnet2 in target.get_subnets():
            rule = route_template.format(subnet2,
                    self._settings.get_interface(), source.get_address())
            self._install_rule(rule)


    def new(self, tunnel: Tunnel) -> None:
        self._logger.info("New tunnel: " + str(tunnel))

        source, target, connection1, connection2 = self._get_source_and_target(tunnel)

        self._write_out_state(tunnel, source, target, connection1)
        self._write_in_state(tunnel, target, source, connection2)
        self._write_out_policy(source, target, connection1)
        self._write_in_policy(target, source, connection2)
        self._write_route(source, target)

    def renew(self, tunnel: Tunnel):
        self._logger.info("Renewing tunnel: " + str(tunnel))
        # TODO find something better -> only update the key, soft time limit etc.
        self.remove(tunnel)
        self.new(tunnel)

    def _remove_state(self, source: Endpoint, target: Endpoint, connection: Connection) -> None:
        rule = state_del_template.format(
            str(source.get_address()), str(target.get_address()),
            connection.get_spi().hex()
        )
        self._install_rule(rule)

    def _remove_in_policy(self, source: Endpoint, target: Endpoint, connection: Connection) -> None:
        for subnet1 in source.get_subnets():
            for subnet2 in target.get_subnets():
                rule = policy_del_template.format(str(subnet1), str(subnet2), "in")
                self._install_rule(rule)

    def _remove_out_policy(self, source: Endpoint, target: Endpoint, connection: Connection) -> None:
        for subnet1 in source.get_subnets():
            for subnet2 in target.get_subnets():
                rule = policy_del_template.format(str(subnet1), str(subnet2), "out")
                self._install_rule(rule)

    def _remove_route(self, source: Endpoint, target: Endpoint) -> None:
        for subnet2 in target.get_subnets():
            rule = route_del_template.format(subnet2, source.get_address())
            self._install_rule(rule)

    def remove(self, tunnel: Tunnel):
        self._logger.info("Removing tunnel: " + str(tunnel))

        source, target, connection1, connection2 = self._get_source_and_target(tunnel)

        self._remove_state(source, target, connection1)
        self._remove_state(target, source, connection2)
        self._remove_out_policy(source, target, connection1)
        self._remove_in_policy(target, source, connection2)
        self._remove_route(source, target)

    def _get_source_and_target(self, tunnel: Tunnel) -> Tuple[ Endpoint, Endpoint, Connection, Connection ]:
        endpoint1 = tunnel.get_endpoint1()
        endpoint2 = tunnel.get_endpoint2()

        if endpoint1.get_address() == self._settings.get_ip():
            return endpoint1, endpoint2, tunnel.get_connection_1_to_2(), tunnel.get_connection_2_to_1()
        else:
            return endpoint2, endpoint1, tunnel.get_connection_2_to_1(), tunnel.get_connection_1_to_2()


