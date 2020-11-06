# common
from common_lib.logger import Logger

# local
from local_lib.packet import CPUPacket, Notification, notification_types
from local_lib.p4runtime_lib import SwitchConnection

class PacketProcessor:
    def __init__(self,
            logger: Logger,
            topology_manager,
            l2_manager,
            authenticator,
            macsec_manager,
            ipsec_manager
        ):
        self._logger = logger
        self._topology_manager = topology_manager
        self._l2_manager = l2_manager
        self._authenticator = authenticator
        self._macsec_manager = macsec_manager
        self._ipsec_manager = ipsec_manager

    def process_packet(self, packet):
        cpu = CPUPacket(packet.payload)
        self._logger.info("Packet in -> " + str(cpu.summary()))

        if not cpu.haslayer(Notification):
            # drop the packet
            return

        notification = cpu[Notification]

        self._logger.debug("Notification type: " + notification_types[notification.type])

        if notification.type == Notification(type="DST_MAC_UNKNOWN").type \
                or notification.type == Notification(type="SRC_MAC_UNKNOWN").type \
                or notification.type == Notification(type="REFRESH_L2_ENTRY").type \
                or notification.type == Notification(type="CHANGED_L2_ENTRY").type \
                or notification.type == Notification(type="ARP").type:
            self._l2_manager.process_packet(cpu)
        elif notification.type == Notification(type="LLDP").type:
            self._l2_manager.learn_source(cpu)
            self._topology_manager.handle_lldp(cpu)
        elif notification.type == Notification(type="EAP").type:
            self._authenticator.handle_eapol(cpu)
        elif notification.type == Notification(type="MACSEC_SOFT_PACKET_LIMIT").type \
                or notification.type == Notification(type="MACSEC_HARD_PACKET_LIMIT").type:
            self._macsec_manager.handle_notification(cpu)
        elif notification.type == Notification(type="IPSEC_SOFT_PACKET_LIMIT").type \
                or notification.type == Notification(type="IPSEC_HARD_PACKET_LIMIT").type:
            self._ipsec_manager.handle_notification(cpu)
        else:
            self._logger.warn("Unknown notification type: " + str(notification.type))

    def listen(self, switch_connection: SwitchConnection):
        switch_connection.listen_packet_in(self.process_packet)


