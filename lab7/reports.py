"""Two-table schema and JOIN reports on the standard ``sqlite3``."""

import sqlite3
from typing import Any


def create_schema_two_tables(conn: sqlite3.Connection) -> None:
    """Create ``users`` and ``tasks`` tables linked by a foreign key."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            user_id INTEGER NOT NULL
                REFERENCES users (id)
        )
        """
    )
    conn.commit()


def seed(conn: sqlite3.Connection) -> None:
    """Fill both tables with a small demo dataset.

    Three users are created; ``carol`` gets no tasks on purpose so
    that the ``LEFT JOIN`` report can show users without tasks.
    """
    conn.execute("DELETE FROM tasks")
    conn.execute("DELETE FROM users")
    conn.executemany(
        "INSERT INTO users (name) VALUES (?)",
        [("alice",), ("bob",), ("carol",)],
    )
    conn.executemany(
        "INSERT INTO tasks (title, done, user_id) "
        "VALUES (?, ?, (SELECT id FROM users WHERE name = ?))",
        [
            ("write report", 1, "alice"),
            ("review code", 0, "alice"),
            ("deploy service", 0, "bob"),
        ],
    )
    conn.commit()


def tasks_with_users(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return every task joined with the name of its owner."""
    rows = conn.execute(
        """
        SELECT tasks.id, tasks.title, tasks.done, users.name
        FROM tasks
        JOIN users ON tasks.user_id = users.id
        ORDER BY tasks.id
        """
    ).fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
            "user_name": row["name"],
        }
        for row in rows
    ]


def user_task_counts(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """Count tasks per user with a ``LEFT JOIN``.

    Users who own no tasks are still reported, with a zero count.
    """
    rows = conn.execute(
        """
        SELECT users.id, users.name, COUNT(tasks.id) AS task_count
        FROM users
        LEFT JOIN tasks ON tasks.user_id = users.id
        GROUP BY users.id, users.name
        ORDER BY users.id
        """
    ).fetchall()
    return [
        {
            "user_id": row["id"],
            "user_name": row["name"],
            "task_count": row["task_count"],
        }
        for row in rows
    ]
