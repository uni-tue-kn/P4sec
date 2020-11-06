#!/usr/bin/env python3

import setup

# client_lib
from client_lib import Client, Settings

# other
from argparse import ArgumentParser

#############################################################
# Define CLI                                               #
#############################################################

parser = ArgumentParser()
parser.add_argument("config", help="Path to configuration file.", type=str)


parser.add_argument("-i", "--interactive", default=False, type=bool)

parser.add_argument("-v", "--verbose", default=False, action="store_const",
        const=True, help="verbose")

#############################################################
# Run client                                               #
#############################################################

args = parser.parse_args()
settings = Settings(args)
client = Client(settings)
client.start()
