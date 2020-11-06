# common
from common_lib.topology import Topology, Edge, BDDPPacket
from common_lib.logger import Logger
from common_lib.event import EventSystem

# local
from local_lib.p4runtime_lib import SwitchConnection, PortMonitor
from local_lib.packet import CPUPacket

# other
from threading import Lock, Thread, Event
from time import time, sleep
from scapy.all import Ether # type: ignore
from macsec_pb2 import bddp_key # type: ignore
from typing import Optional

class TopologyManager:
    def __init__(self, controller):
        # utils
        self._controller = controller
        self._logger = controller.logger
        self._event_system = controller.event_system
        self._switch_connection = controller.switch_connection
        self._global_controller = controller.global_controller
        self._port_monitor = controller.port_monitor
        self._mac = controller.settings.get_mac()
        self._ignore_ports = controller.settings.get_extern_ports()

        # Attributes
        self._topology = Topology()

        self._lldp_interval = 30#s
        self._event_system.set_interval(self.send_lldp_packets, self._lldp_interval, \
                immediate=True)
        self._event_system.set_interval(self.lldp_garbage_collect, self._lldp_interval)

        self._bddp_sequence = int(time()) # check if lock is needed when you access this

    def get_topology(self) -> Topology:
        return self._topology

    def add_local_edge(self, edge: Edge) -> None:
        self._logger.info("Change local topology, add connection: " + str(edge))
        self._topology.set(edge)

    def remove_local_edge(self, edge: Edge) -> None:
        self._logger.info("Change local topology, remove connection: " + str(edge))
        self._topology.remove(edge.get_controller1(), edge.get_controller2())

    def add_edge(self, edge: Edge) -> None:
        self._global_controller.get_service("lldp").add_edge(edge)

    def remove_edge(self, edge: Edge) -> None:
        self._global_controller.get_service("lldp").remove_edge(edge)

    def handle_port_change(self, switch_id, port, status):
        self._logger.debug("Port changed", 2)
        self.send_lldp_packets()
        #TODO delete expired edges

    def handle_lldp(self, packet: CPUPacket) -> None:
        """ Handle incoming lldp packet -> update topology """
        if packet.port in self._ignore_ports:
            return

        # If you change this, check if you need a lock

        # read bddp / lldp package
        try:
            bddp_packet = BDDPPacket.parse(packet["Ether"], \
                    self._global_controller.get_service("registration").get_key())
        except:
            # ignore
            return
        controller1 = self._global_controller.get_service("registration").get_id()
        port1 = packet.port
        controller2 = bddp_packet.get_controller()
        port2 = bddp_packet.get_port()

        # Construct edge for incremental topology change
        edge = Edge(controller1, port1, controller2, port2)

        self._logger.debug("Received LLDP - " + str(edge), 3)

        if self._topology.has(edge):
            self._logger.debug("topology did not change.", 3)
            self._topology.refresh(edge)
        else:
            self._logger.debug("topology changed.", 3)
            # update global topology
            # Let the global controller update the local topology.
            # - Easier to implement
            # - LLDP packets do not have a short interval.
            #   In the rare case that we receive another lldp packet before the
            #   global controller has updated the local topology, the packet is sent twice
            #   and the global controller ignores it.
            self.add_edge(edge)

    def send_lldp_packets(self, key: Optional[ bddp_key ] = None):
        """ Send lldp packets out on every port. """
        self._logger.debug("Sending lldp packets.", 3)

        #generate packets
        bddp_ether = Ether( \
            src=self._mac, \
            dst="ff:ff:ff:ff:ff:ff", \
            type=CPUPacket.TYPE_BDDP \
        )
        packets = [ ]
        for i in range(self._switch_connection.get_num_ports()):
            if i in self._ignore_ports:
                continue
            bddp_packet = BDDPPacket(str(self._global_controller.get_service("registration").get_id()), \
                    i, self._global_controller.get_service("registration").get_key() if key is None else key.value, \
                    self._bddp_sequence)
            self._bddp_sequence += 1 # only modified here

            cpu = CPUPacket(reason="SEND_DIRECT", port=i, timestamp=int(time()))
            packets += [ bytes(cpu / bddp_ether / bddp_packet.serialize()) ]

        # send
        self._switch_connection.send_packets_out(packets) # threadsafe (synchronized queue)

    def lldp_garbage_collect(self):
        self._logger.debug("Running lldp garbage collection.", 2)

        edges = self._topology.get_edges_older_than(self._lldp_interval)

        for edge in edges:
            try:
                self.remove_edge(edge)
            except Exception as e:
                self._logger.warn("Unexpected exception occured: " + str(e))

    def start(self):
        self._port_monitor.register_on_change(self.handle_port_change)

    def teardown(self):
        self._port_monitor.unregister_on_change(self.handle_port_change)
