import traceback as tb

class traceback:
    def __init__(self, logger):
        self._logger = logger

    def __call__(self, f):
        def wrapper(other, request, context):
            try:
                return f(other, request, context)
            except:
                getattr(other, self._logger).error(tb.format_exc())
        return wrapper
