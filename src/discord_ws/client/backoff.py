import random
import time
from typing import Protocol


class Backoff(Protocol):
    """
    Defines a backoff algorithm that can be called to retrieve the amount
    of time to wait.
    """

    def __call__(self) -> float:
        ...


class ExponentialBackoff(Backoff):
    """Implements a basic exponential backoff algorithm.

    Each time this is called, the base time is computed as ``offset + base ** occurrences``
    and the number of occurrences is increased by 1, up to :attr:`max_occurrences`.
    If :attr:`randomize` is true, an additional random factor of [0, 1) seconds
    is applied to the result.

    After ``offset + base ** (max_occurrences + 1)`` seconds have passed,
    the number of occurrences resets to 0.

    """

    def __init__(
        self,
        *,
        offset: int = 0,
        base: int = 2,
        max_occurrences: int = 10,
        randomize: bool = True,
    ) -> None:
        self.offset = offset
        self.base = base
        self.max_occurrences = max_occurrences
        self.randomize = randomize

        self.occurrences = 0
        self._last_called = self._time()
        self._rand = random.Random()

    def __call__(self) -> float:
        now = self._time()
        elapsed = now - self._last_called
        self._last_called = now

        if elapsed > self._duration(self.max_occurrences + 1):
            self.occurrences = 0

        occurrences = self.occurrences
        if occurrences < self.max_occurrences:
            self.occurrences += 1

        duration = self._duration(occurrences)
        if self.randomize:
            duration += self._rand.random()
        return duration

    def _time(self) -> float:
        return time.monotonic()

    def _duration(self, occurrences: int) -> float:
        return self.offset + self.base**occurrences
