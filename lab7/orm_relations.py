"""SQLAlchemy 2.0 models with a ``users`` to ``tasks`` relationship."""

from sqlalchemy import Boolean, ForeignKey, String, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    selectinload,
    sessionmaker,
)


class Base(DeclarativeBase):
    """Declarative base class for the relational ORM models."""


class User(Base):
    """One row of the ``users`` table."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="owner",
        lazy="select",
        order_by="Task.id",
    )

    def __repr__(self) -> str:
        """Return a developer-readable representation."""
        return f"User(id={self.id!r}, name={self.name!r})"


class Task(Base):
    """One row of the ``tasks`` table owned by a :class:`User`."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    done: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    owner: Mapped[User] = relationship(back_populates="tasks")

    def __repr__(self) -> str:
        """Return a developer-readable representation."""
        return (
            f"Task(id={self.id!r}, title={self.title!r}, "
            f"user_id={self.user_id!r})"
        )


def make_engine(url: str = "sqlite+pysqlite:///:memory:") -> Engine:
    """Create a database engine; the default is an in-memory SQLite."""
    return create_engine(url)


def create_all(engine: Engine) -> None:
    """Create the ``users`` and ``tasks`` tables."""
    Base.metadata.create_all(engine)


def open_session(engine: Engine) -> Session:
    """Open one ORM session bound to ``engine`` via ``sessionmaker``."""
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return factory()


def create_task_for_user(
    session: Session, username: str, title: str
) -> Task:
    """Create ``title`` for ``username``, creating the user if needed.

    The user is looked up by exact name; when no such user exists a
    new one is inserted first, so the foreign key is always satisfied.
    """
    user = session.scalar(
        select(User).where(User.name == username)
    )
    if user is None:
        user = User(name=username)
        session.add(user)
        session.flush()
    task = Task(title=title, owner=user)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def tasks_of_user(session: Session, username: str) -> list[Task]:
    """Return the tasks of ``username`` ordered by identifier.

    The ``User.tasks`` collection is loaded eagerly with
    ``selectinload``: one extra ``SELECT`` fetches all related tasks
    in a single statement instead of lazy-loading them one by one.
    An unknown user yields an empty list.
    """
    statement = (
        select(User)
        .where(User.name == username)
        .options(selectinload(User.tasks))
    )
    user = session.scalar(statement)
    if user is None:
        return []
    return list(user.tasks)
