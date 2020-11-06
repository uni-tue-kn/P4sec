# common
from common_lib.logger import Logger
from common_lib.ipsec import Endpoint, Tunnel
from common_lib.event import EventSystem, Task

# client
from client_lib.settings import Settings
from client_lib.wan import WanController
from client_lib.manager.ipsec import IpsecManager
from client_lib.dns_interceptor import DNSInterceptor

# grpc / protobuf
from ipsec_pb2_grpc import NetworkStub # type: ignore
from ipsec_pb2 import tunnel_description # type: ignore

# other
from ipaddress import ip_network, ip_address
from datetime import timedelta
from uuid import uuid1
from typing import Dict
from datetime import datetime


class TunnelManager:

    def __init__(self,
            logger: Logger,
            event_system: EventSystem,
            settings: Settings,
            wan_controller: WanController,
            ipsec_manager: IpsecManager,
            dns_interceptor: DNSInterceptor
        ) -> None:
        self._logger = logger
        self._event_system = event_system
        self._settings = settings
        self._wan_controller = wan_controller
        self._ipsec_manager = ipsec_manager
        self._network = self._wan_controller.get_service("network")
        self._endpoint = Endpoint(
            ip_address("10.0.2.5"),
            uuid1(),
            True,
            set([ ip_network("10.0.2.5/32") ])
        )

        dns_interceptor.on_dns_request(self._handle_dns_request)

        self._tunnels = dict() # type: Dict[ str, Tunnel ]
        self._tasks = dict() # type: Dict[ str, Task ]


    def _handle_dns_request(self, target: str) -> None:
        if not target in self._tunnels:
            tunnel = self.request_tunnel(target)
            self._ipsec_manager.new(tunnel)

    def connect(self) -> None:
        self._logger.info("Connecting.")
        self._network.add_endpoint(self._endpoint)

    def disconnect(self) -> None:
        self._logger.info("Disconnecting.")

        try:
            for target, tunnel in self._tunnels.items():
                self.remove_tunnel(tunnel)

            self._network.remove_endpoint(self._endpoint)
        except:
            self._logger.warn("Could not disconnect from wan controller.")

    def request_tunnel(self, target: str) -> Tunnel:
        self._logger.info("Request tunnel to " + str(target))

        ipsec = self._wan_controller.get_service("ipsec")
        lifetime = timedelta(minutes=1)
        tunnel_desc = tunnel_description(
                lifetime=int(lifetime.total_seconds()),
                source=self._endpoint.to_proto(),
                target=target
        )
        tunnel = Tunnel.from_proto(ipsec.request_tunnel(tunnel_desc))
        self._tunnels[target] = tunnel

        self._tasks[target] = self._event_system.set_timeout(lambda: self.refresh_tunnel(target), 10)

        return tunnel

    def refresh_tunnel(self, target: str) -> None:
        self._logger.info("Refresh tunnel to " + str(target))
        ipsec = self._wan_controller.get_service("ipsec")

        tunnel = self._tunnels[target]
        self._tunnels[target] = Tunnel.from_proto(ipsec.refresh_tunnel(tunnel.to_proto()))

        self._ipsec_manager.renew(tunnel)

        self._tasks[target].set_ready(datetime.timestamp(
            datetime.now() + tunnel.get_soft_time_limit()))

    def remove_tunnel(self, tunnel: Tunnel) -> None:
        ipsec = self._wan_controller.get_service("ipsec")
        try:
            ipsec.remove_tunnel(tunnel.to_proto())
        except:
            pass
        self._ipsec_manager.remove(tunnel)
