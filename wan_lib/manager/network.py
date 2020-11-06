# common
from common_lib.event import EventSystem
from common_lib.logger import Logger
from common_lib.manager import ControllerManager
from common_lib.ipsec import Connection, Tunnel, Endpoint, AES_CTR, HMAC_MD5
from common_lib.ipaddress import Address, Network
from common_lib.exception import UnknownEndpoint
from common_lib.stub import StubController

# wan
from wan_lib.manager.dns_resolver import DNSResolver

# other
from networkx import Graph # type: ignore
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from os import urandom
from datetime import timedelta

# protobuf
from ipsec_pb2 import tunnel_description # type: ignore

class NetworkManager:

    def __init__(self, \
            logger: Logger, \
            event_system: EventSystem, \
            controller_manager: ControllerManager
        ):
        self._logger = logger
        self._event_system = event_system
        self._controller_manager = controller_manager

        self._dns_resolver = DNSResolver()
        self._tunnels = Graph() # Graph<Edge<id, id>, Tunnel>

    def get_endpoints(self) -> List[ Endpoint ]:
        return [ self._tunnels.nodes[x]["endpoint"] for x in self._tunnels.nodes() ]

    def get_endpoint(self, address: Address) -> Endpoint:
        for endpoint in self.get_endpoints():
            if endpoint.get_address() == address:
                return endpoint

        raise UnknownEndpoint(address)

    def add_subnet(self, network_id: UUID, subnet: Network) -> None:
        if self._tunnels.has_node(network_id):
            self._logger.info("Add new subnet (" + str(subnet) + \
                    ") to network (" + str(network_id) + ")")
            self._tunnels.nodes[network_id]["endpoint"].add_subnet(subnet)
            self._refresh_tunnels_for(network_id)

    def remove_subnet(self, network_id: UUID, subnet: Network) -> None:
        if self._tunnels.has_node(network_id):
            self._logger.info("Remove subnet (" + str(subnet) + \
                    ") from network (" + str(network_id) + ")")
            self._tunnels.nodes[network_id]["endpoint"].remove_subnet(subnet)
            self._refresh_tunnels_for(network_id)

    def _refresh_tunnel(self, tunnel: Tunnel) -> None:
        self._logger.debug("Refresh tunnel: " + str(tunnel))

        endpoint1 = tunnel.get_endpoint1()
        endpoint2 = tunnel.get_endpoint2()

        if not endpoint1.is_client():
            controller1 = self._get_controller(endpoint1)
            controller1.get_service("ipsec").renew(tunnel)

        if not endpoint2.is_client():
            controller2 = self._get_controller(endpoint2)
            controller2.get_service("ipsec").renew(tunnel)

    def _resolve_endpoint(self, target: str) -> Endpoint:
        address = self._dns_resolver.resolve(target)

        for endpoint in self.get_endpoints():
            for subnet in endpoint.get_subnets():
                if address in subnet.hosts():
                    return endpoint

        raise Exception("Unknown target")

    def async_connect(self, tunnel_description: tunnel_description) -> Tunnel:
        self._logger.info("Async connect tunnel.")

        client = Endpoint.from_proto(tunnel_description.source)
        target = self._resolve_endpoint(tunnel_description.target)
        tunnel = self._make_tunnel(client, target)

        # save tunnel
        self._tunnels.add_edge(client.get_id(), target.get_id(), tunnel=tunnel)

        # install tunnel at switch
        controller2 = self._get_controller(target)
        controller2.get_service("ipsec").new(tunnel)

        # return tunnel for client
        return tunnel

    def _make_tunnel(self, endpoint1: Endpoint, endpoint2: Endpoint) -> Tunnel:
        encryption = AES_CTR()
        authentication = HMAC_MD5()
        connection1 = Connection(urandom(4), encryption, authentication)
        connection2 = Connection(urandom(4), encryption, authentication)

        tunnel = Tunnel(endpoint1, endpoint2, connection1, connection2,
                timedelta(seconds=20), timedelta(seconds=40),
                100, 200)

        return tunnel

    def async_refresh_tunnel(self, tunnel: Tunnel) -> Tunnel:
        self._logger.info("Async refresh tunnel.")

        endpoint1 = tunnel.get_endpoint1()
        endpoint2 = tunnel.get_endpoint2()
        tunnel = self.get_tunnel(endpoint1, endpoint2)

        # create tunnel
        tunnel = self._make_tunnel(endpoint1, endpoint2)
        self._refresh_tunnel(tunnel)

        # return tunnel for client
        return tunnel


    def async_remove_tunnel(self, tunnel: Tunnel) -> None:
        self._logger.info("Async remove tunnel.")

        endpoint1 = tunnel.get_endpoint1()
        endpoint2 = tunnel.get_endpoint2()

        self._logger.info("Disconnect " + str(endpoint1) + " and " + str(endpoint2))

        if not self._tunnels.has_edge(endpoint1.get_id(), endpoint2.get_id()):
            self._logger.warn("Connection does not exist.")
            return

        self._remove_tunnel(tunnel)

    def _refresh_tunnels_for(self, network_id: UUID) -> None:
        for a, b in self._tunnels.edges([ network_id ]):
            tunnel = self._tunnels.get_edge_data(a, b)["tunnel"]
            self._refresh_tunnel(tunnel)

    def add_endpoint(self, endpoint: Endpoint) -> None:
        self._logger.info("New endpoint: " + str(endpoint))
        self._tunnels.add_node(endpoint.get_id(), endpoint=endpoint)

    def _remove_tunnel(self, tunnel: Tunnel) -> None:
        endpoint1 = tunnel.get_endpoint1()
        endpoint2 = tunnel.get_endpoint2()

        if not endpoint1.is_client():
            controller1 = self._get_controller(endpoint1)
            controller1.get_service("ipsec").remove(tunnel)

        if not endpoint2.is_client():
            controller2 = self._get_controller(endpoint2)
            controller2.get_service("ipsec").remove(tunnel)

    def remove_endpoint(self, endpoint: Endpoint) -> None:
        self._logger.info("Remove endpoint: " + str(endpoint))

        # remove tunnels
        for a, b in self._tunnels.edges([ endpoint.get_id() ]):
            tunnel = self._tunnels.get_edge_data(a, b)["tunnel"]
            self._remove_tunnel(tunnel)

        self._tunnels.remove_node(endpoint.get_id())

    def connect(self, endpoint1: Endpoint, endpoint2: Endpoint) -> None:
        assert self._tunnels.has_node(endpoint1.get_id()), "Unknown endpoint"
        assert self._tunnels.has_node(endpoint2.get_id()), "Unknown endpoint"

        # create tunnel
        tunnel = self._make_tunnel(endpoint1, endpoint2)

        # save tunnel
        self.set_tunnel(endpoint1, endpoint2, tunnel)

        # install tunnel
        endpoint1 = tunnel.get_endpoint1()
        endpoint2 = tunnel.get_endpoint2()

        if not endpoint1.is_client():
            controller1 = self._get_controller(endpoint1)
            controller1.get_service("ipsec").new(tunnel)

        if not endpoint2.is_client():
            controller2 = self._get_controller(endpoint2)
            controller2.get_service("ipsec").new(tunnel)

    def set_tunnel(self, endpoint1: Endpoint, endpoint2: Endpoint, tunnel: Tunnel) -> None:
        self._tunnels.add_edge(endpoint1.get_id(), endpoint2.get_id(), tunnel=tunnel)

    def get_tunnel(self, endpoint1: Endpoint, endpoint2: Endpoint) -> Tunnel:
        return self._tunnels.get_edge_data(endpoint1.get_id(), endpoint2.get_id())["tunnel"]

    def disconnect(self, endpoint1: Endpoint, endpoint2: Endpoint) -> None:
        assert self._tunnels.has_node(endpoint1.get_id()), "Unknown endpoint"
        assert self._tunnels.has_node(endpoint2.get_id()), "Unknown endpoint"

        self._logger.info("Disconnect " + str(endpoint1) + " and " + str(endpoint2))

        if self._tunnels.has_edge(endpoint1.get_id(), endpoint2.get_id()):
            self._logger.warn("Connection does not exist.")

        tunnel = self.get_tunnel(endpoint1, endpoint2)
        self._remove_tunnel(tunnel)

    def _get_controller(self, endpoint: Endpoint) -> StubController:
        return self._controller_manager.get_controller(endpoint.get_id())

    def _get_controllers(self, tunnel: Tunnel) -> Tuple[ StubController, StubController ]:
        controller1 = self._get_controller(tunnel.get_endpoint1())
        controller2 = self._get_controller(tunnel.get_endpoint2())

        return controller1, controller2

    def renew(self, tunnel: Tunnel) -> None:
        self._logger.info("Renew IPsec tunnel: " + str(tunnel))
        self.disconnect(tunnel.get_endpoint1(), tunnel.get_endpoint2())
        self.connect(tunnel.get_endpoint1(), tunnel.get_endpoint2())

    def remove(self, tunnel: Tunnel) -> None:
        self._logger.info("Remove IPsec tunnel: " + str(tunnel))
        self.disconnect(tunnel.get_endpoint1(), tunnel.get_endpoint2())
