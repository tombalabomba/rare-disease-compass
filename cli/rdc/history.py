"""Lokale SQLite-History — akkumulierter, durchsuchbarer Recherche-Speicher.

Jede Abfrage eines Quellen-Subkommandos wird hier abgelegt, sodass sich der
gesammelte Rechercheverlauf über die Zeit auflisten und durchsuchen lässt.

Die Default-DB liegt **außerhalb** des Repos (``~/.rdc/history.db`` oder via
``RCA_HISTORY_DB``) und ist damit gitignored. Tests nutzen ``":memory:"``.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HISTORY_DB_ENV = "RCA_HISTORY_DB"
DEFAULT_DB_DIR = Path.home() / ".rdc"
DEFAULT_DB_NAME = "history.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS queries (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp      TEXT    NOT NULL,
    source         TEXT    NOT NULL,
    command        TEXT    NOT NULL,
    params         TEXT,
    result_summary TEXT,
    result_count   INTEGER,
    raw            TEXT
);
"""


def default_db_path() -> str:
    """Default-Pfad der History-DB (Env überschreibt, sonst ``~/.rdc``)."""
    env = os.environ.get(HISTORY_DB_ENV)
    if env:
        return env
    return str(DEFAULT_DB_DIR / DEFAULT_DB_NAME)


def connect(path: str) -> sqlite3.Connection:
    """Öffnet/erstellt die DB und legt das Schema an.

    ``":memory:"`` wird für Tests akzeptiert; bei einem Datei-Pfad wird das
    übergeordnete Verzeichnis bei Bedarf angelegt.
    """
    if path != ":memory:":
        Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def save_query(
    conn: sqlite3.Connection,
    *,
    source: str,
    command: str,
    params: Mapping[str, Any] | None = None,
    result_summary: str | None = None,
    result_count: int | None = None,
    raw: Any | None = None,
    timestamp: str | None = None,
) -> int:
    """Speichert eine Abfrage samt Ergebnis. Liefert die neue Zeilen-ID."""
    ts = timestamp or datetime.now(UTC).isoformat()
    cur = conn.execute(
        """
        INSERT INTO queries
            (timestamp, source, command, params, result_summary, result_count, raw)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ts,
            source,
            command,
            json.dumps(params, ensure_ascii=False) if params is not None else None,
            result_summary,
            result_count,
            json.dumps(raw, ensure_ascii=False, default=str)
            if raw is not None
            else None,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_queries(
    conn: sqlite3.Connection,
    *,
    limit: int = 20,
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Listet Abfragen zeitlich absteigend (neueste zuerst)."""
    sql = "SELECT * FROM queries"
    args: list[Any] = []
    if source is not None:
        sql += " WHERE source = ?"
        args.append(source)
    sql += " ORDER BY timestamp DESC, id DESC LIMIT ?"
    args.append(limit)
    return [dict(row) for row in conn.execute(sql, args).fetchall()]


def search_queries(
    conn: sqlite3.Connection,
    term: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """LIKE-Suche über Quelle, Command, Params und Result-Summary."""
    like = f"%{term}%"
    rows = conn.execute(
        """
        SELECT * FROM queries
        WHERE source LIKE ?
           OR command LIKE ?
           OR params LIKE ?
           OR result_summary LIKE ?
        ORDER BY timestamp DESC, id DESC
        LIMIT ?
        """,
        (like, like, like, like, limit),
    ).fetchall()
    return [dict(row) for row in rows]
