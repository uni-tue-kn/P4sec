from common_lib.event import EventSystem

class Service:
    def __init__(self, add_method, event_system: EventSystem):
        self._add_method = add_method
        self._event_system = event_system

    def get_event_system(self) -> EventSystem:
        return self._event_system

    def use(self, server):
        return self._add_method(self, server)
