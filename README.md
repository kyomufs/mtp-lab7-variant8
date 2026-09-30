# Лабораторная работа №7

Самодуров Матвей Николаевич, группа 221341, вариант 8, лабораторная №7.

Тема работы: работа с СУБД в Python (стандартная библиотека `sqlite3`
и ORM SQLAlchemy 2.0).

## Задания варианта

**Средняя сложность:**

- №4 — обновить запись (`lab7/sqlite_tasks.py`)
- №8 — выполнить JOIN (`lab7/reports.py`)
- №10 — SQLAlchemy для одной таблицы (`lab7/orm_models.py`)

**Повышенная сложность:**

- №1 — SQLAlchemy с несколькими таблицами, связь (`lab7/orm_relations.py`)
- №8 — кэширование запросов (`lab7/cache.py`)

## Клонирование

```bash
git clone https://github.com/kyomufs/mtp-lab7-variant8.git
cd mtp-lab7-variant8
```

## Запуск

Демонстрация всех заданий на in-memory базе данных:

```bash
uv run --with sqlalchemy python -m lab7
```

## Проверки

```bash
uv run --with sqlalchemy --with flake8 python -m unittest discover -s tests -v
uv run --with sqlalchemy --with flake8 flake8 lab7 tests
```

Зависимости для CI перечислены в `requirements-dev.txt`.

Подробное описание выполнения — в `docs/report.md`.
