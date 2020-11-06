# common
from common_lib.services import GeneralService
from common_lib.logger import Logger
from common_lib.controller import Settings
from common_lib.event import EventSystem
from common_lib.ipaddress import Address
from common_lib.credentials import Credentials

# other
from abc import abstractmethod
from grpc import server # type: ignore
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Event
from multiprocessing import cpu_count
from typing import Set

class Server:

    def __init__(self, logger: Logger, event_system: EventSystem, settings: Settings, secure: bool = True):
        self._logger = logger
        self._event_system = event_system
        self._settings = settings
        self.secure = secure

        self._thread = Thread(target=self.run_thread)
        self._event_stopped = Event()
        self._event_started = Event()

        self.services = set() # type: Set

        self.register(GeneralService(event_system))

    def register(self, service) -> None:
        self.services.add(service)

    def run_thread(self) -> None:
        self._logger.debug("Start thread")

        # Create instance
        self.instance = server(ThreadPoolExecutor(max_workers=cpu_count()))
        if self.secure == True:
            self.instance.add_secure_port(str(self.get_address()), \
                    self.get_credentials().get_server_credentials())
        else:
            self.instance.add_insecure_port(str(self.get_address()))

        # Add services to instance
        for service in self.services:
            service.use(self.instance)

        self.instance.start()

        # notify main thread that server is running
        self._event_started.set()
        self._logger.debug("Listening on " + str(self.get_address()))

        # Block until server shutdown
        self._event_stopped.wait()

        self.instance.stop(0)

    def start(self) -> None:
        """ Start the server without blocking. """
        self._logger.debug("Start server.")

        # clear events
        self._event_started.clear()
        self._event_stopped.clear()

        # start thread
        self._thread.start()

        # wait until the server is started
        self._event_started.wait()

    def stop(self) -> None:
        self._logger.debug("Stopping server.")

        # stop server
        self._event_stopped.set()
        self._thread.join()

    def get_address(self) -> str:
        return self._settings.get_address()

    def get_credentials(self) -> Credentials:
        return self._settings.get_credentials()
