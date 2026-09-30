"""Single-table task storage built on the standard ``sqlite3`` module."""

import sqlite3
from typing import Any


def connect(db_path: str = ":memory:") -> sqlite3.Connection:
    """Open a database connection with the ``sqlite3.Row`` row factory.

    The default ``":memory:"`` path creates a temporary database that
    exists only while the connection is open.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the ``tasks`` table if it does not exist yet."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()


def insert_task(conn: sqlite3.Connection, title: str,
                done: bool = False) -> int:
    """Insert one task and return the identifier of the new row."""
    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (title, 1 if done else 0),
    )
    conn.commit()
    row_id = cursor.lastrowid
    if row_id is None:
        raise RuntimeError("sqlite3 did not return the inserted row id")
    return int(row_id)


def update_task(conn: sqlite3.Connection, task_id: int,
                title: str | None = None,
                done: bool | None = None) -> bool:
    """Update ``title`` and/or ``done`` of the row with ``task_id``.

    ``None`` means "leave the column unchanged".  Returns ``True`` when
    a row with ``task_id`` exists and ``False`` otherwise.  When both
    fields are ``None`` no ``UPDATE`` statement is issued and the
    return value only reports whether the row exists.

    All values are passed as bound query parameters; the statement
    text is assembled from a fixed whitelist of column assignments.
    """
    assignments: list[str] = []
    params: list[Any] = []
    if title is not None:
        assignments.append("title = ?")
        params.append(title)
    if done is not None:
        assignments.append("done = ?")
        params.append(1 if done else 0)
    if not assignments:
        cursor = conn.execute(
            "SELECT 1 FROM tasks WHERE id = ?", (task_id,)
        )
        return cursor.fetchone() is not None
    # "assignments" only ever contains the literal fragments
    # "title = ?" and "done = ?"; user data stays in "params".
    statement = (
        "UPDATE tasks SET " + ", ".join(assignments) + " WHERE id = ?"
    )
    params.append(task_id)
    cursor = conn.execute(statement, params)
    conn.commit()
    return cursor.rowcount > 0


def count_tasks(conn: sqlite3.Connection) -> int:
    """Return the number of rows stored in the ``tasks`` table."""
    row = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()
    if row is None:
        raise RuntimeError("COUNT(*) always returns one row")
    return int(row[0])


def list_tasks(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return all tasks as dictionaries ordered by identifier."""
    rows = conn.execute(
        "SELECT id, title, done FROM tasks ORDER BY id"
    ).fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
        }
        for row in rows
    ]
