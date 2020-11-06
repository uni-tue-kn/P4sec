from scapy.all import Ether # type: ignore
from scapy.contrib import lldp # type: ignore
from cryptography.hazmat.primitives.ciphers.aead import AESGCM # type: ignore
from os import urandom
import struct
from uuid import UUID

class LLDPPacket:
    def __init__(self, controller, port):
        self._controller = controller
        self._port = port

    def get_controller(self):
        return self._controller

    def get_port(self):
        return self._port

    def serialize(self):
        controller = lldp.LLDPDUChassisID(id=str.encode(self._controller))
        port = lldp.LLDPDUPortID(id=struct.pack(">H", self._port))
        ttl = lldp.LLDPDUTimeToLive(ttl=6)
        end_of_lldp = lldp.LLDPDUEndOfLLDPDU()

        #add an ether object that the lldp packet can be stringified
        #-> than remove it
        return bytes(Ether() / controller / port / ttl / end_of_lldp)[14:]

class BDDPPacket(LLDPPacket):
    def __init__(self, controller, port, registration_key, sequence):
        LLDPPacket.__init__(self, controller, port)
        self._registration_key = registration_key
        self._sequence = sequence

    def serialize(self):
        lldp_packet = LLDPPacket.serialize(self)

        nonce = urandom(12)
        aesgcm = AESGCM(self._registration_key)
        seq = struct.pack(">i", self._sequence)
        ciphertext = aesgcm.encrypt(nonce, lldp_packet, seq)

        return nonce + seq + ciphertext

    @staticmethod
    def parse(ethernet: Ether, registration_key):
        payload = bytes(ethernet.payload)
        nonce = payload[:12]
        sequence = struct.unpack(">i", payload[12:16])[0]

        #decrypt
        aesgcm = AESGCM(registration_key)
        plaintext = aesgcm.decrypt(nonce, payload[16:], payload[12:16])

        # this is a bit hacky
        # transform to original lldp packet
        ethernet.type = 0x88cc
        ethernet.remove_payload()
        ethernet = ethernet / plaintext

        # reinterpret ethernet packet that scapy does not mess up the type
        # and can read the lldp packet
        ethernet = Ether(bytes(ethernet))

        # replace ethernet payload with plaintext
        controller = UUID(ethernet[lldp.LLDPDUChassisID].id.decode("ascii"))
        port = int(ethernet[lldp.LLDPDUPortID].id.hex(), 16)

        return BDDPPacket(controller, port, registration_key, sequence)

    @staticmethod
    def generate_key() -> bytes:
        return urandom(16)

    def __repr__(self) -> str:
        return "BDDPPacket(controller={controller}, port={port})".format(
                controller=self.get_controller(), port=self.get_port())
