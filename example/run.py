#!/usr/bin/env python2
# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Adapted by Robert MacDavid (macdavid@cs.princeton.edu) from scripts found in
# the p4app repository (https://github.com/p4lang/p4app)
#
# We encourage you to dissect this script to better understand the BMv2/Mininet
# environment used by the P4 tutorial.

import os, sys, json, subprocess, re, argparse
from time import sleep
from os.path import join, dirname, exists
import shutil

from p4_mininet import P4Switch, P4Host

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.link import Intf
from mininet.cli import CLI
from mininet.util import makeIntfPair
from mininet.log import setLogLevel, info, error, debug

import atexit

setLogLevel("info")

from p4runtime_switch import P4RuntimeSwitch

def configureP4Switch(**switch_args):
    """
    Helper class that is called by mininet to initialize
    the virtual P4 switches. The purpose is to ensure each
    switch's thrift server is using a unique port.
    """
    if "sw_path" in switch_args and 'grpc' in switch_args['sw_path']:
        print("appears to be a grpc target")
        # If grpc appears in the BMv2 switch target, we assume will start P4 Runtime
        class ConfiguredP4RuntimeSwitch(P4RuntimeSwitch):
            def __init__(self, *opts, **kwargs):
                kwargs.update(switch_args)
                P4RuntimeSwitch.__init__(self, *opts, **kwargs)

            def describe(self):
                print("%s -> gRPC port: %d" % (self.name, self.grpc_port))

        return ConfiguredP4RuntimeSwitch
    else:
        print("appears to be a thrift target")
        class ConfiguredP4Switch(P4Switch):
            next_thrift_port = 9090
            def __init__(self, *opts, **kwargs):
                global next_thrift_port
                kwargs.update(switch_args)
                kwargs['thrift_port'] = ConfiguredP4Switch.next_thrift_port
                ConfiguredP4Switch.next_thrift_port += 1
                P4Switch.__init__(self, *opts, **kwargs)

            def describe(self):
                print("%s -> Thrift port: %d" % (self.name, self.thrift_port))

        return ConfiguredP4Switch


class ExerciseTopo(Topo):
    """ The mininet topology class for the P4 tutorial exercises.
        A custom class is used because the exercises make a few topology
        assumptions, mostly about the IP and MAC addresses.
    """
    def __init__(self, hosts, switches, links, log_dir, cpu_port, **opts):
        Topo.__init__(self, **opts)
        host_links = []
        switch_links = []
        self.sw_port_mapping = {}

        for link in links:
            if link['node1'][0] in ['h']:
                host_links.append(link)
            else:
                switch_links.append(link)

        link_sort_key = lambda x: x['node1'] + x['node2']
        # Links must be added in a sorted order so bmv2 port numbers are predictable
        host_links.sort(key=link_sort_key)
        switch_links.sort(key=link_sort_key)

        for sw in switches:
            self.addSwitch(sw, log_file="%s/%s.log" %(log_dir, sw), cpu_port=cpu_port)

        #add the hosts and hosts<->switch links
        for link in host_links:
            host_name = link['node1']
            host_sw   = link['node2']
            host_num = int(host_name[1:])
            sw_num   = int(host_sw[1:])
            host_ip = "10.0.%d.%d" % (sw_num, host_num)
            print(host_ip)
            host_mac = '00:00:00:00:%02x:%02x' % (sw_num, host_num)
            # Each host IP should be /24, so all exercise traffic will use the
            # default gateway (the switch) without sending ARP requests.
            self.addHost(host_name, ip=host_ip+'/24', mac=host_mac)
            self.addLink(host_name, host_sw,
                         delay=link['latency'], bw=link['bandwidth'],
                         addr1=host_mac, addr2=host_mac)
            self.addSwitchPort(host_sw, host_name)

        for link in switch_links:
            self.addLink(link['node1'], link['node2'],
                        delay=link['latency'], bw=link['bandwidth'])
            self.addSwitchPort(link['node1'], link['node2'])
            self.addSwitchPort(link['node2'], link['node1'])

        self.printPortMapping()

    def addSwitchPort(self, sw, node2):
        if sw not in self.sw_port_mapping:
            self.sw_port_mapping[sw] = []
        portno = len(self.sw_port_mapping[sw])+1
        self.sw_port_mapping[sw].append((portno, node2))

    def printPortMapping(self):
        print("Switch port mapping:")
        for sw in sorted(self.sw_port_mapping.keys()):
            print("%s: " % sw),
            for portno, node2 in self.sw_port_mapping[sw]:
                print("%d:%s\t" % (portno, node2)),
            print("\n"),


