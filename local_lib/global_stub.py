# common
from common_lib.credentials import Credentials

# Exceptions
from local_lib.exception import RegistrationException

# protobuf / grpc
from grpc import secure_channel, RpcError
from global_pb2_grpc import PrivateInterfaceStub
from controller_pb2 import controller

# Other
import socket


class GlobalStub:
    """ Stub of the global controller. """

    def __init__(self, controller):
        # make the connection

        settings = controller.settings
        certificate = Credentials.read(
            settings.ca_path,
            settings.cert_path,
            settings.key_path
        ).get_client_credentials()
        channel = secure_channel(controller.settings.controller_address, certificate)
        self.stub = PrivateInterfaceStub(channel)

        # properties
        self.controller = controller
        self.logger = controller.logger
        self.registration = None

    def topology_add_edge(self, edge):
        self.stub.topology_add_edge(edge.to_protobuf())

    def topology_remove_edge(self, edge):
        self.stub.topology_remove_edge(edge.to_protobuf())

    def _get_controller(self):
        request = controller()
        request.name = self.controller.settings.switch_name
        request.mac = self.controller.settings.mac_address
        # TODO this does not work
        #request.address = socket.gethostbyname(socket.gethostname()) \
        #        + ":" + str(self.controller.settings.port)
        request.address = str(self.controller.settings.address)
        return request

    def register(self):
        assert self.registration == None, "Already registered."

        self.logger.info("Register at global controller")

        # Request
        request = self._get_controller()

        # register
        try:
            self.registration = self.stub.register(request)
        except RpcError as e:
            raise RegistrationException(str(e))

    def unregister(self):
        request = self._get_controller()
        try:
            self.stub.unregister(request)
        except RpcError as e:
            self.logger.warn("Could not unregister at global controller: " + str(e))

