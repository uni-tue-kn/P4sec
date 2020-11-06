from nothing_pb2 import nothing # type: ignore

def lazy(f):
    def lazy_wrapper(self, *args, **kwargs):
        def lazy_execute():
            f(self, *args, **kwargs)
        self._event_system.set_timeout(lazy_execute, 0)
        return nothing()
    return lazy_wrapper
