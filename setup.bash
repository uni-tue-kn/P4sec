#!/usr/bin/env bash

# Script
vagrant up
vagrant ssh -- -t "cd /vagrant && make"
vagrant ssh -- -t "cd /vagrant && /vagrant/setup-tmux.bash"
