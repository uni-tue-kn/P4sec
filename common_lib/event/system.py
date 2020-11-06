from common_lib.event.task import Task
from common_lib.logger import Logger

from time import time
from threading import Event, RLock
from typing import Set, Dict, Any
import traceback

class System:

    def __init__(self, logger: Logger):
        self._logger = logger
        self._tasks = set() # type: Set[Task]

        self._new_task_event = Event()
        self._lock = RLock()
        self._stop = False

        self._context = { } # type: Dict[ str, Any ]

    def set_context(self, key: str, value: Any) -> None:
        self._context[key] = value

    def get_context(self, key) -> Any:
        return self._context.get(key)

    def _push_task(self, task: Task) -> None:
        self._tasks.add(task)

    def _pop_task(self) -> Task:
        task = self._peek_task()
        self._tasks.remove(task)
        return task

    def _peek_task(self) -> Task:
        return sorted(self._tasks, reverse=True).pop()

    def set_timeout(self, f, timeout: int) -> Task:
        self.acquire()
        task = Task(f, time() + timeout)
        self._push_task(task)
        self._new_task_event.set()
        self.release()
        return task

    def set_interval(self, f, interval: int, continue_=True, immediate=False) -> None:
        self.set_timeout(lambda: self.set_interval(f, interval, not f()), \
                0 if immediate else interval)

    def force_release(self) -> None:
        while not self._lock.acquire(blocking=False):
            self._lock.release()
        self._lock.release()

    def acquire(self) -> bool:
        result = self._lock.acquire(timeout=10)#s

        if result == False:
            self._logger.warn("Could not acquire Lock -> Probably a deadlock occured.")
            self.force_release()

        return result

    def release(self) -> None:
        self._lock.release()

    def stop(self) -> None:
        self._stop = True
        self._new_task_event.set()

    def run(self) -> None:
        self._stop = False

        while True:
            self._new_task_event.clear()

            if len(self._tasks) > 0:
                self._new_task_event.wait(self._peek_task().get_ready() - time())
            else:
                self._new_task_event.wait()

            if self._stop:
                break

            try:
                self.acquire()
                task = self._pop_task()

                if task.get_ready() < time():
                    task()
                else:
                    self._push_task(task)
            except Exception as e:
                self._logger.error("Unexpected error occured: " + str(e))
                traceback.print_exc()
            finally:
                # ensure that the lock is released
                self.release()

