#!/bin/bash

# Print commands and exit on errors
set -xe

apt-get update

DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade

apt-get install -y --no-install-recommends \
  autoconf \
  autoconf-archive \
  automake \
  bison \
  build-essential \
  ca-certificates \
  cmake \
  cpp \
  curl \
  flex \
  git \
  libboost-dev \
  libboost-filesystem-dev \
  libboost-iostreams-dev \
  libboost-program-options-dev \
  libboost-system-dev \
  libboost-test-dev \
  libboost-thread-dev \
  libc6-dev \
  libevent-dev \
  libffi-dev \
  libfl-dev \
  libgc-dev \
  libgc1c2 \
  libgflags-dev \
  libgmp-dev \
  libgmp10 \
  libgmpxx4ldbl \
  libjudy-dev \
  libpcap-dev \
  libpthread-stubs0-dev \
  libreadline-dev \
  libtool \
  make \
  coreutils \
  pkg-config \
  python \
  python-dev \
  python-ipaddr \
  python-pip \
  python-scapy \
  python-setuptools \
  python3-pip \
  tcpdump \
  unzip \
  vim \
  wget \
  xterm \
  libpcre3-dev \
  libavl-dev \
  libev-dev \
  libcmocka-dev \
  swig \
  python-psutil \
  libprotobuf-c-dev \
  protobuf-c-compiler \
  golang \
  virtualenv \
  python3-dev \
  network-manager
  #gcc-5 \
  #g++-5 \
  #libssl-dev \
  #libgrpc++-dev \
  #libgrpc-dev \
  #protobuf-compiler \
  #libprotobuf-dev \
  #libcrypto++-dev \
  #libcrypto++6 \
  #libprotobuf-dev \
  #libssl-dev \
  #libgrpc-dev \

#ln -s /usr/lib/x86_64-linux-gnu/libcrypto.so.1.1 /usr/lib/x86_64-linux-gnu/libcrypto.so.6
#ln -s /usr/lib/x86_64-linux-gnu/libssl.so.1.1 /usr/lib/x86_64-linux-gnu/libssl.so.6

# radius
apt install -y --no-install-recommends freeradius freeradius-utils libssl-dev devscripts pkg-config libnl-3-dev libnl-genl-3-dev

apt install -y --install-recommends linux-image-generic-hwe-16.04 xserver-xorg-hwe-16.04

if [ ! -d "certstrap" ]; then
	git clone https://github.com/square/certstrap
	cd certstrap
	git checkout "v1.1.1"
	./build
	cp bin/certstrap-v1.1.1-linux-amd64 /usr/local/bin/certstrap
	cd ..
fi

if [ ! -d "iproute2" ]; then
	git clone git://git.kernel.org/pub/scm/linux/kernel/git/shemminger/iproute2.git
	cd iproute2
	./configure
	make -j2
	make install
	cd ..
fi

cat /vagrant/example/freeradius-clients.txt >> /etc/freeradius/clients.conf
cat /vagrant/example/freeradius-users.txt >> /etc/freeradius/users
systemctl restart freeradius


apt install -y libncurses-dev
git clone https://github.com/tmux/tmux.git
cd tmux
git checkout 3.0
./autogen.sh
./configure
make
make install
cd ..
