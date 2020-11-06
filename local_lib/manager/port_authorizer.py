# common
from common_lib.logger import Logger
from common_lib.event import EventSystem

# local
from local_lib.p4runtime_lib import SwitchConnection
from local_lib.settings import Settings

# other
from typing import Dict, Set

class PortController:

    def __init__(self, switch_connection: SwitchConnection, prefix: str) -> None:
        self._switch_connection = switch_connection
        self._prefix = prefix

    def get_prefix(self) -> str:
        return self._prefix

    def resolve(self, path: str) -> str:
        return self.get_prefix() + "." + path

    def add_auto_authorize(self, port: int, mac: str) -> None:
        self._switch_connection.write(
            table_name=self.resolve("auto_authorizations"),
            match_fields={
                "port": port,
                "mac": mac
            },
            action_name=self.resolve("grant_access")
        )

    def remove_auto_authorize(self, port: int, mac: str) -> None:
        self._switch_connection.delete(
            table_name=self.resolve("auto_authorizations"),
            match_fields={
                "port": port,
                "mac": mac
            }
        )

    def add_force_authorize(self, port: int) -> None:
        self._switch_connection.write(
            table_name=self.resolve("forced_authorizations"),
            match_fields={
                "port": port
            },
            action_name=self.resolve("grant_access")
        )

    def remove_force_authorize(self, port: int) -> None:
        self._switch_connection.delete(
            table_name=self.resolve("forced_authorizations"),
            match_fields={
                "port": port
            }
        )

    def add_force_unauthorize(self, port: int) -> None:
        self._switch_connection.write(
            table_name=self.resolve("forced_unauthorizations"),
            match_fields={
                "port": port
            },
            action_name=self.resolve("grant_access")
        )

    def remove_force_unauthorize(self, port: int) -> None:
        self._switch_connection.delete(
            table_name=self.resolve("forced_unauthorizations"),
            match_fields={
                "port": port
            }
        )

class PortAuthorizer:

    def __init__(self,
            logger: Logger,
            settings: Settings,
            event_system: EventSystem,
            switch_connection: SwitchConnection
        ) -> None:
        self._logger = logger
        self._settings = settings
        self._event_system = event_system
        self._switch_connection = switch_connection

        self._port_mapping = dict() # type: Dict[ str, int ]

        self._force_authorized_ports = set() # type: Set[ int ]
        self._force_unauthorized_ports = set() # type: Set[ int ]

        self._in_port_controller = PortController(self._switch_connection,
                "ingress.in_port_authorizer")
        self._out_port_controller = PortController(self._switch_connection,
                "ingress.out_port_authorizer")

    def authorize(self, port: int, mac: str) -> None:
        self._logger.info("Grant access for port " + str(port) + " to " + mac)

        if mac in self._port_mapping.items():
            self.unauthorize(self._port_mapping[mac], mac)

        self._in_port_controller.add_auto_authorize(port, mac)
        self._in_port_controller.add_auto_authorize(port, self._settings.get_mac())
        self._out_port_controller.add_auto_authorize(port, mac)
        self._out_port_controller.add_auto_authorize(port, "ff:ff:ff:ff:ff:ff")

        self._port_mapping[mac] = port

    def unauthorize(self, port: int, mac: str) -> None:
        assert mac in self._port_mapping, "Cannot remove unknown port access"
        port = self._port_mapping[mac]

        self._logger.info("Revoke access for port " + str(port) + " to " + mac)

        self._in_port_controller.remove_auto_authorize(port, mac)
        self._in_port_controller.remove_auto_authorize(port, self._settings.get_mac())
        self._out_port_controller.remove_auto_authorize(port, mac)
        self._out_port_controller.remove_auto_authorize(port, "ff:ff:ff:ff:ff:ff")

        del self._port_mapping[mac]

    def get_port_mapping(self) -> Dict[ str, int ]:
        return self._port_mapping

    def force_authorization(self, port: int) -> None:
        self._logger.info("Force access for port " + str(port))

        self._in_port_controller.add_force_authorize(port)
        self._out_port_controller.add_force_authorize(port)

        self._force_authorized_ports.add(port)

    def unforce_authorization(self, port: int) -> None:
        self._logger.info("Revoke access for port " + str(port))

        self._in_port_controller.remove_force_authorize(port)
        self._out_port_controller.remove_force_authorize(port)

        self._force_authorized_ports.remove(port)

    def force_unauthorization(self, port: int) -> None:
        self._logger.info("Block port " + str(port))

        self._in_port_controller.add_force_unauthorize(port)
        self._out_port_controller.add_force_unauthorize(port)

        self._force_unauthorized_ports.add(port)

    def unforce_unauthorization(self, port: int) -> None:
        self._logger.info("Unblock port " + str(port))

        self._in_port_controller.remove_force_unauthorize(port)
        self._out_port_controller.remove_force_unauthorize(port)

        self._force_unauthorized_ports.remove(port)

    def initialize(self) -> None:
        for port in self._settings.get_extern_ports():
            self.force_authorization(port)

    def cleanup(self) -> None:
        for port in self._force_authorized_ports.copy():
            self.unforce_authorization(port)
        for port in self._force_unauthorized_ports.copy():
            self.unforce_unauthorization(port)
