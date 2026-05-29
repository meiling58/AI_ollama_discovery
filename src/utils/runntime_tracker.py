import time
from functools import wraps


def track_runtime(engine_name=None):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            m, s = divmod(duration, 60)
            m = int(m)

            label = f"[{engine_name}] " if engine_name else ""

            print(f"\n⏱️ {label}{func.__name__} completed in {m} m {s:2f}s")

            return result

        return wrapper

    return decorator

