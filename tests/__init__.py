from contextlib import contextmanager
from typing import Type


@contextmanager
def raises_exception_group(exc: Type[BaseException] | tuple[Type[BaseException], ...]):
    if not isinstance(exc, tuple):
        exc = (exc,)

    try:
        yield
    except* exc:
        pass
    else:
        exc_names = " or ".join(type(e).__name__ for e in exc)
        assert False, f"Expected {exc_names} to be raised"
