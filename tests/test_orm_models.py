"""Tests for the single-table SQLAlchemy model (medium task No. 10)."""

import unittest

from sqlalchemy.orm import Session

from lab7.orm_models import (
    create_all,
    create_task,
    list_tasks,
    make_engine,
    open_session,
)


class OrmModelsTests(unittest.TestCase):
    """Checks for the ``lab7.orm_models`` module."""

    def setUp(self) -> None:
        """Create an in-memory engine with the ``tasks`` table."""
        self.engine = make_engine()
        create_all(self.engine)

    def tearDown(self) -> None:
        """Dispose the engine."""
        self.engine.dispose()

    def test_create_task_persists_defaults(self) -> None:
        """A new task gets an id and the ``done`` flag is false."""
        with open_session(self.engine) as session:
            task = create_task(session, "write report")
            self.assertIsInstance(task.id, int)
            self.assertEqual(task.title, "write report")
            self.assertFalse(task.done)

    def test_list_tasks_keeps_insertion_order(self) -> None:
        """Tasks are returned in the order they were created."""
        with open_session(self.engine) as session:
            create_task(session, "write report")
            create_task(session, "review code")
            titles = [task.title for task in list_tasks(session)]
            self.assertEqual(
                titles, ["write report", "review code"]
            )

    def test_data_survives_between_sessions(self) -> None:
        """Committed rows are visible to a second session."""
        with open_session(self.engine) as session:
            create_task(session, "write report")
        with open_session(self.engine) as session:
            tasks = list_tasks(session)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].title, "write report")

    def test_done_flag_round_trip(self) -> None:
        """Boolean column stores and reads back as a real bool."""
        with open_session(self.engine) as session:
            task = create_task(session, "deploy service")
            task.done = True
            session.commit()
        with open_session(self.engine) as session:
            tasks = list_tasks(session)
            self.assertIs(tasks[0].done, True)

    def test_default_engine_is_in_memory_sqlite(self) -> None:
        """``make_engine`` defaults to an in-memory SQLite URL."""
        engine = make_engine()
        try:
            self.assertEqual(engine.url.drivername, "sqlite+pysqlite")
            self.assertEqual(engine.url.database, ":memory:")
        finally:
            engine.dispose()

    def test_open_session_returns_session(self) -> None:
        """The helper returns a usable ORM session."""
        session = open_session(self.engine)
        try:
            self.assertIsInstance(session, Session)
            self.assertEqual(list_tasks(session), [])
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
