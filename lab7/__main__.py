"""Demo entry point: run ``python -m lab7``."""

from typing import Any

from lab7 import orm_models, orm_relations, reports, sqlite_tasks
from lab7.cache import cached


def demo_sqlite_tasks() -> None:
    """Medium task 4: insert, update and list rows with sqlite3."""
    conn = sqlite_tasks.connect()
    sqlite_tasks.create_schema(conn)
    first = sqlite_tasks.insert_task(conn, "write report")
    second = sqlite_tasks.insert_task(conn, "review code")
    print("insert_task ->", first, second)
    print(
        "update_task(first, done=True) ->",
        sqlite_tasks.update_task(conn, first, done=True),
    )
    print(
        "update_task(999, title='ghost') ->",
        sqlite_tasks.update_task(conn, 999, title="ghost"),
    )
    print("list_tasks ->", sqlite_tasks.list_tasks(conn))
    conn.close()


def demo_reports() -> None:
    """Medium task 8: JOIN and GROUP BY reports over two tables."""
    conn = sqlite_tasks.connect()
    reports.create_schema_two_tables(conn)
    reports.seed(conn)
    print("tasks_with_users (JOIN):")
    for row in reports.tasks_with_users(conn):
        print("   ", row)
    print("user_task_counts (LEFT JOIN + GROUP BY):")
    for row in reports.user_task_counts(conn):
        print("   ", row)
    conn.close()


def demo_orm_models() -> None:
    """Medium task 10: one table through SQLAlchemy ORM."""
    engine = orm_models.make_engine()
    orm_models.create_all(engine)
    with orm_models.open_session(engine) as session:
        orm_models.create_task(session, "write report")
        orm_models.create_task(session, "review code")
        tasks = orm_models.list_tasks(session)
        print("list_tasks ->", tasks)
    engine.dispose()


def demo_orm_relations() -> None:
    """Advanced task 1: users and tasks linked by a relationship."""
    engine = orm_relations.make_engine()
    orm_relations.create_all(engine)
    with orm_relations.open_session(engine) as session:
        orm_relations.create_task_for_user(
            session, "alice", "write report"
        )
        orm_relations.create_task_for_user(
            session, "alice", "review code"
        )
        orm_relations.create_task_for_user(
            session, "bob", "deploy service"
        )
        tasks = orm_relations.tasks_of_user(session, "alice")
        print("tasks_of_user('alice') ->", tasks)
        print("tasks_of_user('ghost') ->",
              orm_relations.tasks_of_user(session, "ghost"))
    engine.dispose()


def demo_cache() -> None:
    """Advanced task 8: repeated queries served from the cache."""
    conn = sqlite_tasks.connect()
    reports.create_schema_two_tables(conn)
    reports.seed(conn)
    executions: list[int] = []

    @cached(ttl=60.0)
    def query(user_name: str) -> list[dict[str, Any]]:
        """Return tasks of one user, counting real executions."""
        executions.append(1)
        rows = reports.tasks_with_users(conn)
        return [
            row for row in rows if row["user_name"] == user_name
        ]

    for _ in range(3):
        query("alice")
    print("query('alice') called 3 times, executed ->",
          len(executions))
    print("cache_info ->", query.cache_info())
    query.cache_clear()
    print("after cache_clear, cache_info ->", query.cache_info())
    conn.close()


def main() -> None:
    """Run every variant task on in-memory databases."""
    print("Medium tasks")
    demo_sqlite_tasks()
    demo_reports()
    demo_orm_models()
    print("Advanced tasks")
    demo_orm_relations()
    demo_cache()


if __name__ == "__main__":
    main()
