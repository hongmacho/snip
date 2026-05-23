"""Tests for database initialization and connection."""
import sqlite3
import tempfile
import pytest
from pathlib import Path
from snip.db import init_db, get_db


class TestInitDb:
    """Tests for init_db function."""

    def test_init_db_creates_table(self):
        """Test that init_db creates the snippets table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            init_db(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='snippets'"
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == 'snippets'

    def test_init_db_creates_fts_table(self):
        """Test that init_db creates the FTS5 virtual table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            init_db(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='snippets_fts'"
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == 'snippets_fts'

    def test_init_db_creates_proper_schema(self):
        """Test that snippets table has the correct columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            init_db(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(snippets)")
            columns = {row[1] for row in cursor.fetchall()}
            conn.close()

            expected_columns = {
                'id', 'title', 'language', 'tags', 'description',
                'code', 'created_at', 'updated_at'
            }
            assert columns == expected_columns

    def test_init_db_idempotent(self):
        """Test that calling init_db multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            # Call init_db three times
            init_db(db_path)
            init_db(db_path)
            init_db(db_path)

            # Database should still be valid
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM snippets")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 0

    def test_init_db_with_memory_db(self):
        """Test init_db with in-memory database does not raise."""
        conn = get_db(":memory:")
        init_db_conn = sqlite3.connect(":memory:")
        # Call init_db on a temp file to verify it works without exceptions
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "mem_test.db")
            init_db(db_path)
            verify_conn = get_db(db_path)
            cursor = verify_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='snippets'")
            result = cursor.fetchone()
            verify_conn.close()
        conn.close()
        assert result is not None


class TestGetDb:
    """Tests for get_db function."""

    def test_get_db_returns_connection(self):
        """Test that get_db returns a valid database connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            init_db(db_path)

            conn = get_db(db_path)

            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row
            conn.close()

    def test_get_db_sets_row_factory(self):
        """Test that get_db sets sqlite3.Row as row_factory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            init_db(db_path)

            conn = get_db(db_path)

            assert conn.row_factory == sqlite3.Row
            conn.close()

    def test_get_db_with_memory(self):
        """Test get_db with in-memory database."""
        conn = get_db(":memory:")

        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory == sqlite3.Row
        conn.close()

    def test_get_db_can_execute_queries(self):
        """Test that connection returned by get_db can execute queries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            init_db(db_path)

            conn = get_db(db_path)
            cursor = conn.cursor()

            # Should be able to insert and query
            cursor.execute(
                "INSERT INTO snippets (title, language, code) VALUES (?, ?, ?)",
                ("Test", "python", "print('hello')")
            )
            cursor.execute("SELECT COUNT(*) as count FROM snippets")
            result = cursor.fetchone()

            assert result['count'] == 1
            conn.close()
