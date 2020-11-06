# common
from common_lib.ipsec import Endpoint, Tunnel
from common_lib.logger import Logger
from common_lib.manager import ControllerManager
from common_lib.stub import StubController
from common_lib.ipaddress import Network
from common_lib.event import EventSystem

# global
from global_lib.local import LocalController
from global_lib.wan import WanController
from global_lib.manager import RoutingManager
from global_lib.settings import Settings

# other
from typing import cast, Dict
from uuid import UUID

class IpsecManager:
    """ Global Ipsec manager which forwards all tunnels to the local ipsec manager. """

    def __init__(self,
            logger: Logger,
            settings: Settings,
            wan_controller: WanController,
            controller_manager: ControllerManager,
            routing_manager: RoutingManager
        ) -> None:
        self._logger = logger
        self._settings = settings
        self._wan_controller = wan_controller
        self._controller_manager = controller_manager
        self._routing_manager = routing_manager

        self._controller_manager.listen_new_controller(self._handle_new_controller)
        self._controller_manager.listen_remove_controller(self._handle_remove_controller)

        self._endpoints = dict() # type: Dict[ UUID, StubController ]

    def get_concentrators(self):
        return [ controller for controller in self._controller_manager.get_controllers()
                if controller.is_concentrator() ]

    def _update_subnets(self, concentrator: StubController, tunnel: Tunnel) -> None:
        if tunnel.get_endpoint1().get_address() == concentrator.get_address():
            for subnet in tunnel.get_endpoint1().get_subnets():
                self._routing_manager.add_subnet_silent(concentrator.get_id(), subnet)
        else:
            for subnet in tunnel.get_endpoint2().get_subnets():
                self._routing_manager.add_subnet_silent(concentrator.get_id(), subnet)

    def new(self, tunnel: Tunnel):
        # forward to all concentrators
        for concentrator in self.get_concentrators():
            concentrator.get_service("ipsec").new(tunnel)
            self._update_subnets(concentrator, tunnel)

    def renew(self, tunnel: Tunnel):
        # forward to all concentrators
        for concentrator in self.get_concentrators():
            concentrator.get_service("ipsec").renew(tunnel)
            self._update_subnets(concentrator, tunnel)

    def remove(self, tunnel: Tunnel):
        # forward to all concentrators
        for concentrator in self.get_concentrators():
            concentrator.get_service("ipsec").remove(tunnel)

    def _get_endpoint(self):
        return Endpoint(
                self._settings.get_site_address(),
                self._wan_controller.get_service("registration").get_id(),
                False,
                self._routing_manager.get_all_subnets()
            )

    def _add_endpoint(self, endpoint: StubController) -> None:
        assert endpoint.get_id() not in self._endpoints, "Duplicate endpoint with same id."
        self._endpoints[endpoint.get_id()] = endpoint

        endpoint.get_service("concentrator").set_ip(self._get_endpoint().get_address())

        if len(self._endpoints.items()) == 1:
            self._wan_controller.get_service("network").add_endpoint(self._get_endpoint())

    def _remove_endpoint(self, endpoint: StubController) -> None:
        del self._endpoints[endpoint.get_id()]

        if len(self._endpoints.items()) == 0:
            self._wan_controller.get_service("network").remove_endpoint(self._get_endpoint())

    def _handle_new_controller(self, controller: StubController):
        controller = cast(LocalController, controller)
        if controller.is_concentrator():
            self._add_endpoint(controller)

    def _handle_remove_controller(self, controller: StubController):
        self._logger.debug("handle remove controller -> remove endpoint")
        controller = cast(LocalController, controller)
        if controller.is_concentrator():
            self._remove_endpoint(controller)

