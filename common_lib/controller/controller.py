from abc import abstractmethod

# common
from common_lib.logger import Logger
from common_lib.credentials import Credentials
from common_lib.event import EventSystem
from common_lib.repl import Repl

# other
from tempfile import TemporaryFile
from uuid import UUID

class Controller:
    """
    Generic class of a controller which provides basic controller functionality,
    such as logging and instantiating the server and a repl.
    """

    def __init__(self, repl: Repl, interactive: bool):
        # Properties
        self.repl = repl
        self._interactive = interactive

        self.logger = Logger(TemporaryFile(), TemporaryFile()) if interactive else Logger()
        self.event_system = EventSystem(self.logger)

    def start(self) -> None:
        self.prepare()

        if self._interactive:
            self.repl.start()

        try:
            self.event_system.run()
        except KeyboardInterrupt:
            # -> continue
            pass
        except Exception as e:
            self.logger.error("Unexpected exception occured: " + str(e))

        if self._interactive:
            self.repl.stop()

        self.shutdown()

    @abstractmethod
    def prepare(self) -> None:
        """ Hook which is used to set up the server before it is started. """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """ Hook which is used to clean up the server before it is stopped. """
        pass
