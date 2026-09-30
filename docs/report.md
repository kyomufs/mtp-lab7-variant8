# Отчёт по лабораторной работе №7

Самодуров Матвей Николаевич, группа 221341, вариант 8.

Тема: работа с СУБД в Python — стандартная библиотека `sqlite3`
и ORM SQLAlchemy 2.0.

## Средняя сложность

- **№4 Обновить запись** — `lab7/sqlite_tasks.py`: подключение
  `connect(db_path=":memory:")` с `row_factory=sqlite3.Row`,
  `create_schema`, `insert_task`, `update_task`, `list_tasks`.
  Идея обновления: функция собирает список присваиваний только из
  белого списка фрагментов `"title = ?"` и `"done = ?"`, а значения
  (заголовок и `0`/`1` для флага) передаются в запрос исключительно
  параметрами `?` — SQL-строка не собирается f-строками и данные
  пользователя в неё не попадают.  Возвращается `cursor.rowcount > 0`,
  поэтому несуществующий `id` даёт `False`; если оба поля равны
  `None`, `UPDATE` не выполняется и результат лишь сообщает,
  существует ли строка.  `list_tasks` приводит `done` к `bool`.

- **№8 Выполнить JOIN** — `lab7/reports.py`:
  `create_schema_two_tables` создаёт `users` и `tasks` со связью
  `FOREIGN KEY user_id REFERENCES users(id)`, `seed` наполняет таблицы
  (пользователь `carol` намеренно без задач).
  `tasks_with_users` выполняет `SELECT ... FROM tasks JOIN users ON
  tasks.user_id = users.id` — в каждой строке отчёта появляется имя
  владельца; внутреннее соединение не выводит «осиротевшие» задачи.
  `user_task_counts` использует `LEFT JOIN ... GROUP BY users.id` —
  агрегат `COUNT(tasks.id)` для пользователя без задач равен 0, и он
  всё равно присутствует в результате.

- **№10 SQLAlchemy для одной таблицы** — `lab7/orm_models.py`:
  объявительный базовый класс `Base(DeclarativeBase)` и модель
  `Task` с `Mapped[int]`/`Mapped[str]`/`Mapped[bool]` и
  `mapped_column`; `make_engine(url="sqlite+pysqlite:///:memory:")`,
  `create_all(engine)` через `Base.metadata.create_all`,
  `create_task(session, title)` (`add` → `commit` → `refresh`),
  `list_tasks(session)` через `select(Task).order_by(Task.id)`;
  сессии создаются штатным `sessionmaker` в `open_session`.

## Повышенная сложность

- **№1 SQLAlchemy с несколькими таблицами (связь)** —
  `lab7/orm_relations.py`: классы `User` и `Task` связаны
  `relationship(back_populates=...)`, коллекция
  `User.tasks: Mapped[list["Task"]]` упорядочена по `Task.id`.
  `create_task_for_user(session, username, title)` ищет пользователя
  по точному имени и при отсутствии создаёт его (`flush` перед
  вставкой задачи, чтобы внешний ключ был заполнен).
  `tasks_of_user(session, username)` выбирает пользователя
  `select(User).where(...).options(selectinload(User.tasks))` —
  вся коллекция задач подгружается одним дополнительным `SELECT`
  вместо ленивой загрузки по одному объекту; неизвестное имя даёт
  пустой список.

- **№8 Кэширование запросов** — `lab7/cache.py`: декоратор
  `cached(ttl: float | None = None)` оборачивает функции-запросы.
  Ключ кэша — неизменяемые аргументы вызова (позиционные, при
  наличии и именованные), поэтому немутабельный аргумент приводит к
  `TypeError`.  Время жизни записи меряется `time.monotonic()`:
  при `ttl=None` запись живёт вечно, истёкшая запись удаляется и
  запрос выполняется заново (промах).  У обёртки есть атрибуты
  `cache_info()` (`hits`, `misses`, `currsize`) и `cache_clear()`,
  который чистит хранилище и обнуляет счётчики.

## Проверки

Все команды выполнялись из корня репозитория; вывод ниже —
фактический stdout команд.

### Демонстрация

```text
$ uv run --with sqlalchemy python -m lab7
Medium tasks
insert_task -> 1 2
update_task(first, done=True) -> True
update_task(999, title='ghost') -> False
list_tasks -> [{'id': 1, 'title': 'write report', 'done': True}, {'id': 2, 'title': 'review code', 'done': False}]
tasks_with_users (JOIN):
    {'id': 1, 'title': 'write report', 'done': True, 'user_name': 'alice'}
    {'id': 2, 'title': 'review code', 'done': False, 'user_name': 'alice'}
    {'id': 3, 'title': 'deploy service', 'done': False, 'user_name': 'bob'}
user_task_counts (LEFT JOIN + GROUP BY):
    {'user_id': 1, 'user_name': 'alice', 'task_count': 2}
    {'user_id': 2, 'user_name': 'bob', 'task_count': 1}
    {'user_id': 3, 'user_name': 'carol', 'task_count': 0}
list_tasks -> [Task(id=1, title='write report', done=False), Task(id=2, title='review code', done=False)]
Advanced tasks
tasks_of_user('alice') -> [Task(id=1, title='write report', user_id=1), Task(id=2, title='review code', user_id=1)]
tasks_of_user('ghost') -> []
query('alice') called 3 times, executed -> 1
cache_info -> CacheInfo(hits=2, misses=1, currsize=1)
after cache_clear, cache_info -> CacheInfo(hits=0, misses=0, currsize=0)
```

