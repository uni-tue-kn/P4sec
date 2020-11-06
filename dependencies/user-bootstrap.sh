#!/bin/bash

# Print script commands.
set -x
# Exit on errors.
set -e

#BMV2_COMMIT="39abe290b4143e829b8f983965fcdc711e3c450c"
#BMV2_COMMIT="ae87b4d4523488ac935133b4aef437796ad1bbd1"
BMV2_COMMIT="master"

#PI_COMMIT="1ca80066e065ae52a34416822c20b83173b2146f"
PI_COMMIT="stable"

#P4C_COMMIT="e737c57d1dd32b2daaaecf0bc17bb475b14bdf4c"
#P4C_COMMIT="6070b20a6ca83bc6c66c6aac2ea53f83df1c8c61"
#P4C_COMMIT="5f948527dc9f67525b5d0067dc33365f3c6c669b"
#P4C_COMMIT="04c02d5eab53fbfc35a4dfca5bfeeeeaa378456a"

#P4C_COMMIT="69e132d"
#P4C_COMMIT="d5654621336b4c24f0f738860796def0ece42934"
P4C_COMMIT="580902a0dfda3c4d657295e5c5b474450e108a89"



PROTOBUF_COMMIT="v3.5.2"
#PROTOBUF_COMMIT="v3.9.1" #-> somehow create runtime error (https://github.com/protocolbuffers/protobuf/issues/4958)
GRPC_COMMIT="v1.3.2"
#GRPC_COMMIT="v1.23.0"

NUM_CORES=`grep -c ^processor /proc/cpuinfo`

# create python
#if [ ! -d ".venv" ]; then
#  virtualenv -p python3 ~/.venv
#fi
#
#source ~/.venv/bin/activate

PYTHON=$(sudo which python3)
export CXX=$(which g++)
export CC=$(which gcc)

# Mininet
if [ ! -d "mininet" ]; then
	git clone git://github.com/mininet/mininet mininet
	cd mininet
	sudo ./util/install.sh -nwv
	cd ".."
fi


PYTHON="$(which python)"

# Protobuf
if [ ! -d "protobuf" ]; then
	git clone https://github.com/google/protobuf.git
	cd protobuf
	git checkout ${PROTOBUF_COMMIT}
	export CFLAGS="-Os"
	export CXXFLAGS="-Os"
	export LDFLAGS="-Wl,-s"
	./autogen.sh
	./configure --prefix=/usr/local
	make -j${NUM_CORES}
	sudo make install
	sudo ldconfig
	unset CFLAGS CXXFLAGS LDFLAGS
	cd ..
fi

# gRPC
if [ ! -d "grpc" ]; then
	git clone https://github.com/grpc/grpc.git
	cd grpc
	git checkout ${GRPC_COMMIT}
	git submodule update --init --recursive
	export LDFLAGS="-Wl,-s"
	sudo make install
	sudo ldconfig
	#mkdir .build
	#cd .build
	#cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=$(which g++-5) -DCMAKE_C_COMPILER=$(which gcc-5) ..
	#make -j${NUM_CORES}
	#sudo make install
	#sudo ldconfig
	#unset LDFLAGS
	#cd ..
	cd ..
fi

# BMv2 deps (needed by PI)
if [ ! -d "behavioral-model" ]; then
  git clone https://github.com/p4lang/behavioral-model.git
fi

cd behavioral-model
git checkout ${BMV2_COMMIT}
# From bmv2's install_deps.sh, we can skip apt-get install.
# Nanomsg is required by p4runtime, p4runtime is needed by BMv2...
if [ ! -d ".build-dependencies" ]; then
	mkdir .build-dependencies
	cd .build-dependencies
	bash ../travis/install-thrift.sh
	bash ../travis/install-nanomsg.sh
	sudo ldconfig
	bash ../travis/install-nnpy.sh
	cd ..
fi
cd ..

# PI/P4Runtime
if [ ! -d "PI" ]; then
  git clone https://github.com/p4lang/PI.git
fi
cd PI
git checkout ${PI_COMMIT}
git submodule update --init --recursive
./autogen.sh
./configure --with-proto
make -j${NUM_CORES}
sudo make install
sudo ldconfig
cd ..

# Bmv2
cd behavioral-model
./autogen.sh
./configure --enable-debugger --with-pi --enable-modules
make -j${NUM_CORES}
sudo make install
sudo ldconfig
# Simple_switch_grpc target
cd targets/simple_switch_grpc
./autogen.sh
./configure --with-thrift --enable-modules
make -j${NUM_CORES}
sudo make install
sudo ldconfig
cd ..
cd ..
cd ..

# P4C
if [ ! -d "p4c" ]; then
  git clone https://github.com/p4lang/p4c
fi
cd p4c
git checkout ${P4C_COMMIT}
git submodule update --init --recursive
mkdir -p build
cd build
cmake -DPC_LIBGMP_LIBDIR="/usr/lib/x86_64-linux-gnu/" ..
make -j${NUM_CORES}
sudo make install
sudo ldconfig
cd ..
cd ..

#pip3 install --upgrade pip
pip3 install setuptools
pip3 install pyopenssl
pip3 install grpcio
pip3 install grpcio-tools
pip3 install termcolor
pip3 install protobuf
pip3 install tabulate
pip3 install networkx
pip3 install scapy
pip3 install nnpy
#pip install psutil
pip3 install netifaces
pip3 install dnspython

pip2 install setuptools
pip2 install psutil

sudo cp -r /usr/local/lib/python2.7/dist-packages/p4 /usr/local/lib/python3.5/dist-packages
sudo cp -r /usr/local/lib/python2.7/dist-packages/google /usr/local/lib/python3.5/dist-packages
