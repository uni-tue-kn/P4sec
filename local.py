#!/usr/bin/env python3

import setup

from local_lib import Controller, Settings

# Other
from argparse import ArgumentParser
from os.path import join, dirname

parser = ArgumentParser(description="local p4macsec controller")

parser.add_argument("config", help="Path to the configuration file.", type=str)

parser.add_argument("-i", "--interactive",
        help="Enter interactive mode.",
        action="store_true", required=False, default=False)

args = parser.parse_args()

settings = Settings(args)
controller = Controller(settings)

controller.start()
