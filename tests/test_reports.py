"""Tests for the JOIN reports (medium task No. 8)."""

import unittest

from lab7.reports import (
    create_schema_two_tables,
    seed,
    tasks_with_users,
    user_task_counts,
)
from lab7.sqlite_tasks import connect


class ReportsTests(unittest.TestCase):
    """Checks for the ``lab7.reports`` module."""

    def setUp(self) -> None:
        """Create and seed a fresh in-memory database."""
        self.conn = connect()
        create_schema_two_tables(self.conn)
        seed(self.conn)

    def tearDown(self) -> None:
        """Close the in-memory database."""
        self.conn.close()

    def test_join_returns_owner_name_per_task(self) -> None:
        """Every task row carries the name of its owner."""
        joined = tasks_with_users(self.conn)
        self.assertEqual(len(joined), 3)
        self.assertEqual(
            joined[0],
            {
                "id": 1,
                "title": "write report",
                "done": True,
                "user_name": "alice",
            },
        )
        self.assertEqual(
            [row["user_name"] for row in joined],
            ["alice", "alice", "bob"],
        )

    def test_join_excludes_tasks_without_user(self) -> None:
        """An inner JOIN drops rows whose owner does not exist."""
        self.conn.execute(
            "INSERT INTO tasks (title, done, user_id) "
            "VALUES ('orphan', 0, 999)"
        )
        self.conn.commit()
        joined = tasks_with_users(self.conn)
        self.assertEqual(len(joined), 3)
        self.assertNotIn("orphan", [row["title"] for row in joined])

    def test_task_counts_include_users_without_tasks(self) -> None:
        """The LEFT JOIN keeps users with a zero task count."""
        counts = user_task_counts(self.conn)
        self.assertEqual(
            counts,
            [
                {"user_id": 1, "user_name": "alice", "task_count": 2},
                {"user_id": 2, "user_name": "bob", "task_count": 1},
                {"user_id": 3, "user_name": "carol", "task_count": 0},
            ],
        )

    def test_counts_match_join_results(self) -> None:
        """Aggregated counts agree with the row-level JOIN."""
        joined = tasks_with_users(self.conn)
        counts = user_task_counts(self.conn)
        by_name = {row["user_name"]: row["task_count"]
                   for row in counts}
        manual: dict[str, int] = {}
        for row in joined:
            manual[row["user_name"]] = manual.get(
                row["user_name"], 0
            ) + 1
        for name, count in manual.items():
            self.assertEqual(by_name[name], count)
        self.assertEqual(by_name["carol"], 0)


if __name__ == "__main__":
    unittest.main()
