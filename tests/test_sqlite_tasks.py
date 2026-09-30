"""Tests for the sqlite3 single-table task (medium task No. 4)."""

import unittest

from lab7.sqlite_tasks import (
    connect,
    create_schema,
    insert_task,
    list_tasks,
    update_task,
)


class SqliteTasksTests(unittest.TestCase):
    """Checks for the ``lab7.sqlite_tasks`` module."""

    def setUp(self) -> None:
        """Create an empty in-memory database for every test."""
        self.conn = connect()
        create_schema(self.conn)

    def tearDown(self) -> None:
        """Close the in-memory database."""
        self.conn.close()

    def test_insert_and_list(self) -> None:
        """Inserted rows are returned as dictionaries with ids."""
        first = insert_task(self.conn, "write report")
        second = insert_task(self.conn, "review code", done=True)
        self.assertEqual(
            list_tasks(self.conn),
            [
                {"id": first, "title": "write report", "done": False},
                {"id": second, "title": "review code", "done": True},
            ],
        )

    def test_update_title_and_done(self) -> None:
        """Both columns change and the function reports success."""
        task_id = insert_task(self.conn, "write report")
        self.assertTrue(
            update_task(self.conn, task_id, title="send report",
                        done=True)
        )
        self.assertEqual(
            list_tasks(self.conn),
            [
                {
                    "id": task_id,
                    "title": "send report",
                    "done": True,
                },
            ],
        )

    def test_update_missing_row_returns_false(self) -> None:
        """Updating an unknown identifier reports failure."""
        insert_task(self.conn, "write report")
        self.assertFalse(
            update_task(self.conn, 999, title="ghost task")
        )
        self.assertEqual(len(list_tasks(self.conn)), 1)

    def test_update_single_column_keeps_the_other(self) -> None:
        """Passing only ``done`` keeps the original title."""
        task_id = insert_task(self.conn, "write report", done=True)
        self.assertTrue(update_task(self.conn, task_id, done=False))
        tasks = list_tasks(self.conn)
        self.assertEqual(tasks[0]["title"], "write report")
        self.assertFalse(tasks[0]["done"])

    def test_update_without_fields_checks_existence(self) -> None:
        """With no fields the result reports row existence only."""
        task_id = insert_task(self.conn, "write report")
        self.assertTrue(update_task(self.conn, task_id))
        self.assertFalse(update_task(self.conn, 42))
        self.assertEqual(len(list_tasks(self.conn)), 1)

    def test_quoted_title_is_not_sql(self) -> None:
        """Quotes in the title are stored literally, not executed."""
        title = "O'Brien; DROP TABLE tasks; --"
        task_id = insert_task(self.conn, title)
        self.assertTrue(update_task(self.conn, task_id, title=title))
        self.assertEqual(list_tasks(self.conn)[0]["title"], title)


if __name__ == "__main__":
    unittest.main()
