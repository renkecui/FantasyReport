from typing import Any, Dict


class Singleton(type):
    """Metaclass for classes that must have exactly one instance per process.

        class Logger(metaclass=Singleton): ...
        Logger() is Logger()   # True

    The first call creates the instance (with any arguments it was given); later calls return
    that same instance and ignore their arguments. `reset()` forgets it, for tests.
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in Singleton._instances:
            Singleton._instances[cls] = super().__call__(*args, **kwargs)
        return Singleton._instances[cls]

    def reset(cls):
        Singleton._instances.pop(cls, None)
