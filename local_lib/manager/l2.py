# common
from common_lib.logger import Logger
from common_lib.event import EventSystem

# local
from local_lib.packet.cpu import CPUPacket, Notification
from local_lib.p4runtime_lib import SwitchConnection
from local_lib.settings import Settings

# other
from time import time
from copy import copy
from typing import Dict, List
from datetime import datetime, timedelta
from scapy.all import ARP, Ether # type: ignore


class L2Entry:

    def __init__(self, mac: str, port: int, timestamp: int):
        self._mac = mac
        self._port = port
        self._timestamp = timestamp

    def refresh(self, timestamp):
        self._timestamp = timestamp

    def get_mac(self):
        return self._mac

    def get_port(self):
        return self._port

    def set_timestamp(self, timestamp: int) -> None:
        self._timestamp = timestamp

    def get_timestamp(self):
        return self._timestamp

    def __str__(self):
        return "MAC: " + self.get_mac() + \
                ", Port: " + str(self.get_port()) + \
                ", Timestamp: " + str(datetime.fromtimestamp(self.get_timestamp()))

class L2Manager:
    def __init__(self,
            logger: Logger,
            settings: Settings,
            event_system: EventSystem,
            switch_connection: SwitchConnection
        ) -> None:
        # utils
        self._logger = logger
        self._settings = settings
        self._switch_connection = switch_connection

        # attributes
        self._mapping = { } # type: Dict[ str, L2Entry ]
        self._l2_mapping_timeout = 40 #s
        self._gateway_mac_set = False

        event_system.set_interval(self._remove_old_macs, self._l2_mapping_timeout)

    def _set_entry(self, entry):
        self._mapping[entry.get_mac()] = entry

    def _delete_entry(self, entry):
        del self._mapping[entry.get_mac()]

    def _has_entry(self, mac_address):
        return mac_address in self._mapping

    def _get_entry(self, mac_address):
        return self._mapping[mac_address]

    def _write_l2_entry(self, entry):
        self._logger.debug("writing l2 entry (" + str(entry) + ")", 4)
        self._set_entry(entry)
        self._switch_connection.write( \
            table_name="ingress.ethernet.forward.mac_dst", \
            match_fields={ "hdr.ethernet.dstAddr": entry.get_mac() }, \
            action_name="ingress.ethernet.forward.forward", \
            action_params={ "port": entry.get_port() } \
        )

        self._switch_connection.write(
            table_name="ingress.ethernet.learn.mac_src", \
            match_fields={ "hdr.ethernet.srcAddr": entry.get_mac() }, \
            action_name="ingress.ethernet.learn.src_known",
            action_params={ \
                "port": entry.get_port(),
                "refresh_time": int(datetime.timestamp(datetime.now() + timedelta(seconds=self._l2_mapping_timeout / 2)))
            } \
        )

    def _delete_l2_entry(self, entry):
        self._logger.debug("deleting l2 entry (" + str(entry) + ")", 4)
        self._delete_entry(entry)
        self._switch_connection.delete( \
            table_name="ingress.ethernet.forward.mac_dst", \
            match_fields={ "hdr.ethernet.dstAddr": entry.get_mac() } \
        )

        self._switch_connection.delete( \
            table_name="ingress.ethernet.learn.mac_src", \
            match_fields={ "hdr.ethernet.srcAddr": entry.get_mac() } \
        )

    def _update_l2_entry(self, entry):
        """
        update an l2 entry, thus save it in software and write to switch.
        entry: L2Entry
        """
        self._logger.debug("update entry (" + str(entry) + ")")
        # delete old entries -> prevent errors by p4
        if self._has_entry(entry.get_mac()):
            self._delete_l2_entry(entry)
        self._write_l2_entry(entry)

    def learn_source(self, packet):
        """
        Learn a source mac address.
        packet: CPUPacket
        """
        ethernet = packet["Ether"]
        self._logger.debug("Learn new mac address {mac} on port {port}"
                .format(mac=ethernet.src, port=packet.port))
        if ethernet.src.lower() == self._settings.get_mac().lower():
            if not self._gateway_mac_set:
                self._switch_connection.write(
                    table_name="ingress.ethernet.learn.mac_src", \
                    match_fields={ "hdr.ethernet.srcAddr": ethernet.src }, \
                    action_name="ingress.ethernet.learn.ignore_source"
                )
                self._gateway_mac_set = True
        else:
            self._update_l2_entry(L2Entry(ethernet.src, packet.port, int(time())))

    def _flood_packet(self, packet: CPUPacket) -> None:
        """
        Flood packet to all ports except the ingress port.
        packet: CPUPacket
        """
        packets = [] # type: List[ bytes ]
        for i in range(1, self._switch_connection.get_num_ports()):
            if i != packet.port:
                self._logger.debug("flooding, port " + str(i), 4)
                cpu = CPUPacket(reason="SEND_DIRECT", port=i)
                packets += [ bytes(cpu / copy(packet["Ether"])) ]

        self._switch_connection.send_packets_out(packets)

    def process_packet(self, packet):
        """
        process packet
        packet: CPUPacket
        """

        type = packet.type

        if type == Notification(type="SRC_MAC_UNKNOWN").type \
                or type == Notification(type="REFRESH_L2_ENTRY").type \
                or type == Notification(type="CHANGED_L2_ENTRY").type:
            self.learn_source(packet)
            cpu = CPUPacket(
                reason="SEND",
                port=packet.port
            )
            self._switch_connection.send_packet_out(bytes(cpu / packet["Ether"]))
        elif type == Notification(type="DST_MAC_UNKNOWN").type:
            self._logger.debug("destination mac {mac} unknown"
                    .format(mac=packet["Ether"].dst))
            self._flood_packet(packet)
        elif type == Notification(type="ARP").type:
            arp = packet["ARP"]
            if arp.pdst == self._settings.get_gateway():
                reply = ARP(op="is-at", hwsrc=self._settings.get_mac(),
                        psrc=arp.pdst, hwdst="FF:FF:FF:FF:FF:FF",
                        pdst=arp.psrc)

                cpu = CPUPacket(
                    reason="SEND_DIRECT",
                    port=packet.port,
                )
                cpu.payload = Ether(src=self._settings.get_mac(), dst=packet["Ether"].src) / reply
                self._switch_connection.send_packet_out(bytes(cpu))
            else:
                self._flood_packet(packet)

    def _remove_old_macs(self) -> None:
        self._logger.debug("Remove old l2 entries.")
        old_entries = [ entry for mac, entry in self._mapping.items()
            if datetime.fromtimestamp(entry.get_timestamp()) \
                    + timedelta(seconds=self._l2_mapping_timeout) < datetime.now() ]

        for entry in old_entries:
            self._delete_l2_entry(entry)
