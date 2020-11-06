#!/usr/bin/env python3

from os import system, devnull
from json import load
from typing import Set, Union, Optional, Dict, List
from os.path import join, dirname, splitext, expanduser, exists
from ipaddress import IPv4Address, ip_address
import logging
from cmd import Cmd
from subprocess import Popen
from networkx import Graph # type: ignore
from time import sleep
import tempfile
import readline
import re

class Settings:

    def __init__(self, path: str) -> None:
        self._data = load(open(path))

    def get_data(self):
        return self._data

    def get_hosts(self):
        return self._data["hosts"] if "hosts" in self._data else [ ]

    def get_switches(self):
        return self._data["switches"] if "switches" in self._data else [ ]

    def get_log_level(self) -> int:
        if not "log_level" in self._data:
            return logging.INFO

        if self._data["log_level"] == "DEBUG":
            return logging.DEBUG
        elif self._data["log_level"] == "INFO":
            return logging.INFO
        elif self._data["log_level"] == "CRITICAL":
            return logging.CRITICAL
        elif self._data["log_level"] == "WARNING":
            return logging.WARNING
        elif self._data["log_level"] == "ERROR":
            return logging.ERROR

        raise Exception("Unknown log level {level}".format(self._data["log_level"]))

class Host:

    def __init__(self, config) -> None:
        self._config = config

    def get_name(self) -> str:
        return self._config["name"]

    def get_ip(self) -> IPv4Address:
        return ip_address(self._config["ip"])

    def get_mac(self) -> Optional[ str ]:
        return self._config["mac"] if "mac" in self._config else None

    def set_gateway(self, gateway: str) -> None:
        command = "ip route add {gateway} dev {host}-eth0".format(
                gateway=gateway, host=self.get_name())
        status = self.run_command(command)

        if status != 0:
            raise Exception("Could not set gateway for {host}".format(host=self))

        command = "ip route add default via {gateway} dev {host}-eth0".format(
                gateway=gateway, host=self.get_name())
        status = self.run_command(command)

        if status != 0:
            raise Exception("Could not set gateway for {host}".format(host=self))


        if status != 0:
            raise Exception("Could not set gateway for {host}".format(host=self))


    def run_command(self, command: str) -> int:
        logging.debug("Running \"{command}\" on {host}"
                .format(command=command, host=self.get_name()))
        return system("ip netns exec {host} {command}"
                .format(host=self.get_name(), command=command))

    def create(self) -> None:
        logging.debug("Create " + repr(self))

        status = system("ip netns add {name}".format(name=self.get_name()))

        if status != 0:
            raise Exception("Could not create {host}".format(host=self))

        status = system("ip link add {host}-eth0 type veth peer name {host}"
                .format(host=self.get_name()))

        if status != 0:
            raise Exception("Could not create {host}".format(host=self))

        status = system("ip link set {host}-eth0 netns {host}".format(host=self.get_name()))

        if status != 0:
            raise Exception("Could not create {host}".format(host=self))

        status = self.run_command("ip link set {host}-eth0 up".format(host=self.get_name()))

        if status != 0:
            raise Exception("Could not create {host}".format(host=self))

        status = self.run_command("ip link set lo up")

        if status != 0:
            raise Exception("Could not create {host}".format(host=self))

        status = system("ip link set {host} up".format(host=self.get_name()))

        if status != 0:
            raise Exception("Could not create {host}".format(host=self))

        status = self.run_command("ip a add {ip}/24 dev {host}-eth0".format(ip=self.get_ip(), host=self.get_name()))

        if status != 0:
            raise Exception("Could not create {host}".format(host=self))

        if self.get_mac() != None:
            command = "ip link set dev {host}-eth0 address {mac}".format(
                    host=self.get_name(), mac=self.get_mac())
            status = self.run_command(command)
            if status != 0:
                raise Exception("Could not create {host}".format(host=self))

        status = self.run_command("ip -6 a flush {host}-eth0".format(host=self.get_name()))
        if status != 0:
            raise Exception("Could not create {host}".format(host=self))

    def destroy(self) -> None:
        logging.debug("Destroy " + repr(self))

        status = system("ip netns del {name}".format(name=self.get_name()))

        if status != 0:
            raise Exception("Could not destroy {host}".format(host=self))

        status = system("ip link del {host}"
                .format(host=self.get_name()))

        if status != 0:
            raise Exception("Could not destroy {host}".format(host=self))

    def __repr__(self) -> str:
        return "Host(name={name}, ip={ip})".format(name=self.get_name(), ip=self.get_ip())

