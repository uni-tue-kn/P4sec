from grpc import ServicerContext # type: ignore

def synchronize(f):
    def synchronous_method(self, request, context: ServicerContext):
        ev_system = self.get_event_system()

        if ev_system.get_context("server.peer") is not None and ev_system.get_context("server.peer") == context.peer_identity_key():
            return f(self, request, context)
        else:
            ev_system.set_context("server.peer", context.peer_identity_key())
            ev_system.acquire()
            try:
                result = f(self, request, context)
            finally:
                ev_system.release()
            ev_system.set_context("server.peer", None)
            return result
    return synchronous_method
