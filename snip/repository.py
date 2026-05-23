import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from snip.models import Snippet
from snip.db import init_db, get_db


class SnippetRepository:
    """Repository for managing Snippet database operations."""

    def __init__(self, db_path: str = None):
        """Initialize repository with optional db_path for testing."""
        self.db_path = db_path
        self._in_memory_conn = None

        if db_path == ":memory:":
            # For in-memory databases, create a persistent connection
            self._in_memory_conn = get_db(":memory:")
            self._init_db_on_connection(self._in_memory_conn)
        else:
            # For file-based database, initialize once
            init_db(db_path)

    def _init_db_on_connection(self, conn: sqlite3.Connection) -> None:
        """Create tables on a given connection."""
        cursor = conn.cursor()

        # Create main snippets table
        cursor.execute('''
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
        ''')

        # Create FTS5 virtual table for full-text search
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS snippets_fts USING fts5(
                title,
                description,
                code,
                content=snippets,
                content_rowid=id
            )
        ''')

        conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection and initialize if needed."""
        if self.db_path == ":memory:":
            return self._in_memory_conn
        return get_db(self.db_path)

    def create(self, snippet: Snippet) -> Snippet:
        """Insert snippet and return with id set."""
        conn = self._get_conn()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO snippets (title, language, tags, description, code, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (snippet.title, snippet.language, snippet.tags, snippet.description, snippet.code, now, now))

        snippet.id = cursor.lastrowid
        conn.commit()

        # Only close file-based connections, not in-memory
        if self.db_path != ":memory:":
            conn.close()

        # Fetch the created record to get timestamps
        return self.get_by_id(snippet.id)

    def get_all(self, language: str = None, tag: str = None) -> List[Snippet]:
        """Get all snippets with optional language and tag filters."""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = 'SELECT * FROM snippets WHERE 1=1'
        params = []

        if language:
            query += ' AND language = ?'
            params.append(language)

        if tag:
            query += ' AND tags LIKE ?'
            params.append(f'%{tag}%')

        query += ' ORDER BY created_at DESC'
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Only close file-based connections, not in-memory
        if self.db_path != ":memory:":
            conn.close()

        return [self._row_to_snippet(row) for row in rows]

    def get_by_id(self, id: int) -> Optional[Snippet]:
        """Get snippet by id, returns None if not found."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM snippets WHERE id = ?', (id,))
        row = cursor.fetchone()

        # Only close file-based connections, not in-memory
        if self.db_path != ":memory:":
            conn.close()

        return self._row_to_snippet(row) if row else None

    def search(self, query: str) -> List[Snippet]:
        """Search snippets by title, description, and code using LIKE."""
        conn = self._get_conn()
        cursor = conn.cursor()

        search_term = f'%{query}%'
        cursor.execute('''
            SELECT * FROM snippets
            WHERE title LIKE ? OR description LIKE ? OR code LIKE ?
            ORDER BY created_at DESC
        ''', (search_term, search_term, search_term))

        rows = cursor.fetchall()

        # Only close file-based connections, not in-memory
        if self.db_path != ":memory:":
            conn.close()

        return [self._row_to_snippet(row) for row in rows]

    def delete(self, id: int) -> bool:
        """Delete snippet by id, returns True if deleted."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM snippets WHERE id = ?', (id,))
        deleted = cursor.rowcount > 0
        conn.commit()

        # Only close file-based connections, not in-memory
        if self.db_path != ":memory:":
            conn.close()

        return deleted

    def update(self, snippet_id: int, **kwargs) -> Optional[Snippet]:
        """Update snippet fields and return updated snippet."""
        # Validate that the snippet exists
        if not self.get_by_id(snippet_id):
            return None

        # Allowed fields to update
        allowed_fields = {'title', 'language', 'tags', 'description', 'code'}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return self.get_by_id(snippet_id)

        conn = self._get_conn()
        cursor = conn.cursor()

        # Build dynamic UPDATE query
        set_clause = ', '.join([f'{field} = ?' for field in update_fields.keys()])
        set_clause += ', updated_at = datetime(\'now\')'
        values = list(update_fields.values()) + [snippet_id]

        cursor.execute(f'''
            UPDATE snippets SET {set_clause} WHERE id = ?
        ''', values)

        conn.commit()

        # Only close file-based connections, not in-memory
        if self.db_path != ":memory:":
            conn.close()

        return self.get_by_id(snippet_id)

    def get_stats(self) -> Dict:
        """Return statistics about snippets."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Total count
        cursor.execute('SELECT COUNT(*) as total FROM snippets')
        total = cursor.fetchone()['total']

        # Count by language
        cursor.execute('SELECT language, COUNT(*) as count FROM snippets GROUP BY language')
        languages = {row['language']: row['count'] for row in cursor.fetchall()}

        # Count by tags
        tags = {}
        cursor.execute('SELECT tags FROM snippets WHERE tags != ""')
        for row in cursor.fetchall():
            for tag in row['tags'].split(','):
                tag = tag.strip()
                if tag:
                    tags[tag] = tags.get(tag, 0) + 1

        # Only close file-based connections, not in-memory
        if self.db_path != ":memory:":
            conn.close()

        return {
            'total': total,
            'languages': languages,
            'tags': tags
        }

    def _row_to_snippet(self, row) -> Snippet:
        """Convert sqlite3.Row to Snippet object."""
        if row is None:
            return None

        return Snippet(
            id=row['id'],
            title=row['title'],
            language=row['language'],
            tags=row['tags'],
            description=row['description'],
            code=row['code'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
