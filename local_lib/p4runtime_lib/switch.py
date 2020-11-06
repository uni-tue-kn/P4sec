# Copyright 2017-present Open Networking Foundation
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
from time import sleep
from p4.v1.p4runtime_pb2 import SetForwardingPipelineConfigRequest, WriteRequest, ReadRequest, Update, StreamMessageRequest, RegisterEntry, Index # type: ignore
from p4.v1.p4data_pb2 import P4Data # type: ignore
from p4.v1.p4runtime_pb2_grpc import P4RuntimeStub # type: ignore
from p4.tmp.p4config_pb2 import P4DeviceConfig # type: ignore
from local_lib.p4runtime_lib.helper import P4InfoHelper
import grpc # type: ignore
from threading import Thread, Event
from queue import Queue

import traceback

from common_lib.logger import Logger
from local_lib.packet.cpu import CPUPacket
from local_lib.settings import Settings

from typing import Set
from scapy.all import Ether # type: ignore

class CloseConnection:
    pass

class SwitchConnection:
    """
    Connection to switch.
    This class allows you to connect to a switch, write / read
    table entries or listen on packets.
    """

    def __init__(self, logger: Logger, settings: Settings):
        self.logger = logger
        self._settings = settings
        self._switch_settings = settings.get_switch()
        self.stub = P4RuntimeStub(grpc.insecure_channel(self._switch_settings.get_address()))
        self.helper = P4InfoHelper(self._switch_settings.get_p4info())

        # Queue that holds all packets which will be send out
        self.packets_out_q = Queue() # type: Queue

        # Thread on which the packets are send / received
        self.thread = None

        self.packet_in_listeners = set() # type: Set
        self.connection_started = Event()

    def _get_write_request(self):
        # Construct request
        request = WriteRequest()
        request.device_id = self._switch_settings.get_device_id()

        # Only master can write
        request.election_id.low = 1
        request.election_id.high = 0

        return request

    def get_num_ports(self):
        return self._switch_settings.get_num_ports()

    def write_table_entry(self, table_entry):
        self.logger.debug("Write table entry", 4)
        request = self._get_write_request()

        update = request.updates.add()
        update.type = Update.INSERT
        update.entity.table_entry.CopyFrom(table_entry)

        # write
        self.stub.Write(request)


    def write(self, table_name, match_fields, action_name, action_params={}):
        entry = self.helper.buildTableEntry( \
                table_name, match_fields, action_name, action_params)
        self.write_table_entry(entry)

    def update_table_entries(self, table_entries):
        self.logger.debug("Update table entries", 4)
        request = self._get_write_request()

        #TODO this should be added, however it is not supported yet.
        # request.atomicity = WriteRequest.Atomicity.DATAPLANE_ATOMIC

        for table_entry in table_entries:
            update = request.updates.add()
            update.type = Update.MODIFY
            update.entity.table_entry.CopyFrom(table_entry)

        self.stub.Write(request)

    def update_table_entry(self, table_entry):
        self.logger.debug("Update table entry", 4)
        request = self._get_write_request()

        update = request.updates.add()
        update.type = Update.MODIFY
        update.entity.table_entry.CopyFrom(table_entry)

        # write
        self.stub.Write(request)

    def update(self, table_name, match_fields, action_name, action_params={}):
        entry = self.helper.buildTableEntry( \
                table_name, match_fields, action_name, action_params)
        self.update_table_entry(entry)

    def delete(self, table_name, match_fields):
        entry = self.helper.buildTableEntry(table_name, match_fields)
        self.delete_table_entry(entry)

    def delete_table_entry(self, table_entry):
        request = self._get_write_request()

        update = request.updates.add()
        update.type = Update.DELETE
        update.entity.table_entry.CopyFrom(table_entry)

        # delete
        self.stub.Write(request)

    def read_table_entry(self, table_id):
        # request
        request = ReadRequest()
        request.device_id = self._switch_settings.get_device_id()

        # query
        entity = request.entities.add()
        table_entry = entity.table_entry
        table_entry.table_id = table_id

        # read
        return self.stub.Read(request)

    def write_register(self, name: str, index: int, value: int) -> None:
        try:
            entry = RegisterEntry(
                register_id=self.helper.get_registers_id(name),
                index=Index(index=0),
                data=P4Data(bitstring=bytes(bytearray([0, 0, 0, 0])))
            )
            request = self._get_write_request()

            update = request.updates.add()
            update.type = Update.INSERT
            update.entity.register_entry.CopyFrom(entry)

            self.stub.Write(request)
        except:
            raise Exception("Not supported by P4Runtime yet.")

    def read_table(self, table_name):
        table_id = self.helper.get_tables_id(table_name)
        return self.read_table_entry(table_id)

    def send(self, packet: Ether, port: int) -> None:
        cpu = CPUPacket(reason="SEND_DIRECT", port=port)
        packet.src = self._settings.get_mac()
        self.send_packet_out(bytes(cpu / packet))

    def send_packet_out(self, payload):
        request = StreamMessageRequest()
        request.packet.payload = payload
        self.packets_out_q.put(request)

    def send_packets_out(self, payloads):
        for payload in payloads:
            self.send_packet_out(payload)

    def listen_packet_in(self, callback):
        self.packet_in_listeners.add(callback)

    def unlisten_packet_in(self, callback):
        self.packet_in_listeners.remove(callback)

    def _notify_listeners(self, packet):
        for handler in self.packet_in_listeners:
            try:
                handler(packet)
            except Exception as e:
                traceback.print_exc()
                self.logger.warn("Unexpected exception occured: " + str(e))

    def _packet_out_iterator(self):
        # Check if packet is in the queue -> it will be send out via the StreamChannel
        while True:
            packet = self.packets_out_q.get(block=True)
            if isinstance(packet, CloseConnection):
                break
            yield packet

    def _handle_packet_in(self, stream):
        for response in stream:
            if response.packet:
                self._notify_listeners(response.packet)

    def _start_stream(self):
        self.logger.debug("Starting stream to switch", 3)

        try:
            stream = self.stub.StreamChannel(self._packet_out_iterator())
            self.connection_started.set()
            self._handle_packet_in(stream)
        except grpc.RpcError:
            self.logger.error("Stream to switch broken. Cannot read packages.")

    def _init_forwarding_pipeline(self):
        self.logger.debug("initializing forwarding pipeline", 3)

        device_config = P4DeviceConfig()
        device_config.reassign = True

        with open(self._switch_settings.get_bmv2()) as f:
            device_config.device_data = f.read().encode("utf8")

        # Request
        request = SetForwardingPipelineConfigRequest()
        request.device_id = self._switch_settings.get_device_id()
        request.config.p4info.CopyFrom(P4InfoHelper(self._switch_settings.get_p4info()).p4info)
        request.config.p4_device_config = device_config.SerializeToString()
        request.action = SetForwardingPipelineConfigRequest.VERIFY_AND_COMMIT

        # Send to switch
        self.stub.SetForwardingPipelineConfig(request)

        self.logger.debug("send init to switch", 3)
        request = StreamMessageRequest()
        request.arbitration.device_id = self._switch_settings.get_device_id()
        request.arbitration.election_id.high = 0
        request.arbitration.election_id.low = 1
        self.packets_out_q.put(request)

    def connect(self):
        self.logger.info("Connecting to switch.")

        self._init_forwarding_pipeline()

        self.connection_started.clear()
        self.thread = Thread(target=self._start_stream)
        self.thread.start()
        self.connection_started.wait()

    def disconnect(self):
        self.logger.debug("Disconnecting from switch.", 3)
        assert self.thread != None, "You have not started the switch connection."

        self.packets_out_q.put(CloseConnection())

        self.thread.join()

