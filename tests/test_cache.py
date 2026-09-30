"""Tests for the query cache decorator (advanced task No. 8)."""

import time
import unittest
from typing import Any

from lab7.cache import cached
from lab7.reports import create_schema_two_tables, seed, tasks_with_users
from lab7.sqlite_tasks import connect


class CacheTests(unittest.TestCase):
    """Checks for the :func:`lab7.cache.cached` decorator."""

    def setUp(self) -> None:
        """Create an in-memory database with the demo dataset."""
        self.conn = connect()
        create_schema_two_tables(self.conn)
        seed(self.conn)
        self.executions = 0

        @cached()
        def query(done: bool) -> list[dict[str, Any]]:
            """Pretend to be a slow SELECT counted by the test."""
            self.executions += 1
            rows = tasks_with_users(self.conn)
            return [row for row in rows if row["done"] == done]

        self.query = query

    def tearDown(self) -> None:
        """Close the in-memory database."""
        self.conn.close()

    def test_repeated_calls_execute_query_once(self) -> None:
        """Three identical calls run one query and record two hits."""
        for _ in range(3):
            self.query(True)
        self.assertEqual(self.executions, 1)
        info = self.query.cache_info()
        self.assertEqual(info.hits, 2)
        self.assertEqual(info.misses, 1)
        self.assertEqual(info.currsize, 1)

    def test_cached_value_equals_fresh_result(self) -> None:
        """The cached answer matches an uncached computation."""
        first = self.query(False)
        second = self.query(False)
        self.assertEqual(first, second)
        self.assertEqual(
            [row["title"] for row in second],
            ["review code", "deploy service"],
        )

    def test_cache_clear_forces_recomputation(self) -> None:
        """After ``cache_clear`` the next call is a miss again."""
        self.query(True)
        self.query(True)
        self.query.cache_clear()
        info = self.query.cache_info()
        self.assertEqual(info.hits, 0)
        self.assertEqual(info.misses, 0)
        self.assertEqual(info.currsize, 0)
        self.query(True)
        self.assertEqual(self.executions, 2)
        self.assertEqual(self.query.cache_info().misses, 1)

    def test_different_arguments_use_different_entries(self) -> None:
        """Distinct arguments are cached independently."""
        self.query(True)
        self.query(False)
        self.query(True)
        self.assertEqual(self.executions, 2)
        self.assertEqual(self.query.cache_info().hits, 1)
        self.assertEqual(self.query.cache_info().currsize, 2)

    def test_ttl_expiry_triggers_recomputation(self) -> None:
        """An entry older than ``ttl`` is recomputed on access."""

        @cached(ttl=0.05)
        def timed(done: bool) -> int:
            self.executions += 1
            return 1

        timed(False)
        timed(False)
        self.assertEqual(self.executions, 1)
        time.sleep(0.06)
        timed(False)
        self.assertEqual(self.executions, 2)
        self.assertEqual(timed.cache_info().misses, 2)

    def test_ttl_keeps_entry_while_fresh(self) -> None:
        """A fresh entry is served without calling the query."""

        @cached(ttl=10.0)
        def timed(done: bool) -> int:
            self.executions += 1
            return 1

        timed(False)
        timed(False)
        self.assertEqual(self.executions, 1)
        self.assertEqual(timed.cache_info().hits, 1)

    def test_unhashable_argument_raises_type_error(self) -> None:
        """Only immutable arguments can form a cache key."""
        with self.assertRaises(TypeError):
            self.query(["not", "hashable"])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
