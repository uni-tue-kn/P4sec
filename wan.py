#!/usr/bin/env python3
import setup

from argparse import ArgumentParser
from wan_lib import Controller, Settings

parser = ArgumentParser(description="p4sec wan controller.")

parser.add_argument("config", help="Configuration file for the controller.", type=str)
parser.add_argument("-i", "--interactive",
        help="Enter interactive mode.",
        action="store_true", required=False, default=False)

args = parser.parse_args()
settings = Settings(args)

controller = Controller(settings)
controller.start()