class ExerciseRunner:
    def _formatLatency(self, l):
        """ Helper method for parsing link latencies from the topology json. """
        if isinstance(l, (str, unicode)):
            return l
        else:
            return str(l) + "ms"


    def __init__(self, settings):
        self.settings = settings
        print("Reading topology file.")
        self._read_topology()

    def initialize(self):
        for dir_name in [self.settings.build_path, self.settings.logs_path, self.settings.pcaps_path]:
            if not exists(dir_name):
                os.makedirs(dir_name)

    def clean(self):
        shutil.rmtree(self.settings.build_path)
        os.system("mn -c")

    def _read_topology(self):
        with open(self.settings.topology, "r") as f:
            topology = json.load(f)
            self.hosts = topology["hosts"]
            self.switches = topology["switches"]
            self.links = self.parse_links(topology["links"])


    def run(self):
        """
        Sets up the mininet instance, programs the switches,
        and starts the mininet CLI. This is the main method to run after
        initializing the object.
        """
        try:
            self.initialize()

            # Initialize mininet with the topology specified by the config
            self.create_network()
            self.net.start()
            sleep(1)

            # some programming that must happen after the net has started
            self.program_hosts()
            #self.program_switches()

            # wait for that to finish. Not sure how to do this better
            sleep(1)

            self.do_net_cli()
            # stop right after the CLI is exited
            self.net.stop()
        finally:
            self.clean()


    def parse_links(self, unparsed_links):
        """
        Given a list of links descriptions of the form [node1, node2, latency, bandwidth]
        with the latency and bandwidth being optional, parses these descriptions
        into dictionaries and store them as self.links
        """
        links = []
        for link in unparsed_links:
            # make sure each link's endpoints are ordered alphabetically
            s, t, = link[0], link[1]
            if s > t:
                s,t = t,s

            link_dict = {'node1':s,
                        'node2':t,
                        'latency':'0ms',
                        'bandwidth':None
                        }
            if len(link) > 2:
                link_dict['latency'] = self._formatLatency(link[2])
            if len(link) > 3:
                link_dict['bandwidth'] = link[3]

            if link_dict['node1'][0] == 'h':
                assert link_dict['node2'][0] == 's', 'Hosts should be connected to switches, not ' + str(link_dict['node2'])
            if link_dict['node2'][0] == 'c':
                assert link_dict['node1'][0] == 'a', 'Controller should be connected to agents, not ' + str(link_dict['node1'])
            links.append(link_dict)
        return links


    def create_network(self):
        """ Create the mininet network object, and store it as self.net.

            Side effects:
                - Mininet topology instance stored as self.topo
                - Mininet instance stored as self.net
        """
        print("Building mininet topology.")

        self.topo = ExerciseTopo(self.hosts, self.switches.keys(), self.links,
                self.settings.logs_path, self.settings.cpu_port)

        switchClass = configureP4Switch(
                sw_path=self.settings.behavioral_model,
                json_path=self.settings.switch_json,
                log_console=True,
                pcap_dump=self.settings.pcaps_path,
                cpu_port=self.settings.cpu_port)

        self.net = Mininet(topo = self.topo,
                      link = TCLink,
                      host = P4Host,
                      switch = switchClass,
                      controller = None)

    def program_hosts(self):
        """ Adds static ARP entries and default routes to each mininet host.

            Assumes:
                - A mininet instance is stored as self.net and self.net.start() has
                  been called.
        """
        for host_name in self.topo.hosts():
            h = self.net.get(host_name)
            h_iface = h.intfs.values()[0]
            link = h_iface.link

            # phony IP to lie to the host about
            host_id = int(host_name[1:])
            sw_ip = "10.0.%d.254" % host_id

            # Ensure each host's interface name is unique, or else
            # mininet cannot shutdown gracefully
            h.defaultIntf().rename('%s-eth0' % host_name)
            # static arp entries and default routes
            h.cmd('ethtool --offload %s rx off tx off' % h_iface.name)
            h.cmd('ip route add %s dev %s' % (sw_ip, h_iface.name))
            h.cmd("echo \"nameserver 127.0.0.1\" > /etc/resolv.conf")
            h.cmd("./setup.bash")
            h.setDefaultRoute("via %s" % sw_ip)


    def do_net_cli(self):
        """ Starts up the mininet CLI and prints some helpful output.

            Assumes:
                - A mininet instance is stored as self.net and self.net.start() has
                  been called.
        """
        for s in self.net.switches:
            s.describe()
        for h in self.net.hosts:
            h.describe()
        print("Starting mininet CLI")
        # Generate a message that will be printed by the Mininet CLI to make
        # interacting with the simple switch a little easier.
        print("")
        print("======================================================================")
        print("Welcome to the BMV2 Mininet CLI!")
        print("======================================================================")
        print("Your P4 program is installed into the BMV2 software switch")
        print("and your initial configuration is loaded. You can interact")
        print("with the network using the mininet CLI below.")
        print("")
        if self.settings.switch_json:
            print("To inspect or change the switch configuration, connect to")
            print("its CLI from your host operating system using this command:")
            print("  simple_switch_CLI --thrift-port <switch thrift port>")
            print("")
        print("To view a switch log, run this command from your host OS:")
        print("  tail -f %s/<switchname>.log" %  self.settings.logs_path)
        print("")
        print("To view the switch output pcap, check the pcap files in %s:" % self.settings.pcaps_path)
        print(" for example run:  sudo tcpdump -xxx -r s1-eth1.pcap")
        print("")

        CLI(self.net)

class Settings:
    def __init__(self):
        cwd = os.getcwd()
        self.build_path = join(cwd, "build")
        self.logs_path = self.resolve("logs")
        self.pcaps_path = self.resolve("pcaps")
        self.quiet = False
        self.topology = join(dirname(__file__), "topology.json")
        self.switch_json = join(dirname(__file__), "../build/p4c/basic.json")
        self.behavioral_model = "simple_switch_grpc"
        self.cpu_port = 16

    def resolve(self, path):
        return join(self.build_path, path)

# Run exercise
settings = Settings()
exercise = ExerciseRunner(settings)
exercise.run()
