# common
from common_lib.logger import Logger
from common_lib.ipsec import Connection, Tunnel, Endpoint
from common_lib.ipaddress import Address

# local
from local_lib.p4runtime_lib import SwitchConnection
from local_lib.settings import Settings
from local_lib.packet.cpu import CPUPacket, Notification, Config
from local_lib.global_ import GlobalController

# other
from typing import Set, Optional
import traceback

class RegisterManager:

    def __init__(self):
        self.unused_registers = set(range(1024))

    def get_register(self) -> int:
        return self.unused_registers.pop()

    def return_register(self, register: int):
        self.unused_registers.add(register)


class IpsecManager:
    def __init__(self,
            logger: Logger,
            settings: Settings,
            switch_connection: SwitchConnection,
            global_controller: GlobalController
        ):
        self._logger = logger
        self._settings = settings
        self._switch_connection = switch_connection
        self._tunnels = set() # type: Set[ Tunnel ]
        self._ip = None # type: Optional[ Address ]
        self._global_controller = global_controller

        self.register_manager = RegisterManager()

        self.register_tunnel = dict()

    def get_ip(self) -> str:
        assert self._ip is not None, "IP of concentrator has not been set."
        return str(self._ip)

    def set_ip(self, ip: Address) -> None:
        self._logger.info("New concentrator ip: " + str(ip))
        self._ip = ip

    def _write_decrypt(self,
            source: Endpoint,
            destination: Endpoint,
            connection: Connection,
            register: int
        ) -> None:
        self._logger.debug("Write decryption rule.")

        src_address = str(source.get_address())
        dst_address = str(destination.get_address())

        self._switch_connection.write(
            table_name="ingress.ethernet.ipv4.ipsec.decrypt",
            match_fields={
                "hdr.ipv4.srcAddr": src_address,
                "hdr.ipv4.dstAddr": dst_address,
                "hdr.esp.spi": connection.get_spi()
            },
            action_name="ingress.ethernet.ipv4.ipsec.esp_decrypt",
            action_params={
                "key": connection.get_encryption().get_key(),
                "key_hmac": connection.get_authentication().get_key(),
                "register_index": register
            }
        )

    def _write_encrypt(self,
            source: Endpoint,
            destination: Endpoint,
            connection: Connection,
            register: int,
            soft_packet_limit: int,
            hard_packet_limit: int
        ) -> None:

        src_address = str(source.get_address())
        dst_address = str(destination.get_address())

        self._logger.debug("Write ipsec encryption rule for {src} -- {dst}"
                .format(src=src_address, dst=dst_address))

        for subnet in destination.get_subnets():
            self._switch_connection.write(
                table_name="ingress.ethernet.ipv4.ipsec.encrypt",
                match_fields={
                    "hdr.ipv4.dstAddr": (str(subnet.network_address), subnet.prefixlen)
                },
                action_name="ingress.ethernet.ipv4.ipsec.esp_encrypt",
                action_params={
                    "key": connection.get_encryption().get_key(),
                    "key_hmac": connection.get_authentication().get_key(),
                    "spi": connection.get_spi(),
                    "src": src_address,
                    "dst": dst_address,
                    "register_index": register,
                    "soft_packet_limit": soft_packet_limit,
                    "hard_packet_limit": hard_packet_limit
                })

    def new(self, tunnel: Tunnel) -> None:
        self._logger.info("Create new tunnel: " + str(tunnel))

        register1 = self.register_manager.get_register()
        register2 = self.register_manager.get_register()

        self.register_tunnel[register1] = tunnel
        self.register_tunnel[register2] = tunnel

        if tunnel in self._tunnels:
            self._logger.warn("Tunnel already exists.")
            return

        try:
            if str(tunnel.get_endpoint1().get_address()) == str(self.get_ip()):
                self._write_encrypt(tunnel.get_endpoint1(), tunnel.get_endpoint2(),
                        tunnel.get_connection_1_to_2(), register1,
                        tunnel.get_soft_packet_limit(), tunnel.get_hard_packet_limit())
                self._write_decrypt(tunnel.get_endpoint2(), tunnel.get_endpoint1(),
                        tunnel.get_connection_2_to_1(), register2)
            elif str(tunnel.get_endpoint2().get_address())== str(self.get_ip()):
                self._write_encrypt(tunnel.get_endpoint2(), tunnel.get_endpoint1(),
                        tunnel.get_connection_2_to_1(), register1,
                        tunnel.get_soft_packet_limit(), tunnel.get_hard_packet_limit())
                self._write_decrypt(tunnel.get_endpoint1(), tunnel.get_endpoint2(),
                        tunnel.get_connection_1_to_2(), register2)
            else:
                self._logger.info("ignore tunnel")

            self._tunnels.add(tunnel)
        except:
            self._logger.error("Could not create ipsec connection.")


    def _delete_encrypt(self, destination: Endpoint) -> None:
        for subnet in destination.get_subnets():
            self._logger.debug("Delete encryption rule for " + str(subnet))

            self._switch_connection.delete(
                table_name="ingress.ethernet.ipv4.ipsec.encrypt",
                match_fields={
                    "hdr.ipv4.dstAddr": (str(subnet.network_address), subnet.prefixlen)
                }
            )

    def _delete_decrypt(self,
            source: Endpoint,
            destination: Endpoint,
            connection: Connection
        ) -> None:
        src_address = str(source.get_address())
        dst_address = str(destination.get_address())

        self._switch_connection.delete(
            table_name="ingress.ethernet.ipv4.ipsec.decrypt",
            match_fields={
                "hdr.ipv4.srcAddr": src_address,
                "hdr.ipv4.dstAddr": dst_address,
                "hdr.esp.spi": connection.get_spi()
            }
        )

    def remove(self, tunnel: Tunnel) -> None:
        self._logger.info("Delete tunnel: " + str(tunnel))

        if tunnel not in self._tunnels:
            self._logger.warn("Tunnel does not exist.")
            return

        try:
            if str(tunnel.get_endpoint1().get_address()) == str(self.get_ip()):
                self._delete_encrypt(tunnel.get_endpoint2())
                self._delete_decrypt(tunnel.get_endpoint2(), tunnel.get_endpoint1(),
                        tunnel.get_connection_2_to_1())
            elif str(tunnel.get_endpoint2().get_address())== str(self.get_ip()):
                self._delete_encrypt(tunnel.get_endpoint1())
                self._delete_decrypt(tunnel.get_endpoint1(), tunnel.get_endpoint2(),
                        tunnel.get_connection_1_to_2())

            self._tunnels.remove(tunnel)
        except Exception as e:
            self._logger.error("Could not delete ipsec connection: " + str(e))
            # TODO exception

    def renew(self, tunnel: Tunnel) -> None:
        self._logger.debug("Renew connection: " + str(tunnel))

        self.remove(tunnel)
        self.new(tunnel)


    def handle_notification(self, cpu: CPUPacket) -> None:
        notification = cpu["Notification"]

        packet = CPUPacket(reason="SEND")
        packet.payload = notification.payload
        self._switch_connection.send_packet_out(bytes(packet))

        ipsec = self._global_controller.get_service("ipsec")

        if notification.type == Notification(type="IPSEC_SOFT_PACKET_LIMIT").type:
            tunnel = self.register_tunnel[notification.index]
            ipsec.notify_soft_packet_limit(tunnel)

        if notification.type == Notification(type="IPSEC_HARD_PACKET_LIMIT").type:
            tunnel = self.register_tunnel[notification.index]
            ipsec.notify_hard_packet_limit(tunnel)
