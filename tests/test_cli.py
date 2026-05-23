"""Tests for CLI commands."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from snip.cli import cli
from snip.repository import SnippetRepository
from snip.models import Snippet


@pytest.fixture
def runner():
    """Create a CliRunner for testing."""
    return CliRunner()


@pytest.fixture
def in_memory_repo():
    """Create an in-memory repository for all tests."""
    repo = SnippetRepository(db_path=":memory:")
    return repo


@pytest.fixture
def mock_repo(in_memory_repo, monkeypatch):
    """Mock SnippetRepository to use in-memory database."""
    monkeypatch.setattr("snip.cli.SnippetRepository", lambda db_path=None: in_memory_repo)
    return in_memory_repo


class TestAddCommand:
    """Tests for the add command."""

    def test_add_snippet_with_file(self, runner, mock_repo):
        """Test adding a snippet from a file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello world')")
            temp_file = f.name

        try:
            result = runner.invoke(cli, [
                'add',
                '-t', 'Hello World',
                '-l', 'python',
                '-f', temp_file
            ])

            assert result.exit_code == 0
            assert "Snippet added" in result.output
            assert "ID" in result.output
        finally:
            Path(temp_file).unlink()

    def test_add_snippet_minimal(self, runner, mock_repo):
        """Test adding a snippet with minimal options."""
        result = runner.invoke(cli, [
            'add',
            '-t', 'Test Snippet'
        ], input="print('test')\n")

        assert result.exit_code == 0
        assert "Snippet added" in result.output

    def test_add_snippet_with_all_options(self, runner, mock_repo):
        """Test adding a snippet with all options."""
        result = runner.invoke(cli, [
            'add',
            '-t', 'Complete Snippet',
            '-l', 'python',
            '-d', 'A complete test snippet',
            '--tags', 'test,example,important'
        ], input="def hello(): pass\n")

        assert result.exit_code == 0
        assert "Snippet added" in result.output

    def test_add_snippet_empty_code_fails(self, runner, mock_repo):
        """Test adding a snippet with empty code fails."""
        result = runner.invoke(cli, [
            'add',
            '-t', 'Empty Code'
        ], input="\n")

        assert result.exit_code == 1
        assert "Code cannot be empty" in result.output

    def test_add_snippet_default_language(self, runner, mock_repo):
        """Test that default language is 'text' when not specified."""
        result = runner.invoke(cli, [
            'add',
            '-t', 'Default Lang'
        ], input="some code\n")

        assert result.exit_code == 0
        # Verify the snippet was created with default language
        snippet = mock_repo.get_all()[0]
        assert snippet.language == "text"

    def test_add_snippet_with_tags(self, runner, mock_repo):
        """Test adding a snippet with tags."""
        result = runner.invoke(cli, [
            'add',
            '-t', 'Tagged Snippet',
            '--tags', 'web,api,rest'
        ], input="code\n")

        assert result.exit_code == 0
        snippet = mock_repo.get_all()[0]
        assert snippet.tags == "web,api,rest"

    def test_add_snippet_with_description(self, runner, mock_repo):
        """Test adding a snippet with description."""
        result = runner.invoke(cli, [
            'add',
            '-t', 'Described',
            '-d', 'This is a useful snippet'
        ], input="code\n")

        assert result.exit_code == 0
        snippet = mock_repo.get_all()[0]
        assert snippet.description == "This is a useful snippet"


class TestListCommand:
    """Tests for the list command."""

    def test_list_empty(self, runner, mock_repo):
        """Test listing when no snippets exist."""
        result = runner.invoke(cli, ['list'])

        assert result.exit_code == 0
        assert "No snippets found" in result.output

    def test_list_with_snippets(self, runner, mock_repo):
        """Test listing snippets."""
        mock_repo.create(Snippet(title="Python Snippet", language="python", code="code1"))
        mock_repo.create(Snippet(title="JS Snippet", language="javascript", code="code2"))

        result = runner.invoke(cli, ['list'])

        assert result.exit_code == 0
        assert "Snippets" in result.output
        assert "Python Snippet" in result.output
        assert "JS Snippet" in result.output

    def test_list_filter_by_language(self, runner, mock_repo):
        """Test listing with language filter."""
        mock_repo.create(Snippet(title="Python1", language="python", code="code1"))
        mock_repo.create(Snippet(title="Python2", language="python", code="code2"))
        mock_repo.create(Snippet(title="JS", language="javascript", code="code3"))

        result = runner.invoke(cli, ['list', '-l', 'python'])

        assert result.exit_code == 0
        assert "Python1" in result.output
        assert "Python2" in result.output
        assert "JS" not in result.output

    def test_list_filter_by_tag(self, runner, mock_repo):
        """Test listing with tag filter."""
        mock_repo.create(Snippet(title="Tagged1", language="python", code="code1", tags="web"))
        mock_repo.create(Snippet(title="Tagged2", language="python", code="code2", tags="web,api"))
        mock_repo.create(Snippet(title="NotTagged", language="python", code="code3", tags=""))

        result = runner.invoke(cli, ['list', '-t', 'web'])

        assert result.exit_code == 0
        assert "Tagged1" in result.output
        assert "Tagged2" in result.output
        assert "NotTagged" not in result.output


