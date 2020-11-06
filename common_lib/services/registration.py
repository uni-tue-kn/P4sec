# common
from common_lib.services.service import Service
from common_lib.event import EventSystem

# protobuf / grpc
from controller_pb2_grpc import RegistrationServicer, add_RegistrationServicer_to_server # type: ignore

class RegistrationService(Service, RegistrationServicer):

    def __init__(self, event_system: EventSystem):
        Service.__init__(self, add_RegistrationServicer_to_server, event_system)
