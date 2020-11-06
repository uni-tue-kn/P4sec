from __future__ import print_function
import re
from sys import stderr, stdout
from termcolor import colored

class Logger:

    def __init__(self, fout=stdout, ferror=stderr):
        # Default output streams
        self.fout = fout
        self.ferror = ferror

    def set_output(self, stream):
        """ Define an output stream. """
        self.fout = stream

    def set_error(self, stream):
        """ Define global error output stream. """
        self.ferror = stream

    def log(self, text, stream=None, tag=None, tag_color=None):
        """ Print text to the global output stream. """
        if stream == None:
            stream = self.fout

        if tag != None:
            offset = 8 - len(tag) #Maximum tag length is 8 - 2 brackets = 6
            if stream.isatty():
                tag = colored(tag, tag_color)
            text = "[" + tag + "]" + (offset * " ") + str(text)

        if stream.isatty():
            print(text, file=stream)
        else:
            stream.write((text + "\n").encode("utf8"))


    def info(self, text):
        self.log(text, tag="INFO", tag_color="blue")

    def error(self, text):
        self.log(text, self.ferror, tag="ERROR", tag_color="red")

    def warn(self, text):
        self.log(text, tag="WARN", tag_color="yellow")

    def debug(self, text, level=0):
        self.log(text, tag="DEBUG", tag_color="green")

    def color_log(self, text):
        text = re.sub("^\\[ERROR\\]", "[" + colored("ERROR", "red") + "]", text)
        text = re.sub("^\\[WARN\\]", "[" + colored("WARN", "yellow") + "]", text)
        text = re.sub("^\\[INFO\\]", "[" + colored("INFO", "blue") + "]", text)
        text = re.sub("^\\[DEBUG\\]", "[" + colored("DEBUG", "green") + "]", text)
        return text
