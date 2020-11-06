BUILD_DIR=build
PYTHONPATH=build/proto
CERTSTRAP=certstrap --depot-path "build/certificates" 

all: proto p4c externs certificates

build-dir:
	mkdir -p ${BUILD_DIR}

proto-dir: build-dir
	mkdir -p ${BUILD_DIR}/proto

proto: proto-dir
	python3 -m grpc_tools.protoc \
		-Iprotos \
		--python_out=${BUILD_DIR}/proto \
		--grpc_python_out=${BUILD_DIR}/proto \
		protos/*.proto

p4c-dir: build-dir
	mkdir -p ${BUILD_DIR}/p4c

p4c: p4c-dir
	p4c-bm2-ss \
		--std p4-16 \
		--p4runtime-files ${BUILD_DIR}/p4c/basic.txt \
		--emit-externs \
		--target bmv2 \
		--arch v1model \
		-o ${BUILD_DIR}/p4c/basic.json \
		p4/switch.p4

externs-dir: build-dir
	mkdir -p ${BUILD_DIR}/externs

externs: externs-dir
	cmake -B./${BUILD_DIR}/externs -H./externs
	cmake --build ${BUILD_DIR}/externs

certificates:
	if [ ! -d "build/certificates" ]; then \
		echo "Creating CA"; \
		${CERTSTRAP} init --common-name "ca"; \
		echo "Creating Local"; \
		${CERTSTRAP} request-cert --common-name "localhost"; \
		echo "Creating Local"; \
		${CERTSTRAP} sign localhost --CA "ca"; \
	fi;

clean:
	rm -rf ${BUILD_DIR}
	find . -name '*.pyc' -delete
	find . -name '*.pcap' -delete
	find . -type d -name __pycache__ -exec rm -r {} \+
	find . -type d -name .mypy_cache -exec rm -r {} \+

controller: all
	PYTHONPATH=${PYTHONPATH} ./global_controller.py

dist-controller: all
	PYTHONPATH=${PYTHONPATH} ./local_controller.py \
			   -a 127.0.0.1:50051 \
			   -n s1 \
			   -s ipc:///tmp/bmv2-0-notifications.ipc \
			   -i
