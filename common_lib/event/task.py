from time import time

class Task:
    def __init__(self, f, ready: float):
        self._f = f
        self._ready = ready

    def set_ready(self, ready: float) -> None:
        self._ready = ready

    def get_ready(self) -> float:
        return self._ready

    def __call__(self) -> None:
        self._f()

    def __lt__(self, other) -> bool:
        return self._ready < other.get_ready()

    def __str__(self):
        return "Task(" + str(self._ready) + ")"
