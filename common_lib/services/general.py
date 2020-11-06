# common
from common_lib.services.service import Service
from common_lib.event import EventSystem

# protobuf
from general_pb2_grpc import add_GeneralServicer_to_server, GeneralServicer # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore

class GeneralService(Service, GeneralServicer):

    def __init__(self, event_system: EventSystem):
        Service.__init__(self, add_GeneralServicer_to_server, event_system)

    def check_connection(self, request: nothing, context: ServicerContext) -> nothing:
        return nothing()
