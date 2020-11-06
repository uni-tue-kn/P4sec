# common
from common_lib.logger import Logger

# local
from local_lib.manager.port_authorizer import PortAuthorizer
from local_lib.packet.cpu import CPUPacket
from local_lib.p4runtime_lib import SwitchConnection
from local_lib.settings import Settings, RadiusAuthorizationSettings

# other
from scapy.all import Ether, EAPOL, EAP, eapol_versions, eap_types, Radius, RadiusAttribute, UDP, IP # type: ignore
from typing import Set, Dict, cast, Optional, List
from hashlib import md5
from os import urandom
from ipaddress import ip_address
import hmac
from socket import socket, AF_INET, SOCK_DGRAM
from time import time
from collections import defaultdict

class Supplicant:

    def __init__(self,
            switch_connection: SwitchConnection,
            port: int,
            mac: str
        ) -> None:
        self._switch_connection = switch_connection
        self._created = int(time())
        self._active = True
        self._authorized = False
        self._port = port
        self._mac = mac
        self._identity = None # type: Optional[ str ]
        self._request = None # type: Optional[ EAP ]
        self._request_id = urandom(1)[0]
        self._state = None # type: Optional[ RadiusAttribute ]

    def _create_request_id(self) -> int:
        self._request_id = (self._request_id + 1) % 255
        return self._request_id

    def get_created(self) -> int:
        return self._created

    def destroy(self) -> None:
        self._active = False

    def get_authorized(self) -> bool:
        return self._authorized

    def is_active(self) -> bool:
        return self._active

    def get_port(self) -> int:
        return self._port

    def get_mac(self) -> str:
        return self._mac

    def send(self, eap: EAP) -> None:
        ether = Ether(dst=self.get_mac())
        eapol = EAPOL(version=eapol_versions[0x2], type=EAPOL.EAP_PACKET)

        if eap.code == EAP.REQUEST:
            self._request = eap

        self._switch_connection.send(ether / eapol / eap, self.get_port())

    def send_failure(self) -> None:
        self._authorized = False
        self.send(EAP(code="Failure", id=self._create_request_id()))

    def send_success(self) -> None:
        self._authorized = True
        self.send(EAP(code="Success", id=self._create_request_id()))

    def request(self, *args, **kwargs) -> None:
        eap = EAP(code="Request", id = self._create_request_id(), *args, **kwargs)
        self.send(eap)

    def answer(self, response: EAP) -> None:
        assert response.code is EAP.RESPONSE, "Only eap responses allowed."
        if response.answers(self._request):
            self._request = None
        else:
            raise Exception("Unexpected EAP response.")

    def set_identity(self, identity: str) -> None:
        self._identity = identity

    def get_identity(self) -> Optional[ str ]:
        return self._identity

    def set_state(self, state: RadiusAttribute) -> None:
        self._state = state

    def get_state(self) -> Optional[ RadiusAttribute ]:
        return self._state

    def __str__(self) -> str:
        return "Supplicant(" + \
                "mac=" + str(self.get_mac()) + \
                ", port=" + str(self.get_port()) + \
                ", authorized=" + str(self.get_authorized()) + \
                ")"

class RadiusServer:

    def __init__(self, logger: Logger, settings: Settings) -> None:
        self._logger = logger
        self._settings = cast(RadiusAuthorizationSettings, settings.get_port_authorization())
        self._socket = socket(AF_INET, SOCK_DGRAM)
        self._socket.settimeout(2)
        self._id_count = urandom(1)[0]

    def _create_id(self) -> int:
        self._id_count = (self._id_count + 1) % 255
        return self._id_count

    def request(self, attributes: List[ RadiusAttribute ]) -> Radius:
        # make radius request (https://tools.ietf.org/html/rfc2865)
        radius = Radius(
            code="Access-Request",
            id=self._create_id(),
            authenticator = urandom(16),
            attributes = attributes + [
                RadiusAttribute(type="NAS-IP-Address", value=ip_address("127.0.0.1").packed),
                RadiusAttribute(type="Message-Authenticator", value=bytes([0] * 16))
            ]
        )

        # calculate message authenticator (https://tools.ietf.org/html/rfc3579#page-16)
        radius.attributes[-1] = RadiusAttribute(type="Message-Authenticator",
                value=hmac.new(self._settings.get_secret(), bytes(radius)).digest())

        return self.send(radius)

    def _get_message_authenticator(self, packet: Radius) -> RadiusAttribute:
        for attribute in packet.attributes:
            if attribute.type == RadiusAttribute(type="Message-Authenticator").type:
                return attribute
        raise Exception("No Message Authenticator specified.")

    def send(self, request: Radius) -> Radius:
        self._logger.debug("Send radius " + repr(request) + " to "
                + str(self._settings.get_ip()) + ":" + str(self._settings.get_port()))
        self._socket.sendto(bytes(request),
                (self._settings.get_ip(), self._settings.get_port()))

        # receive response from RADIUS server
        data, server = self._socket.recvfrom(4096)
        response = Radius(data)
        self._logger.debug("Received radius " + repr(response)
                + " from " + str(self._settings.get_ip()) + ":"
                + str(self._settings.get_port()))

        # check message authenticator value
        message_authenticator = self._get_message_authenticator(response)
        old_message_authenticator_value = message_authenticator.value
        old_authenticator = response.authenticator
        message_authenticator.value = bytes([ 0 ] * 16)
        response.authenticator = request.authenticator
        # calculate expected value
        expected_value = hmac.new(self._settings.get_secret(), bytes(response)).digest()
        # reset modified values
        response.authenticator = old_authenticator
        message_authenticator.value = old_message_authenticator_value

        if expected_value != old_message_authenticator_value:
            raise Exception("Radius server message authenticator is incorrect.")

        return response


