# P4Sec Prototype

P4sec uses SDN technologies in form of P4 to provide a basic high speed protection layer.
It uses IPsec to secure WAN connections and allow roadwarrior clients to access the local network.
Ethernet traffic within a network is secured with MACsec and 802.1X is used for authentication.
The goal is to provide a basic security mechanism for networks such that all traffic is protected against an intruder which has physical access to any part of the network.

## Prerequisites

1. The development environment is based on vagrant.
	To set it up install [vagrant](https://www.vagrantup.com/)
	and start the environment with `vagrant up`.

2. If you want to deploy the prototype you must run the follwoing scripts
	to install all dependencies.
	Note that P4sec is only supported by Ubuntu 16.04.

```
./dependencies/root-bootstrap.sh
./dependencies/libyang-sysrepo.sh
./dependencies/user-bootstrap.sh
```

## Compilation

To compile the module run `make`.
This will create a `build` folder with all the compiled p4, proto and externs.

## Run the example

You can find an example under `example`, which can be executed by:
```
sudo ./run.py
```

This will start mininet, bmv2, etc.

The P4sec environment is a three tier environment consisting of a local controller, global controller and WAN controller.
Every local controller has a global controller and every global controller has a WAN controller.
The local controller manages a switch. It provides an API to write MACsec, IPsec etc. rules to the switch.
In contrast to that the global controller manages the relation between the switches (local controllers) in a site, which is a collection of switches that are directly connected to
each other.
Furthermore, the WAN controller manages the relations between each site and thus forwards the tunnel configuration to each global controller, which in turn passes
these information to the local controllers which are connected to the outside (internet).

Each controller has a similar interface. It takes a path to its configuration as an
argument. By providing the `-i` flag to the controller, it will start a REPL
where the user can interact with the controller (e.g. write connect sites).

Therefore to start the application we first have to start the wan controller.
You must first start the WAN controller, then the global controller and then the local controller, because every global controller must register at the WAN controller and
every local controller must register at the WAN controller.

Start the WAN controller:
```
./wan.py example/wan-config.json
```
To connect sites the WAN controller should be started in the interactive mode:
```
./wan.py example/wan-config.json -i
```

Then the global controllers can be started.
In this example we start only two global controller since the example has only two sites.
If you have more sites, you must modify the config accordingly and copy it to each of your
sites and start a global controller there.
```
./global.py example/g1-config.json
./global.py example/g2-config.json
```

At last the local controllers must be started.
```
./local.py example/l1-config.json
./local.py example/l2-config.json
./local.py example/l3-config.json
...
```

By entering connect in the WAN controller REPL you can now connect sites with
each other e.g:
```
connect 10.0.1.254 10.0.2.254
```
You can disconnect them by running
```
disconnect 10.0.1.254 10.0.2.254
```

## Structure of the Repository

The repository is structured as follows

| Directory    | Description                                                       |
|--------------|-------------------------------------------------------------------|
| client_lib   | Source code concerting the roadwarrior client                     |
| global_lib   | Source code concerting the global controller                      |
| local_lib    | Source code concerting the local controller                       |
| wan_lib      | Source code concerting the wan controller                         |
| common_lib   | Code that is shared with other libs like client_lib, wan_lib, ... |
| dependencies | Install scripts for all dependencies.                             |
| extern       | Source code for custom externs which are used by the bmv2         |
| p4           | All p4 programs.                                                  |
| protos       | Definitions of all protobuf messages.                             |
| example      | Example setup of P4sec. (topology, switches, hosts, ...)          |
| docs         | Documentation                                                     |

The programs `local.py`, `global.py`, `wan.py` and `client.py`
can be used to start the local, global, wan controller and the client

## About this project
This project is based on [P4-IPsec](https://github.com/uni-tue-kn/p4-ipsec) and [P4-MACsec](https://github.com/uni-tue-kn/p4-macsec).  
We thank [Arwed Mett](https://github.com/Pfeifenjoy) for his help.
