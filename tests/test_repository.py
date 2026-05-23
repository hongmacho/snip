"""Tests for SnippetRepository."""
import pytest
from snip.repository import SnippetRepository
from snip.models import Snippet


@pytest.fixture
def repo():
    """Create an in-memory repository for testing."""
    return SnippetRepository(db_path=":memory:")


class TestCreateSnippet:
    """Tests for creating snippets."""

    def test_create_snippet(self, repo):
        """Test creating a snippet returns it with an ID."""
        snippet = Snippet(
            title="Test Snippet",
            language="python",
            code="print('hello')",
            tags="test,example",
            description="A test snippet"
        )

        created = repo.create(snippet)

        assert created.id is not None
        assert created.id > 0
        assert created.title == "Test Snippet"
        assert created.language == "python"
        assert created.code == "print('hello')"
        assert created.tags == "test,example"
        assert created.description == "A test snippet"
        assert created.created_at is not None
        assert created.updated_at is not None

    def test_create_multiple_snippets(self, repo):
        """Test creating multiple snippets assigns unique IDs."""
        snippet1 = Snippet(title="First", language="python", code="code1")
        snippet2 = Snippet(title="Second", language="javascript", code="code2")

        created1 = repo.create(snippet1)
        created2 = repo.create(snippet2)

        assert created1.id != created2.id
        assert created1.id < created2.id

    def test_create_with_defaults(self, repo):
        """Test creating a snippet with default values."""
        snippet = Snippet(title="Simple", language="text", code="simple code")

        created = repo.create(snippet)

        assert created.id is not None
        assert created.tags == ""
        assert created.description == ""
        assert created.language == "text"


class TestGetAllSnippets:
    """Tests for retrieving all snippets."""

    def test_get_all_empty(self, repo):
        """Test get_all returns empty list when no snippets exist."""
        snippets = repo.get_all()

        assert snippets == []

    def test_get_all_returns_all_snippets(self, repo):
        """Test get_all returns all created snippets."""
        snippet1 = Snippet(title="First", language="python", code="code1")
        snippet2 = Snippet(title="Second", language="javascript", code="code2")

        repo.create(snippet1)
        repo.create(snippet2)

        snippets = repo.get_all()

        assert len(snippets) == 2
        assert snippets[0].title == "Second"  # Most recent first
        assert snippets[1].title == "First"

    def test_get_all_ordered_by_created_at(self, repo):
        """Test get_all returns snippets ordered by created_at descending."""
        for i in range(3):
            snippet = Snippet(title=f"Snippet {i}", language="python", code=f"code{i}")
            repo.create(snippet)

        snippets = repo.get_all()

        # Should be in reverse order (newest first)
        assert snippets[0].title == "Snippet 2"
        assert snippets[1].title == "Snippet 1"
        assert snippets[2].title == "Snippet 0"

    def test_get_all_filter_by_language(self, repo):
        """Test get_all filters by language."""
        repo.create(Snippet(title="Python1", language="python", code="code1"))
        repo.create(Snippet(title="Python2", language="python", code="code2"))
        repo.create(Snippet(title="JS1", language="javascript", code="code3"))

        snippets = repo.get_all(language="python")

        assert len(snippets) == 2
        assert all(s.language == "python" for s in snippets)

    def test_get_all_filter_by_language_no_matches(self, repo):
        """Test get_all with language filter returns empty when no matches."""
        repo.create(Snippet(title="Python", language="python", code="code"))

        snippets = repo.get_all(language="ruby")

        assert snippets == []

    def test_get_all_filter_by_tag(self, repo):
        """Test get_all filters by tag."""
        repo.create(Snippet(title="Tagged1", language="python", code="code1", tags="web,python"))
        repo.create(Snippet(title="Tagged2", language="python", code="code2", tags="web,api"))
        repo.create(Snippet(title="NoTag", language="python", code="code3", tags=""))

        snippets = repo.get_all(tag="web")

        assert len(snippets) == 2
        assert all("web" in s.tags for s in snippets)

    def test_get_all_filter_by_tag_partial_match(self, repo):
        """Test get_all tag filter works with partial tag matching."""
        repo.create(Snippet(title="Test", language="python", code="code", tags="python,testing"))

        snippets = repo.get_all(tag="test")

        assert len(snippets) == 1