#class SwitchConnection(object):
#    def __init__(self, controller, name, address='127.0.0.1:50051', device_id=0, type='bmv2', crypto_address = None, debug=False):
#        self.controller = controller
#        self.name = name
#        self.address = address
#        self.device_id = device_id
#        self.channel = grpc.insecure_channel(self.address)
#        self.client_stub = p4runtime_pb2_grpc.P4RuntimeStub(self.channel)
#
#        self.crypto_client = None
#        if type == 'tofino':
#            self.crypto_client = TofinoCryptoClient(crypto_address)
#
#        self.debug = debug
#	self.request_lock = threading.Lock()
#
#    @abstractmethod
#    def buildDeviceConfig(self, **kwargs):
#        return p4config_pb2.P4DeviceConfig()
#
#    def SetForwardingPipelineConfig(self, p4info, dry_run=False, **kwargs):
#        device_config = self.buildDeviceConfig(**kwargs)
#        request = p4runtime_pb2.SetForwardingPipelineConfigRequest()
#        #config = request.configs.add()
#        #config.device_id = self.device_id
#
#        request.device_id = self.device_id
#        config = request.config
#
#        config.p4info.CopyFrom(p4info)
#        config.p4_device_config = device_config.SerializeToString()
#        request.action = p4runtime_pb2.SetForwardingPipelineConfigRequest.VERIFY_AND_COMMIT
#        if dry_run:
#            self.controller.logger.info("P4 Runtime SetForwardingPipelineConfig:" + str(request))
#        else:
#            self.client_stub.SetForwardingPipelineConfig(request)
#
#    def WriteTableEntry(self, table_entry, dry_run=False):
#        request = p4runtime_pb2.WriteRequest()
#        request.device_id = self.device_id
#
#        #nur master duerfen writes vornehmen
#        request.election_id.low = 1
#        request.election_id.high = 0
#
#        update = request.updates.add()
#        update.type = p4runtime_pb2.Update.INSERT
#        update.entity.table_entry.CopyFrom(table_entry)
#        if dry_run:
#            self.controller.logger.info("P4 Runtime Write:" + str(request))
#        else:
#            self.client_stub.Write(request)
#
#    def DeleteTableEntry(self, table_entry, dry_run=False):
#        request = p4runtime_pb2.WriteRequest()
#        request.device_id = self.device_id
#
#        #nur master duerfen writes vornehmen
#        request.election_id.low = 1
#        request.election_id.high = 0
#
#        update = request.updates.add()
#        update.type = p4runtime_pb2.Update.DELETE
#        update.entity.table_entry.CopyFrom(table_entry)
#        if dry_run:
#            self.controller.logger.info("P4 Runtime Write:" + str(request))
#        else:
#            self.client_stub.Write(request)
#
#    def ReadTableEntries(self, table_id=None, dry_run=False):
#        request = p4runtime_pb2.ReadRequest()
#        request.device_id = self.device_id
#        entity = request.entities.add()
#        table_entry = entity.table_entry
#        if table_id is not None:
#            table_entry.table_id = table_id
#        else:
#            table_entry.table_id = 0
#        if dry_run:
#            self.controller.logger.info("P4 Runtime Read:" + str(request))
#        else:
#            for response in self.client_stub.Read(request):
#                yield response
#
#    def ReadCounters(self, counter_id=None, index=None, dry_run=False):
#        request = p4runtime_pb2.ReadRequest()
#        request.device_id = self.device_id
#        entity = request.entities.add()
#        counter_entry = entity.counter_entry
#        if counter_id is not None:
#            counter_entry.counter_id = counter_id
#        else:
#            counter_entry.counter_id = 0
#        if index is not None:
#            counter_entry.index = index
#        if dry_run:
#            self.controller.logger.info("P4 Runtime Read:" + str(request))
#        else:
#            for response in self.client_stub.Read(request):
#                yield response
#
#    def stringifySerialData(self, data):
#        numbers = map(ord,data)
#        res = ""
#        for n in numbers:
#            res = res + ("\\0x{:02x}".format(n))
#        return res
#
#    def send_packet_out(self, payload):
#        request = p4runtime_pb2.StreamMessageRequest()
#        request.packet.payload = payload
#	self.request_lock.acquire()
#        self.requests.append(request)
#	self.request_lock.release()
#
#    def send_packet_out_multiple(self, payloads):
#	new_requests = []
#	for payload in payloads:
#	    request = p4runtime_pb2.StreamMessageRequest()
#	    request.packet.payload = payload
#            new_requests.append(request)
#
#	self.request_lock.acquire()
#        self.requests.extend(new_requests)
#	self.request_lock.release()
#
#    def send_init_and_wait(self, response_callback):
#        self.waiting = True
#	self.request_lock.acquire()
#        self.requests = []
#
#        init_req = p4runtime_pb2.StreamMessageRequest()
#        init_req.arbitration.election_id.low = 1
#        init_req.arbitration.election_id.high = 0
#        init_req.arbitration.device_id = self.device_id
#        self.requests.append(init_req)
#        self.request_lock.release()
#
#        for response in self.client_stub.StreamChannel(self.processRequests()):
#            if response_callback is not None:
#                response_callback(self, response)
#            else:
#                if self.debug:
#                    self.controller.logger.info("response: \n"  + str(response))
#
#
#
#    def stop_waiting(self):
#        self.waiting = False
#
#    def processRequests(self):
#        while self.waiting:
#	    self.request_lock.acquire()
#            if len(self.requests) > 0:
#                req = self.requests.pop(0)
#                if self.debug:
#                    self.controller.logger.info("sending request to switch %s \n%s" % (self.name, req))
#                yield req
#	    self.request_lock.release()
#
#
#            sleep(0.1)
