from typing import TypeVar

BE_co = TypeVar("BE_co", bound=BaseException)


def _unwrap_first_exception(eg: BaseExceptionGroup[BE_co]) -> BE_co | None:
    for e in eg.exceptions:
        if isinstance(e, BaseExceptionGroup):
            e = _unwrap_first_exception(e)
            if e is None:
                continue
        return e