class TestGetById:
    """Tests for retrieving snippet by ID."""

    def test_get_by_id(self, repo):
        """Test get_by_id returns the correct snippet."""
        created = repo.create(Snippet(title="Test", language="python", code="code"))
        snippet_id = created.id

        retrieved = repo.get_by_id(snippet_id)

        assert retrieved is not None
        assert retrieved.id == snippet_id
        assert retrieved.title == "Test"

    def test_get_by_id_not_found(self, repo):
        """Test get_by_id returns None for non-existent ID."""
        retrieved = repo.get_by_id(999)

        assert retrieved is None

    def test_get_by_id_returns_all_fields(self, repo):
        """Test get_by_id returns all snippet fields."""
        created = repo.create(Snippet(
            title="Full",
            language="python",
            code="print('test')",
            tags="test,example",
            description="Full test"
        ))

        retrieved = repo.get_by_id(created.id)

        assert retrieved.title == "Full"
        assert retrieved.language == "python"
        assert retrieved.code == "print('test')"
        assert retrieved.tags == "test,example"
        assert retrieved.description == "Full test"
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None


class TestSearch:
    """Tests for searching snippets."""

    def test_search_by_title(self, repo):
        """Test search finds snippets by title."""
        repo.create(Snippet(title="Python Loops", language="python", code="for x in y"))
        repo.create(Snippet(title="JavaScript Functions", language="js", code="function() {}"))

        results = repo.search("Python")

        assert len(results) == 1
        assert results[0].title == "Python Loops"

    def test_search_by_code(self, repo):
        """Test search finds snippets by code content."""
        repo.create(Snippet(title="Test1", language="python", code="print('hello')"))
        repo.create(Snippet(title="Test2", language="js", code="console.log('world')"))

        results = repo.search("print")

        assert len(results) == 1
        assert results[0].title == "Test1"

    def test_search_by_description(self, repo):
        """Test search finds snippets by description."""
        repo.create(Snippet(
            title="Snippet1",
            language="python",
            code="x = 1",
            description="Useful utility function"
        ))
        repo.create(Snippet(
            title="Snippet2",
            language="js",
            code="y = 2",
            description="Something else"
        ))

        results = repo.search("utility")

        assert len(results) == 1
        assert results[0].title == "Snippet1"

    def test_search_no_results(self, repo):
        """Test search returns empty list when no matches."""
        repo.create(Snippet(title="Test", language="python", code="code"))

        results = repo.search("nonexistent")

        assert results == []

    def test_search_case_insensitive(self, repo):
        """Test search is case-insensitive."""
        repo.create(Snippet(title="Python Code", language="python", code="code"))

        results = repo.search("python")

        assert len(results) == 1

    def test_search_multiple_matches(self, repo):
        """Test search returns multiple matches."""
        repo.create(Snippet(title="Test1", language="python", code="test code"))
        repo.create(Snippet(title="Test2", language="js", code="test function"))
        repo.create(Snippet(title="Other", language="python", code="other"))

        results = repo.search("test")

        assert len(results) == 2


class TestDelete:
    """Tests for deleting snippets."""

    def test_delete_snippet(self, repo):
        """Test delete removes a snippet."""
        created = repo.create(Snippet(title="Delete Me", language="python", code="code"))

        deleted = repo.delete(created.id)

        assert deleted is True
        assert repo.get_by_id(created.id) is None

    def test_delete_nonexistent_returns_false(self, repo):
        """Test delete returns False for non-existent ID."""
        deleted = repo.delete(999)

        assert deleted is False

    def test_delete_multiple_snippets(self, repo):
        """Test deleting one snippet doesn't affect others."""
        created1 = repo.create(Snippet(title="Keep", language="python", code="code1"))
        created2 = repo.create(Snippet(title="Delete", language="python", code="code2"))

        repo.delete(created2.id)

        assert repo.get_by_id(created1.id) is not None
        assert repo.get_by_id(created2.id) is None


