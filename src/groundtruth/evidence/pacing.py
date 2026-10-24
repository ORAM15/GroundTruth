"""Quota pacing for embedding calls (GT-11).

Google's free tier counts embedded ITEMS, not requests: ~100 items per
60-second window. A document with more chunks than one window allows
cannot be embedded synchronously, so the background worker paces itself
through this class instead of sleeping ad hoc.

The pacer is deliberately injectable: ``window_seconds`` /
``max_items_per_window`` come from the environment by default but can be
passed directly, and the clock / sleep functions are constructor
arguments, so tests drive pacing without waiting out real windows.
Elapsed time is measured with a monotonic clock (immune to wall-clock
jumps); that is the correct reading of "per 60-second window" for a
rate limiter.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable

DEFAULT_WINDOW_SECONDS = 60.0
DEFAULT_MAX_ITEMS_PER_WINDOW = 100

ENV_WINDOW_SECONDS = "GT_EMBED_RATE_WINDOW_SECONDS"
ENV_MAX_ITEMS = "GT_EMBED_RATE_MAX_ITEMS"


def pacer_from_env(
    *,
    sleep_fn: Callable[[float], None] | None = None,
    clock_fn: Callable[[], float] | None = None,
) -> QuotaPacer:
    """Build a pacer from the environment, falling back to the free-tier
    defaults (100 items per 60 seconds) for missing or malformed values."""
    try:
        window = float(os.getenv(ENV_WINDOW_SECONDS, "") or DEFAULT_WINDOW_SECONDS)
    except ValueError:
        window = DEFAULT_WINDOW_SECONDS
    try:
        max_items = int(os.getenv(ENV_MAX_ITEMS, "") or DEFAULT_MAX_ITEMS_PER_WINDOW)
    except ValueError:
        max_items = DEFAULT_MAX_ITEMS_PER_WINDOW
    if window <= 0:
        window = DEFAULT_WINDOW_SECONDS
    if max_items <= 0:
        max_items = DEFAULT_MAX_ITEMS_PER_WINDOW
    return QuotaPacer(
        max_items_per_window=max_items,
        window_seconds=window,
        sleep_fn=sleep_fn,
        clock_fn=clock_fn,
    )


class QuotaPacer:
    """Allow at most ``max_items_per_window`` items per rolling window.

    ``acquire(n)`` blocks (via the injected sleep function) until ``n``
    items fit in the current window. A request larger than a whole window
    is allowed on its own in a fresh window rather than deadlocking:
    it consumes the entire window.
    """

    def __init__(
        self,
        *,
        max_items_per_window: int = DEFAULT_MAX_ITEMS_PER_WINDOW,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        sleep_fn: Callable[[float], None] | None = None,
        clock_fn: Callable[[], float] | None = None,
    ) -> None:
        self._max_items = max_items_per_window
        self._window = window_seconds
        self._sleep = sleep_fn or time.sleep
        self._clock = clock_fn or time.monotonic
        self._window_start: float | None = None
        self._used = 0

    def acquire(self, n: int) -> None:
        """Wait until ``n`` items fit in the current window, then book them."""
        if n <= 0:
            return
        while True:
            now = self._clock()
            if self._window_start is None or now - self._window_start >= self._window:
                self._window_start = now
                self._used = 0
            if n >= self._max_items:
                # Oversized request: it gets a fresh window to itself.
                if self._used == 0:
                    self._used = self._max_items
                    return
            elif self._used + n <= self._max_items:
                self._used += n
                return
            remaining = self._window_start + self._window - now
            if remaining > 0:
                self._sleep(remaining)

    def note_rate_limit(self, retry_after: float | None) -> None:
        """Record that the provider rejected a call with 429.

        Sleeps the provider's requested delay when one is known, otherwise
        the rest of the current window, then starts a fresh window — the
        rejected window is exhausted either way, so the next acquire must
        not assume any of it remains.
        """
        if retry_after is not None and retry_after > 0:
            self._sleep(retry_after)
        else:
            now = self._clock()
            if self._window_start is not None:
                remaining = self._window_start + self._window - now
                if remaining > 0:
                    self._sleep(remaining)
        self._window_start = None
        self._used = 0
