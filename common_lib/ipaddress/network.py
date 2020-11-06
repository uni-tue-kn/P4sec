from ipaddress import IPv4Network, IPv6Network
from typing import Union, Set

Network = Union[ IPv4Network, IPv6Network ]
Subnets = Set[ Network ]