class Switch:

    def __init__(self, config) -> None:
        self._config = config
        self._ports = dict() # type: Dict[ int, str ]
        self._pid = None # type: Optional[ int ]
        self._log = tempfile.NamedTemporaryFile(
                prefix="log-{name}-".format(name=self.get_name()),
                suffix=".txt")

    def get_name(self) -> str:
        return self._config["name"]

    def set_port(self, number: int, interface: str) -> None:
        self._ports[number] = interface

    def get_gateway(self) -> str:
        return self._config["gateway"]

    def _get_interface_mapping(self) -> str:
        return " ".join([ "-i {number}@{interface}".format(number=number,
            interface=interface) for number, interface in self._ports.items() ])

    def _get_modules(self) -> str:
        return "../build/externs/libp4ipsec.so,../build/externs/libp4macsec.so"

    def start(self) -> None:
        logging.info("Starting switch {switch}. (grpc-port: {grpc}, thrift-port: {thrift})"
                .format(switch=self.get_name(), grpc=self._config["grpc"],
                    thrift=self._config["thrift"]))
        logging.info("Port mapping:")
        for number, interface in self._ports.items():
            logging.info("\t{number} -> {interface}".format(number=number, interface=interface))

        command = "simple_switch_grpc {interfaces} --thrift-port {thrift} --device-id {id} --log-file {log} ../build/p4c/basic.json -- --grpc-server-addr 0.0.0.0:{grpc} --cpu-port 16 --load-modules {modules}".format(
                        interfaces=self._get_interface_mapping(),
                        thrift=self._config["thrift"],
                        id=self._config["id"],
                        grpc=self._config["grpc"],
                        modules=self._get_modules(),
                        log=splitext(self._log.name)[0]
                    )
        logging.debug(command)

        with tempfile.NamedTemporaryFile() as f:
            system(command + " > /dev/null 2>&1 & echo $! >> " + f.name)
            self._pid = int(f.read())

    def stop(self) -> None:
        if not self._pid is None:
            system("kill -9 {pid}".format(pid=self._pid))
        self._log.close()

    def __repr__(self) -> str:
        return "Switch(name={name})".format(name=self.get_name())

class Topology:

    def __init__(self, settings) -> None:
        self._config = settings.get_data()

        self._hosts = dict() # type: Dict[ str, Host ]
        self._switches = dict() # type: Dict[ str, Switch ]

        self._connections = Graph()

    def get_host(self, host: str) -> Host:
        return self._hosts[host]

    def get_switches(self) -> List[ Switch ]:
        return [ switch for name, switch in self._switches.items() ]

    def create(self) -> None:
        # create hosts
        for host_config in self._config["hosts"]:
            self._hosts[host_config["name"]] = Host(host_config)
        for name, host in self._hosts.items():
            host.create()

        # create switches
        for switch_config in self._config["switches"]:
            self._switches[switch_config["name"]] = Switch(switch_config)

        # create connections
        for link_config in self._config["links"]:
            left = link_config[0]
            right = link_config[1]
            self._connections.add_edge(left, right)

        # create connections between switches
        for connection in self._connections.edges():
            if connection[0] in self._switches and connection[1] in self._switches:
                logging.debug("Create connection: {left}-{right}"
                        .format(left=connection[0], right=connection[1]))

                status = system("ip link add {left}-{right} type veth peer name {right}-{left}"
                        .format(left=connection[0], right=connection[1]))
                if status != 0:
                    raise Exception("Could not create connection between {left} and {right}"
                        .format(left=connection[0], right=connection[1]))

                status = system("ip link set {left}-{right} up"
                        .format(left=connection[0], right=connection[1]))
                if status != 0:
                    raise Exception("Could not create connection between {left} and {right}"
                        .format(left=connection[0], right=connection[1]))

                status = system("ip link set {right}-{left} up"
                        .format(left=connection[0], right=connection[1]))
                if status != 0:
                    raise Exception("Could not create connection between {right} and {left}"
                        .format(left=connection[0], right=connection[1]))

        # connect switches
        for switch_name, switch in self._switches.items():
            port = 1

            hosts = sorted([ self._hosts[neighbor] for neighbor in self._connections.neighbors(switch_name)
                if neighbor in self._hosts ], key=lambda host : host.get_name())
            switches = sorted([ self._switches[neighbor] for neighbor in self._connections.neighbors(switch_name)
                    if neighbor in self._switches ], key=lambda switch : switch.get_name())

            for host in hosts:
                # connect to host
                switch.set_port(port, host.get_name())
                host.set_gateway(switch.get_gateway())
                port += 1

            for switch in switches:
                # create connection
                self._switches[switch_name].set_port(port,
                        "{left}-{right}".format(left=switch_name, right=switch.get_name()))
                port += 1


    def destroy(self) -> None:
        for connection in self._connections.edges():
            if connection[0] in self._switches and connection[1] in self._switches:
                logging.debug("Remove connection: {left}-{right}".format(left=connection[0],
                    right=connection[1]))
                system("ip link del {left}-{right}".format(left=connection[0],
                    right=connection[1]))

        for name, host in self._hosts.items():
            host.destroy()

