# common
from common_lib.logger import Logger

# client
from client_lib.settings import Settings

# other
from os import system
from subprocess import Popen, PIPE
import re
from typing import Optional
from scapy.all import EAPOL, sendp, Ether # type: ignore

class Authenticator:

    def __init__(self, logger: Logger, settings: Settings) -> None:
        self._logger = logger
        self._settings = settings
        self._connected = False
        self._process = None # type: Optional[ Popen ]

    def start(self) -> None:
        self._logger.info("Start Authentication")

        self._process = Popen("wpa_supplicant -i {interface} -c {config} -D wired".format(
            interface=self._settings.get_interface(), config=self._settings.get_wpa_config()),
            shell=True, stdout=PIPE)

        i = 0
        while i < 7:
            line = str(self._process.stdout.readline())
            self._logger.debug(line)
            if re.search("CTRL-EVENT-CONNECTED", line) is not None:
                self._connected = True
                self._logger.info("Successfully authenticated.")
                break
            elif re.search("CTRL-EVENT-DISCONNECTED", line) is not None:
                self._connected = False
            i += 1

    def stop(self) -> None:
        if self._process is not None:
            self._process.kill()
        logoff = Ether(src=self._settings.get_mac()) / EAPOL(type="EAPOL-Logoff")
        sendp(logoff, iface=self._settings.get_interface())
