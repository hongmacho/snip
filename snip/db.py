import sqlite3
from pathlib import Path


DB_PATH = Path.home() / ".snip" / "snip.db"

_CREATE_SNIPPETS = '''
    CREATE TABLE IF NOT EXISTS snippets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        language TEXT NOT NULL DEFAULT 'text',
        tags TEXT DEFAULT '',
        description TEXT DEFAULT '',
        code TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
'''

_CREATE_FTS = '''
    CREATE VIRTUAL TABLE IF NOT EXISTS snippets_fts USING fts5(
        title,
        description,
        code,
        content=snippets,
        content_rowid=id
    )
'''


def get_db_path() -> Path:
    db_path = DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_db(db_path: str = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = str(get_db_path())
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db_conn(conn: sqlite3.Connection) -> None:
    """Initialize schema on an existing connection (does NOT close it)."""
    cursor = conn.cursor()
    cursor.execute(_CREATE_SNIPPETS)
    cursor.execute(_CREATE_FTS)
    conn.commit()


def init_db(db_path: str = None) -> None:
    if db_path is None:
        db_path = str(get_db_path())
    conn = get_db(db_path)
    init_db_conn(conn)
    conn.close()