class Simulator:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._topology = Topology(settings)
        self._processes = set() # type: Set[ Popen ]

    def _start_switches(self) -> None:
        for switch in self._topology.get_switches():
            switch.start()

    def _stop_switches(self) -> None:
        for switch in self._topology.get_switches():
            switch.stop()

    def xterm(self, host_name: str) -> None:
        process = Popen(["xterm", "-e", "ip netns exec {host_name} bash"
                .format(host_name=host_name)])

        if process.poll() != None and process.poll() < 0:
            raise Exception("Could not run xterm for {host_name}".format(host_name=host_name))

        self._processes.add(process)

    def get_host(self, name: str) -> Host:
        return self._topology.get_host(name)

    def start(self) -> None:
        logging.basicConfig(level=self._settings.get_log_level())

        self._topology.create()
        self._start_switches()

    def stop(self) -> None:
        for process in self._processes:
            process.kill()

        self._stop_switches()
        self._topology.destroy()

class Repl(Cmd):

    histfile = expanduser('~/.p4sec-simulate-history')
    histfile_size = 1000

    def __init__(self, simulator: Simulator) -> None:
        super().__init__()
        self.prompt = "> "
        self.simulator = simulator

    def preloop(self):
        if readline and exists(Repl.histfile):
            readline.read_history_file(Repl.histfile)

    def postloop(self):
        if readline:
            readline.set_history_length(Repl.histfile_size)
            readline.write_history_file(Repl.histfile)

    def onecmd(self, line: str):
        try:
            return super().onecmd(line)
        except Exception as e:
            logging.error(str(e))

    def do_exit(self, line: str) -> bool:
        return True

    def do_xterm(self, line: str) -> None:
        for host in str.split(line):
            self.simulator.xterm(host)

    def do_host(self, line: str) -> None:
        match = re.search("^([^\\s]+)\\s+(.*)$", line)
        if match is None:
            raise Exception("Malformed command: host <name> <command>")
        host_name = match.group(1)
        command = match.group(2)

        host = self.simulator.get_host(host_name)
        host.run_command(command)

    def do_ping(self, line: str) -> None:
        match = re.search("^\\s*([^\\s]+)\\s+([^\\s]+)\\s*$", line)
        if match is None:
            raise Exception("Malformed command: ping <name 1> <name 2>")

        host_name1 = match.group(1)
        host_name2 = match.group(2)

        host1 = self.simulator.get_host(host_name1)
        host2 = self.simulator.get_host(host_name2)

        host1.run_command("ping {host2}".format(host2=host2.get_ip()))

settings = Settings(join(dirname(__file__), "simulation-topology.json"))
simulator = Simulator(settings)

try:
    simulator.start()
    repl = Repl(simulator)
    repl.cmdloop()
finally:
    simulator.stop()
