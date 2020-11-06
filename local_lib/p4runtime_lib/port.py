import nnpy # type: ignore
import struct
from queue import Queue
from threading import Thread, Event

from common_lib.event import EventSystem
from common_lib.logger import Logger
from local_lib.settings import SwitchSettings

from typing import Set

class PortMonitor:

    def __init__(self, logger: Logger, event_system: EventSystem, settings: SwitchSettings):
        self._logger = logger
        self._event_system = event_system
        self._notification_socket = settings.get_notification_socket()

        self._sub = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
        self._on_port_change_handlers = set() # type: Set

        self._teardown = Event()
        self._thread = Thread(target=self.monitor_messages)

    def start(self) -> None:
        #TODO
        #self._logger.debug("Monitoring switch ports", 3)
        #self._teardown.clear()
        #self._connection = self._sub.connect(self._notification_socket)
        #self._sub.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')
        #self._thread.start()
        pass

    def stop(self) -> None:
        #TODO
        #self._logger.debug("Stopping to monitor switch ports", 3)
        #self._teardown.set()
        #self._sub.shutdown(self._connection)
        #self._thread.join()
        pass

    def register_on_change(self, callback) -> None:
        self._on_port_change_handlers.add(callback)

    def unregister_on_change(self, callback) -> None:
        self._on_port_change_handlers.remove(callback)

    def _handle_port_change(self, msg) -> None:

        self._logger.debug(msg, 3)

        msg_type = struct.unpack("4s", msg[:4])

        if msg_type[0] == "PRT|":
            switch_id = struct.unpack("Q", msg[4:12])
            num_statuses = struct.unpack("I", msg[16:20])
            # wir betrachten immer nur den ersten Status
            port, status = struct.unpack("ii", msg[32:40])

            self._logger.debug("Port status change", 3)
            self._logger.debug("Switch ID: " + str(switch_id[0]), 3)
            self._logger.debug("num_statuses: " + str(num_statuses[0]), 3)
            self._logger.debug("port: " + str(port), 3)
            self._logger.debug("status: " + str(status), 3)

            # notify listeners
            for handler in self._on_port_change_handlers:
                handler(switch_id, port, status)

    def monitor_messages(self) -> None:
        while not self._teardown.isSet(): # type: ignore
            msg = self._sub.recv()
            self._event_system.acquire()
            try:
                self._handle_port_change(msg)
            finally:
                self._event_system.release()

