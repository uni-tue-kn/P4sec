from typing import Callable

class failable:

    def __init__(self, method_name: str) -> None:
        self._method_name = method_name

    def __call__(self, f: Callable[ ..., None ]):
        def failable_wrapper(other, *args, **kwargs):
            try:
                return f(other, *args, **kwargs)
            except:
                # TODO print error message
                pass

        return failable_wrapper