class TestUpdate:
    """Tests for updating snippets."""

    def test_update_title(self, repo):
        """Test updating snippet title."""
        created = repo.create(Snippet(title="Old Title", language="python", code="code"))

        updated = repo.update(created.id, title="New Title")

        assert updated.title == "New Title"
        assert updated.language == "python"
        assert updated.code == "code"

    def test_update_code(self, repo):
        """Test updating snippet code."""
        created = repo.create(Snippet(title="Test", language="python", code="old code"))

        updated = repo.update(created.id, code="new code")

        assert updated.code == "new code"
        assert updated.title == "Test"

    def test_update_multiple_fields(self, repo):
        """Test updating multiple fields at once."""
        created = repo.create(Snippet(
            title="Old",
            language="python",
            code="old",
            tags="old-tag",
            description="Old description"
        ))

        updated = repo.update(
            created.id,
            title="New",
            code="new code",
            tags="new-tag",
            description="New description"
        )

        assert updated.title == "New"
        assert updated.code == "new code"
        assert updated.tags == "new-tag"
        assert updated.description == "New description"

    def test_update_nonexistent_returns_none(self, repo):
        """Test update returns None for non-existent ID."""
        updated = repo.update(999, title="New")

        assert updated is None

    def test_update_updates_timestamp(self, repo):
        """Test update modifies updated_at timestamp."""
        created = repo.create(Snippet(title="Test", language="python", code="code"))

        updated = repo.update(created.id, title="New Title")

        assert updated.updated_at != created.created_at

    def test_update_with_no_fields(self, repo):
        """Test update with no fields returns the current snippet."""
        created = repo.create(Snippet(title="Test", language="python", code="code"))

        updated = repo.update(created.id)

        assert updated.id == created.id
        assert updated.title == created.title

    def test_update_ignores_invalid_fields(self, repo):
        """Test update ignores fields not in allowed list."""
        created = repo.create(Snippet(title="Test", language="python", code="code"))

        # Try to update an invalid field (id)
        updated = repo.update(created.id, id=999, title="New")

        assert updated.id == created.id  # ID should not change
        assert updated.title == "New"


class TestGetStats:
    """Tests for snippet statistics."""

    def test_get_stats_empty_db(self, repo):
        """Test get_stats on empty database."""
        stats = repo.get_stats()

        assert stats['total'] == 0
        assert stats['languages'] == {}
        assert stats['tags'] == {}

    def test_get_stats_total_count(self, repo):
        """Test get_stats returns correct total count."""
        repo.create(Snippet(title="1", language="python", code="code"))
        repo.create(Snippet(title="2", language="python", code="code"))
        repo.create(Snippet(title="3", language="js", code="code"))

        stats = repo.get_stats()

        assert stats['total'] == 3

    def test_get_stats_by_language(self, repo):
        """Test get_stats counts by language."""
        repo.create(Snippet(title="1", language="python", code="code"))
        repo.create(Snippet(title="2", language="python", code="code"))
        repo.create(Snippet(title="3", language="javascript", code="code"))
        repo.create(Snippet(title="4", language="javascript", code="code"))
        repo.create(Snippet(title="5", language="golang", code="code"))

        stats = repo.get_stats()

        assert stats['languages']['python'] == 2
        assert stats['languages']['javascript'] == 2
        assert stats['languages']['golang'] == 1

    def test_get_stats_by_tags(self, repo):
        """Test get_stats counts by tags."""
        repo.create(Snippet(title="1", language="python", code="code", tags="web"))
        repo.create(Snippet(title="2", language="python", code="code", tags="web,api"))
        repo.create(Snippet(title="3", language="js", code="code", tags="api,frontend"))

        stats = repo.get_stats()

        assert stats['tags']['web'] == 2
        assert stats['tags']['api'] == 2
        assert stats['tags']['frontend'] == 1

    def test_get_stats_ignores_empty_tags(self, repo):
        """Test get_stats ignores snippets with empty tags."""
        repo.create(Snippet(title="1", language="python", code="code", tags=""))
        repo.create(Snippet(title="2", language="python", code="code", tags="test"))

        stats = repo.get_stats()

        assert 'test' in stats['tags']
        assert len(stats['tags']) == 1

    def test_get_stats_handles_multiple_tags_per_snippet(self, repo):
        """Test get_stats correctly counts multiple tags per snippet."""
        repo.create(Snippet(title="1", language="python", code="code", tags="a,b,c"))

        stats = repo.get_stats()

        assert stats['tags']['a'] == 1
        assert stats['tags']['b'] == 1
        assert stats['tags']['c'] == 1

    def test_get_stats_with_spaces_in_tags(self, repo):
        """Test get_stats handles tags with spaces correctly."""
        repo.create(Snippet(title="1", language="python", code="code", tags="web, api, test"))

        stats = repo.get_stats()

        assert stats['tags']['web'] == 1
        assert stats['tags']['api'] == 1
        assert stats['tags']['test'] == 1
