"""TTL cache decorator for query-like functions."""

import functools
import time
from collections.abc import Callable, Hashable
from typing import Any, NamedTuple, TypeVar

_RESULT = TypeVar("_RESULT")


class CacheInfo(NamedTuple):
    """Statistics exposed by ``cache_info()``."""

    hits: int
    misses: int
    currsize: int


def cached(
    ttl: float | None = None,
) -> Callable[[Callable[..., _RESULT]], Callable[..., _RESULT]]:
    """Cache results of a query function keyed by its arguments.

    The wrapped function is called at most once per distinct tuple of
    positional arguments until the entry expires.  ``ttl`` is a
    lifetime in seconds measured with :func:`time.monotonic`;
    ``None`` means entries never expire.  Arguments must be
    immutable (hashable), otherwise the lookup raises ``TypeError``.

    The wrapper exposes ``cache_info()`` with ``hits``, ``misses``
    and ``currsize`` attributes, and ``cache_clear()`` which drops
    all entries and resets the counters.
    """

    def decorator(
        func: Callable[..., _RESULT],
    ) -> Callable[..., _RESULT]:
        store: dict[Hashable, tuple[_RESULT, float]] = {}
        hits = 0
        misses = 0

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> _RESULT:
            nonlocal hits, misses
            key: Hashable = args if not kwargs else (
                args,
                tuple(sorted(kwargs.items())),
            )
            now = time.monotonic()
            entry = store.get(key)
            if entry is not None:
                value, stored_at = entry
                if ttl is None or now - stored_at < ttl:
                    hits += 1
                    return value
                del store[key]
            misses += 1
            value = func(*args, **kwargs)
            store[key] = (value, time.monotonic())
            return value

        def cache_info() -> CacheInfo:
            """Return hit/miss counters and the entry count."""
            return CacheInfo(hits, misses, len(store))

        def cache_clear() -> None:
            """Drop every entry and reset the counters."""
            nonlocal hits, misses
            store.clear()
            hits = 0
            misses = 0

        wrapper.cache_info = cache_info  # type: ignore[attr-defined]
        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        return wrapper

    return decorator