### Тесты

```text
$ uv run --with sqlalchemy --with flake8 python -m unittest discover -s tests -v
test_cache_clear_forces_recomputation (test_cache.CacheTests.test_cache_clear_forces_recomputation)
After ``cache_clear`` the next call is a miss again. ... ok
test_cached_value_equals_fresh_result (test_cache.CacheTests.test_cached_value_equals_fresh_result)
The cached answer matches an uncached computation. ... ok
test_different_arguments_use_different_entries (test_cache.CacheTests.test_different_arguments_use_different_entries)
Distinct arguments are cached independently. ... ok
test_repeated_calls_execute_query_once (test_cache.CacheTests.test_repeated_calls_execute_query_once)
Three identical calls run one query and record two hits. ... ok
test_ttl_expiry_triggers_recomputation (test_cache.CacheTests.test_ttl_expiry_triggers_recomputation)
An entry older than ``ttl`` is recomputed on access. ... ok
test_ttl_keeps_entry_while_fresh (test_cache.CacheTests.test_ttl_keeps_entry_while_fresh)
A fresh entry is served without calling the query. ... ok
test_unhashable_argument_raises_type_error (test_cache.CacheTests.test_unhashable_argument_raises_type_error)
Only immutable arguments can form a cache key. ... ok
test_create_task_persists_defaults (test_orm_models.OrmModelsTests.test_create_task_persists_defaults)
A new task gets an id and the ``done`` flag is false. ... ok
test_data_survives_between_sessions (test_orm_models.OrmModelsTests.test_data_survives_between_sessions)
Committed rows are visible to a second session. ... ok
test_default_engine_is_in_memory_sqlite (test_orm_models.OrmModelsTests.test_default_engine_is_in_memory_sqlite)
``make_engine`` defaults to an in-memory SQLite URL. ... ok
test_done_flag_round_trip (test_orm_models.OrmModelsTests.test_done_flag_round_trip)
Boolean column stores and reads back as a real bool. ... ok
test_list_tasks_keeps_insertion_order (test_orm_models.OrmModelsTests.test_list_tasks_keeps_insertion_order)
Tasks are returned in the order they were created. ... ok
test_open_session_returns_session (test_orm_models.OrmModelsTests.test_open_session_returns_session)
The helper returns a usable ORM session. ... ok
test_create_task_creates_missing_user (test_orm_relations.OrmRelationsTests.test_create_task_creates_missing_user)
An unknown username is registered automatically. ... ok
test_relation_is_loaded_eagerly (test_orm_relations.OrmRelationsTests.test_relation_is_loaded_eagerly)
``selectinload`` fills the collection without extra work. ... ok
test_relationship_back_populates (test_orm_relations.OrmRelationsTests.test_relationship_back_populates)
``User.tasks`` and ``Task.owner`` reference each other. ... ok
test_tasks_of_unknown_user_is_empty (test_orm_relations.OrmRelationsTests.test_tasks_of_unknown_user_is_empty)
A name without rows yields an empty task list. ... ok
test_tasks_of_user_returns_owned_tasks_only (test_orm_relations.OrmRelationsTests.test_tasks_of_user_returns_owned_tasks_only)
Each user sees exactly the tasks created for them. ... ok
test_counts_match_join_results (test_reports.ReportsTests.test_counts_match_join_results)
Aggregated counts agree with the row-level JOIN. ... ok
test_join_excludes_tasks_without_user (test_reports.ReportsTests.test_join_excludes_tasks_without_user)
An inner JOIN drops rows whose owner does not exist. ... ok
test_join_returns_owner_name_per_task (test_reports.ReportsTests.test_join_returns_owner_name_per_task)
Every task row carries the name of its owner. ... ok
test_task_counts_include_users_without_tasks (test_reports.ReportsTests.test_task_counts_include_users_without_tasks)
The LEFT JOIN keeps users with a zero task count. ... ok
test_insert_and_list (test_sqlite_tasks.SqliteTasksTests.test_insert_and_list)
Inserted rows are returned as dictionaries with ids. ... ok
test_quoted_title_is_not_sql (test_sqlite_tasks.SqliteTasksTests.test_quoted_title_is_not_sql)
Quotes in the title are stored literally, not executed. ... ok
test_update_missing_row_returns_false (test_sqlite_tasks.SqliteTasksTests.test_update_missing_row_returns_false)
Updating an unknown identifier reports failure. ... ok
test_update_single_column_keeps_the_other (test_sqlite_tasks.SqliteTasksTests.test_update_single_column_keeps_the_other)
Passing only ``done`` keeps the original title. ... ok
test_update_title_and_done (test_sqlite_tasks.SqliteTasksTests.test_update_title_and_done)
Both columns change and the function reports success. ... ok
test_update_without_fields_checks_existence (test_sqlite_tasks.SqliteTasksTests.test_update_without_fields_checks_existence)
With no fields the result reports row existence only. ... ok

----------------------------------------------------------------------
Ran 28 tests in 0.112s

OK
```

### Стиль кода

```text
$ uv run --with flake8 flake8 lab7 tests
```

Вывод команды пуст, код возврата `0` — flake8 (max-line-length = 79
из `setup.cfg`) не нашёл нарушений.

### CI

`.github/workflows/python-checks.yml` запускает те же проверки
на Python 3.12 и 3.13 (matrix-стратегия): установка
`requirements-dev.txt`, `flake8 lab7 tests`, `compileall`
и `python -m unittest discover -s tests -v`.