class TestShowCommand:
    """Tests for the show command."""

    def test_show_snippet(self, runner, mock_repo):
        """Test showing snippet details."""
        created = mock_repo.create(Snippet(
            title="Test Snippet",
            language="python",
            code="print('hello')",
            description="A test snippet"
        ))

        result = runner.invoke(cli, ['show', str(created.id)])

        assert result.exit_code == 0
        assert "Test Snippet" in result.output
        assert "python" in result.output
        assert "print('hello')" in result.output

    def test_show_nonexistent_fails(self, runner, mock_repo):
        """Test showing non-existent snippet fails."""
        result = runner.invoke(cli, ['show', '999'])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_show_displays_all_fields(self, runner, mock_repo):
        """Test show displays all snippet fields."""
        created = mock_repo.create(Snippet(
            title="Complete",
            language="python",
            code="code",
            description="Description here",
            tags="tag1,tag2"
        ))

        result = runner.invoke(cli, ['show', str(created.id)])

        assert result.exit_code == 0
        assert "Complete" in result.output
        assert "python" in result.output
        assert "Description here" in result.output
        assert "tag1,tag2" in result.output

    def test_show_with_syntax_highlighting(self, runner, mock_repo):
        """Test show includes code formatting."""
        created = mock_repo.create(Snippet(
            title="Syntax Test",
            language="python",
            code="def hello():\n    print('world')"
        ))

        result = runner.invoke(cli, ['show', str(created.id)])

        assert result.exit_code == 0
        assert "def hello():" in result.output


class TestSearchCommand:
    """Tests for the search command."""

    def test_search_found(self, runner, mock_repo):
        """Test search returns matching snippets."""
        mock_repo.create(Snippet(title="Python Loop", language="python", code="for x in y"))
        mock_repo.create(Snippet(title="JS Function", language="javascript", code="function() {}"))

        result = runner.invoke(cli, ['search', 'Python'])

        assert result.exit_code == 0
        assert "Python Loop" in result.output
        assert "JS Function" not in result.output

    def test_search_not_found(self, runner, mock_repo):
        """Test search returns empty when no matches."""
        mock_repo.create(Snippet(title="Test", language="python", code="code"))

        result = runner.invoke(cli, ['search', 'nonexistent'])

        assert result.exit_code == 0
        assert "No snippets found" in result.output

    def test_search_by_code(self, runner, mock_repo):
        """Test search finds snippets by code content."""
        mock_repo.create(Snippet(title="Print Test", language="python", code="print('hello')"))
        mock_repo.create(Snippet(title="Log Test", language="js", code="console.log()"))

        result = runner.invoke(cli, ['search', 'print'])

        assert result.exit_code == 0
        assert "Print Test" in result.output

    def test_search_case_insensitive(self, runner, mock_repo):
        """Test search is case-insensitive."""
        mock_repo.create(Snippet(title="UPPERCASE", language="python", code="code"))

        result = runner.invoke(cli, ['search', 'uppercase'])

        assert result.exit_code == 0
        assert "UPPERCASE" in result.output


class TestDeleteCommand:
    """Tests for the delete command."""

    def test_delete_snippet(self, runner, mock_repo):
        """Test deleting a snippet."""
        created = mock_repo.create(Snippet(title="Delete Me", language="python", code="code"))

        result = runner.invoke(cli, ['delete', str(created.id)])

        assert result.exit_code == 0
        assert "deleted" in result.output
        assert str(created.id) in result.output

    def test_delete_nonexistent_fails(self, runner, mock_repo):
        """Test deleting non-existent snippet fails."""
        result = runner.invoke(cli, ['delete', '999'])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_delete_removes_snippet(self, runner, mock_repo):
        """Test deleted snippet is actually removed."""
        created = mock_repo.create(Snippet(title="Delete Me", language="python", code="code"))
        snippet_id = created.id

        runner.invoke(cli, ['delete', str(snippet_id)])

        result = runner.invoke(cli, ['show', str(snippet_id)])
        assert result.exit_code == 1


