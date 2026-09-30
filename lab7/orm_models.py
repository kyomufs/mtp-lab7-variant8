"""SQLAlchemy 2.0 ORM model for a single ``tasks`` table."""

from sqlalchemy import Boolean, String, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)


class Base(DeclarativeBase):
    """Declarative base class for the ORM models of this lab."""


class Task(Base):
    """One row of the ``tasks`` table."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    done: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    def __repr__(self) -> str:
        """Return a developer-readable representation."""
        return (
            f"Task(id={self.id!r}, title={self.title!r}, "
            f"done={self.done!r})"
        )


def make_engine(url: str = "sqlite+pysqlite:///:memory:") -> Engine:
    """Create a database engine; the default is an in-memory SQLite."""
    return create_engine(url)


def create_all(engine: Engine) -> None:
    """Create the table described by the declarative metadata."""
    Base.metadata.create_all(engine)


def create_task(session: Session, title: str) -> Task:
    """Insert one task and return the persisted ORM object."""
    task = Task(title=title)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def list_tasks(session: Session) -> list[Task]:
    """Return all tasks ordered by identifier."""
    statement = select(Task).order_by(Task.id)
    return list(session.scalars(statement).all())


def open_session(engine: Engine) -> Session:
    """Open one ORM session bound to ``engine`` via ``sessionmaker``."""
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return factory()
