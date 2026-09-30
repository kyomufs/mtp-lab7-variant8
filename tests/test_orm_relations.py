"""Tests for ORM relations between users and tasks (advanced No. 1)."""

import unittest

from lab7.orm_relations import (
    create_all,
    create_task_for_user,
    make_engine,
    open_session,
    tasks_of_user,
)


class OrmRelationsTests(unittest.TestCase):
    """Checks for the ``lab7.orm_relations`` module."""

    def setUp(self) -> None:
        """Create an in-memory engine with both tables."""
        self.engine = make_engine()
        create_all(self.engine)

    def tearDown(self) -> None:
        """Dispose the engine."""
        self.engine.dispose()

    def test_create_task_creates_missing_user(self) -> None:
        """An unknown username is registered automatically."""
        with open_session(self.engine) as session:
            task = create_task_for_user(session, "alice",
                                        "write report")
            self.assertEqual(task.owner.name, "alice")
            self.assertEqual(task.user_id, task.owner.id)
            self.assertFalse(task.done)

    def test_tasks_of_user_returns_owned_tasks_only(self) -> None:
        """Each user sees exactly the tasks created for them."""
        with open_session(self.engine) as session:
            create_task_for_user(session, "alice", "write report")
            create_task_for_user(session, "alice", "review code")
            create_task_for_user(session, "bob", "deploy service")
            alice = [
                task.title
                for task in tasks_of_user(session, "alice")
            ]
            bob = [
                task.title for task in tasks_of_user(session, "bob")
            ]
            self.assertEqual(
                alice, ["write report", "review code"]
            )
            self.assertEqual(bob, ["deploy service"])

    def test_tasks_of_unknown_user_is_empty(self) -> None:
        """A name without rows yields an empty task list."""
        with open_session(self.engine) as session:
            create_task_for_user(session, "alice", "write report")
            self.assertEqual(tasks_of_user(session, "ghost"), [])

    def test_relation_is_loaded_eagerly(self) -> None:
        """``selectinload`` fills the collection without extra work."""
        with open_session(self.engine) as session:
            create_task_for_user(session, "alice", "write report")
            session.expire_all()
            tasks = tasks_of_user(session, "alice")
            # The owner back-reference is usable right away.
            self.assertEqual(tasks[0].owner.name, "alice")
            self.assertTrue(len(tasks) >= 1)

    def test_relationship_back_populates(self) -> None:
        """``User.tasks`` and ``Task.owner`` reference each other."""
        with open_session(self.engine) as session:
            task = create_task_for_user(session, "alice",
                                        "write report")
            user = task.owner
            self.assertIn(task, list(user.tasks))


if __name__ == "__main__":
    unittest.main()
