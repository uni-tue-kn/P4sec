from common_lib.event import EventSystem
from common_lib.logger import Logger

from cmd import Cmd
from threading import Thread
from tabulate import tabulate
from typing import Iterable, Optional
from traceback import print_exc
from os.path import expanduser, exists
import readline

class Repl(Cmd):
    histfile_size = 1000

    def __init__(self, controller):
        super().__init__()
        self.prompt = "> "
        self.controller = controller

        self._thread = Thread(target=self.cmdloop)
        self._recording = False
        self._record = ""

    def _get_hist_file(self) -> str:
        return expanduser(self.get_settings().get_data("history_file"))

    def preloop(self):
        if self.get_settings().has("history_file"):
            if readline and exists(self._get_hist_file()):
                readline.read_history_file(self._get_hist_file())

    def postloop(self):
        if self.get_settings().has("history_file"):
            if readline:
                readline.set_history_length(Repl.histfile_size)
                readline.write_history_file(self._get_hist_file())


    #############################################################
    # General                                                  #
    #############################################################

    def record(self):
        self._recording = True

    def flush_record(self):
        self._recording = False
        text = self._record
        self._record = ""
        return text

    def print(self, text: str, **kwargs):
        if self._recording:
            self._record += text + "\n"
        else:
            print(text, **kwargs)

    def list(self, items: Iterable) -> None:
        for item in items:
            self.print("- " + str(item))

    #############################################################
    # Getters                                                  #
    #############################################################
    def get_logger(self) -> Logger:
        return self.controller.logger

    def get_settings(self):
        return self.controller.settings

    def get_event_system(self):
        return self.controller.event_system

    #############################################################
    # Commands                                                 #
    #############################################################

    def do_print_log(self, line):
        self.get_logger().fout.seek(0)
        for line in self.get_logger().fout:
            self.print(self.get_logger().color_log(line.decode("utf8")), end="")

    def do_print_settings(self, line):
        settings = [ [ k, v ] for k, v in vars(self.get_settings()).items() ]
        self.print(tabulate(settings))

    def do_exit(self, line):
        self.get_event_system().stop()
        return True


    #############################################################
    # Hooks                                                    #
    #############################################################

    def onecmd(self, line: str):
        try:
            return super().onecmd(line)
        except Exception as e:
            print_exc()
            self.print(str(e))

    def precmd(self, line):
        self.get_event_system().acquire()
        return line

    def postcmd(self, stop, line):
        self.get_event_system().release()
        return stop

    def start(self):
        self._thread.start()

    def stop(self):
        self._thread.join()

