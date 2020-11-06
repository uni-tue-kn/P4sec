#!/usr/bin/env python3

import setup

# global
from global_lib import Controller, Settings

# other
from argparse import ArgumentParser
from os.path import join, dirname

#############################################################
# Parser                                                   #
#############################################################
parser = ArgumentParser(description="global p4macsec controller")

parser.add_argument("config", help="Path to configuration file.", type=str)

parser.add_argument("-i", "--interactive",
        help="Enter interactive mode.",
        action="store_true", required=False, default=False)

args = parser.parse_args()
settings = Settings(args)
controller = Controller(settings)
controller.start()
