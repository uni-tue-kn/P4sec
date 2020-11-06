#!/usr/bin/env bash

echo "nameserver 127.0.0.1" > /etc/resolv.conf
dnsmasq -C dnsmasq.conf