class SupplicantManager:

    def __init__(self,
            switch_connection: SwitchConnection
        ) -> None:
        self._switch_connection = switch_connection
        self._supplicants = defaultdict(lambda: { }) # type: Dict[ int, Dict[str, Supplicant] ]

    def create(self, cpu: CPUPacket) -> Supplicant:
        supplicant = Supplicant(self._switch_connection, cpu.port, cpu.payload.payload.src)
        self._supplicants[supplicant.get_port()][supplicant.get_mac()] = supplicant
        return supplicant

    def get(self, cpu: CPUPacket) -> Supplicant:
        return self._supplicants[cpu.port][cpu.payload.payload.src]

    def destroy(self, supplicant: Supplicant) -> None:
        del self._supplicants[supplicant.get_port()][supplicant.get_mac()]
        supplicant.destroy()

    def get_all(self) -> List[ Supplicant ]:
        return [ supplicant for port, supplicants in self._supplicants.items()
                for mac, supplicant in supplicants.items() ]

    def __getitem__(self, key: int) -> Dict[ str, Supplicant ]:
        return self._supplicants[key]

class Authenticator:

    def __init__(self,
            logger: Logger,
            settings: Settings,
            switch_connection: SwitchConnection,
            port_authorizer: PortAuthorizer
        ) -> None:
        self._logger = logger
        self._settings = settings
        self._port_authorizer = port_authorizer

        self._radius_server = RadiusServer(logger, settings)
        self._supplicant_manager = SupplicantManager(switch_connection)

    def get_supplicant_manager(self) -> SupplicantManager:
        return self._supplicant_manager

    def _get_eap_from_radius(self, radius: Radius) -> List[ EAP ]:
        return [ attribute.value for attribute in radius.attributes
                if attribute.name == "EAP-Message" ]

    def _handle_identity(self, cpu: CPUPacket) -> None:
        eap = cpu.payload.payload.payload
        supplicant = self._supplicant_manager.get(cpu)
        supplicant.set_identity(eap.identity)
        self._logger.debug("new identity " + str(eap.identity) + " for " + str(supplicant))

    def _forward_to_radius(self, cpu: CPUPacket) -> None:
        self._logger.debug("Forward eap packet to radius server.")

        # forward eap to radius
        supplicant = self._supplicant_manager.get(cpu)
        response = self._radius_server.request( 
            ([ RadiusAttribute(type="User-Name", value=supplicant.get_identity()) ]
            if supplicant.get_identity() != None else [ ])
            + ([ supplicant.get_state() ] if supplicant.get_state() != None else [ ])
            + [
                RadiusAttribute(type="NAS-Port", value=cpu.port.to_bytes(4, byteorder="big")),
                RadiusAttribute(type="EAP-Message", value=bytes(cpu.payload.payload.payload.payload))
            ]
        )

        if response.code == Radius(code="Access-Reject").code:
            self._port_authorizer.unauthorize(supplicant.get_port(), supplicant.get_mac())
        elif response.code == Radius(code="Access-Accept").code:
            self._port_authorizer.authorize(supplicant.get_port(), supplicant.get_mac())
        else:
            for attribute in response.attributes:
                if attribute.type == RadiusAttribute(type="State").type:
                    supplicant.set_state(attribute)
                    break

        # forward eap to supplicant
        for eap in self._get_eap_from_radius(response):
            #print(eap.attributes)
            supplicant.send(eap)

    def _handle_response(self, cpu: CPUPacket) -> None:
        eap = cpu.payload.payload.payload.payload

        if eap_types[eap.type] == "Identity":
            self._handle_identity(cpu)

        self._forward_to_radius(cpu)

    def _handle_start(self, cpu: CPUPacket) -> None:
        supplicant = self._supplicant_manager.create(cpu)
        supplicant.request(type="Identity")

    def _handle_packet(self, cpu: CPUPacket) -> None:
        eap = cpu.payload.payload.payload.payload

        if eap.code == EAP.RESPONSE:
            self._handle_response(cpu)
        else:
            self._logger.warn("Discarding unexpected eap packet.")

    def _handle_logoff(self, cpu: CPUPacket) -> None:
        supplicant = self._supplicant_manager.get(cpu)
        self._port_authorizer.unauthorize(supplicant.get_port(), supplicant.get_mac())
        self._supplicant_manager.destroy(supplicant)

    def handle_eapol(self, cpu: CPUPacket) -> None:
        eapol = cpu.payload.payload.payload
        port = cpu.port
        self._logger.debug("Received " + str(eapol.summary()) + " on port " + str(port), 2)

        if eapol.type == EAPOL.START:
            self._handle_start(cpu)
        elif eapol.type == EAPOL.EAP_PACKET:
            self._handle_packet(cpu)
        elif eapol.type == EAPOL.LOGOFF:
            self._handle_logoff(cpu)