class TestCopyCommand:
    """Tests for the copy command."""

    def test_copy_snippet(self, runner, mock_repo):
        """Test copying snippet to clipboard."""
        created = mock_repo.create(Snippet(title="Copy Me", language="python", code="code"))

        with patch('snip.cli.pyperclip.copy') as mock_copy:
            result = runner.invoke(cli, ['copy', str(created.id)])

            assert result.exit_code == 0
            assert "copied" in result.output
            mock_copy.assert_called_once_with("code")

    def test_copy_nonexistent_fails(self, runner, mock_repo):
        """Test copying non-existent snippet fails."""
        result = runner.invoke(cli, ['copy', '999'])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_copy_clipboard_unavailable_fallback(self, runner, mock_repo):
        """Test copy falls back to stdout when clipboard unavailable."""
        created = mock_repo.create(Snippet(title="Test", language="python", code="test_code"))

        with patch('snip.cli.pyperclip.copy', side_effect=Exception("Clipboard error")):
            result = runner.invoke(cli, ['copy', str(created.id)])

            assert result.exit_code == 0
            assert "test_code" in result.output

    def test_copy_copies_correct_code(self, runner, mock_repo):
        """Test copy copies the correct code content."""
        code_content = "def complex_function():\n    return 42"
        created = mock_repo.create(Snippet(title="Complex", language="python", code=code_content))

        with patch('snip.cli.pyperclip.copy') as mock_copy:
            runner.invoke(cli, ['copy', str(created.id)])

            mock_copy.assert_called_once_with(code_content)


class TestStatsCommand:
    """Tests for the stats command."""

    def test_stats_empty_db(self, runner, mock_repo):
        """Test stats on empty database."""
        result = runner.invoke(cli, ['stats'])

        assert result.exit_code == 0
        assert "Statistics" in result.output
        assert "Total snippets: 0" in result.output

    def test_stats_with_snippets(self, runner, mock_repo):
        """Test stats displays correct counts."""
        mock_repo.create(Snippet(title="1", language="python", code="code"))
        mock_repo.create(Snippet(title="2", language="python", code="code"))
        mock_repo.create(Snippet(title="3", language="javascript", code="code"))

        result = runner.invoke(cli, ['stats'])

        assert result.exit_code == 0
        assert "Total snippets: 3" in result.output
        assert "python" in result.output
        assert "javascript" in result.output

    def test_stats_by_language(self, runner, mock_repo):
        """Test stats shows language breakdown."""
        mock_repo.create(Snippet(title="1", language="python", code="code"))
        mock_repo.create(Snippet(title="2", language="python", code="code"))
        mock_repo.create(Snippet(title="3", language="javascript", code="code"))

        result = runner.invoke(cli, ['stats'])

        assert result.exit_code == 0
        assert "Languages:" in result.output or "python" in result.output

    def test_stats_by_tags(self, runner, mock_repo):
        """Test stats shows tag breakdown."""
        mock_repo.create(Snippet(title="1", language="python", code="code", tags="web"))
        mock_repo.create(Snippet(title="2", language="python", code="code", tags="web,api"))

        result = runner.invoke(cli, ['stats'])

        assert result.exit_code == 0
        assert "Tags:" in result.output or "web" in result.output


class TestCliErrorHandling:
    """Tests for error handling in CLI."""

    def test_add_missing_title(self, runner, mock_repo):
        """Test add command fails without title."""
        result = runner.invoke(cli, ['add'], input="code\n")

        assert result.exit_code != 0

    def test_show_missing_id(self, runner, mock_repo):
        """Test show command fails without ID."""
        result = runner.invoke(cli, ['show'])

        assert result.exit_code != 0

    def test_delete_missing_id(self, runner, mock_repo):
        """Test delete command fails without ID."""
        result = runner.invoke(cli, ['delete'])

        assert result.exit_code != 0

    def test_search_missing_query(self, runner, mock_repo):
        """Test search command fails without query."""
        result = runner.invoke(cli, ['search'])

        assert result.exit_code != 0

    def test_copy_missing_id(self, runner, mock_repo):
        """Test copy command fails without ID."""
        result = runner.invoke(cli, ['copy'])

        assert result.exit_code != 0


class TestCliIntegration:
    """Integration tests for CLI."""

    def test_add_and_list_workflow(self, runner, mock_repo):
        """Test adding and listing snippets."""
        result = runner.invoke(cli, [
            'add',
            '-t', 'Test Snippet',
            '-l', 'python'
        ], input="print('test')\n")

        assert result.exit_code == 0

        result = runner.invoke(cli, ['list'])

        assert result.exit_code == 0
        assert "Test Snippet" in result.output

    def test_add_search_and_delete_workflow(self, runner, mock_repo):
        """Test adding, searching, and deleting snippets."""
        # Add
        result = runner.invoke(cli, [
            'add',
            '-t', 'Workflow Test',
            '-l', 'python'
        ], input="code\n")

        assert result.exit_code == 0

        # Search
        result = runner.invoke(cli, ['search', 'Workflow'])

        assert result.exit_code == 0
        assert "Workflow Test" in result.output

        # Get ID from the search result (it should be ID 1)
        created = mock_repo.get_all()[0]

        # Delete
        result = runner.invoke(cli, ['delete', str(created.id)])

        assert result.exit_code == 0

        # Verify it's deleted
        result = runner.invoke(cli, ['list'])
        assert "No snippets found" in result.output

    def test_full_snippet_lifecycle(self, runner, mock_repo):
        """Test complete snippet lifecycle: add, show, search, update, delete."""
        # Add
        result = runner.invoke(cli, [
            'add',
            '-t', 'Lifecycle Test',
            '-d', 'Initial description',
            '-l', 'python'
        ], input="initial_code\n")

        assert result.exit_code == 0

        # Get the snippet
        snippet = mock_repo.get_all()[0]
        snippet_id = snippet.id

        # Show
        result = runner.invoke(cli, ['show', str(snippet_id)])

        assert result.exit_code == 0
        assert "Lifecycle Test" in result.output

        # Search
        result = runner.invoke(cli, ['search', 'Lifecycle'])

        assert result.exit_code == 0
        assert "Lifecycle Test" in result.output

        # Delete
        result = runner.invoke(cli, ['delete', str(snippet_id)])

        assert result.exit_code == 0

        # Verify deletion
        result = runner.invoke(cli, ['show', str(snippet_id)])

        assert result.exit_code == 1


class TestImportExportCommand:
    """Tests for import and export commands."""

    def test_export_empty(self, runner, mock_repo, tmp_path):
        """Test exporting when no snippets exist."""
        output_file = str(tmp_path / "out.json")
        result = runner.invoke(cli, ['export', '-o', output_file])

        assert result.exit_code == 0
        assert "Exported" in result.output

    def test_export_with_snippets(self, runner, mock_repo, tmp_path):
        """Test exporting snippets to JSON."""
        mock_repo.create(Snippet(title="Export Me", language="python", code="x = 1"))
        output_file = str(tmp_path / "out.json")

        result = runner.invoke(cli, ['export', '-o', output_file])

        assert result.exit_code == 0
        assert "Exported 1" in result.output

        import json
        data = json.loads(Path(output_file).read_text())
        assert len(data) == 1
        assert data[0]["title"] == "Export Me"

    def test_import_valid_json(self, runner, mock_repo, tmp_path):
        """Test importing snippets from JSON."""
        import json
        snippets = [
            {"title": "Imported1", "language": "python", "code": "print(1)"},
            {"title": "Imported2", "language": "javascript", "code": "console.log(2)"},
        ]
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(snippets))

        result = runner.invoke(cli, ['import', '-f', str(import_file)])

        assert result.exit_code == 0
        assert "Imported 2" in result.output

    def test_import_skips_invalid_entries(self, runner, mock_repo, tmp_path):
        """Test import skips entries missing title or code."""
        import json
        snippets = [
            {"title": "Valid", "language": "python", "code": "x = 1"},
            {"title": "", "language": "python", "code": "x = 2"},
            {"title": "No Code", "language": "python"},
        ]
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(snippets))

        result = runner.invoke(cli, ['import', '-f', str(import_file)])

        assert result.exit_code == 0
        assert "Imported 1" in result.output
        assert "skipped 2" in result.output

    def test_import_invalid_json(self, runner, mock_repo, tmp_path):
        """Test import fails on invalid JSON."""
        import_file = tmp_path / "bad.json"
        import_file.write_text("not valid json {{{")

        result = runner.invoke(cli, ['import', '-f', str(import_file)])

        assert result.exit_code == 1

    def test_import_non_list_json(self, runner, mock_repo, tmp_path):
        """Test import fails when JSON is not a list."""
        import json
        import_file = tmp_path / "bad.json"
        import_file.write_text(json.dumps({"title": "oops"}))

        result = runner.invoke(cli, ['import', '-f', str(import_file)])

        assert result.exit_code == 1

    def test_export_import_roundtrip(self, runner, mock_repo, tmp_path):
        """Test export then import produces same data."""
        mock_repo.create(Snippet(title="Roundtrip", language="go", code="fmt.Println()", tags="test"))
        output_file = str(tmp_path / "export.json")

        runner.invoke(cli, ['export', '-o', output_file])

        result = runner.invoke(cli, ['import', '-f', output_file])

        assert result.exit_code == 0
        assert "Imported 1" in result.output
