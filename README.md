# snip

A developer code snippet manager for the terminal.

## Features

- **Add snippets**: Save code snippets with title, language, tags, and description
- **Search**: Full-text search across titles, descriptions, and code
- **Filter**: Filter snippets by programming language and tags
- **Copy to clipboard**: Quickly copy snippet code to your clipboard
- **Export/Import**: Backup and restore snippets in JSON format
- **Statistics**: View statistics about your snippet collection
- **SQLite backend**: All data stored locally in SQLite database

## Installation

### From Source

```bash
git clone https://github.com/paulhong/snip.git
cd snip
pip install -e ".[dev]"
```

### Requirements

- Python 3.8+
- Dependencies:
  - click >= 8.1.0
  - rich >= 13.0.0
  - pygments >= 2.15.0
  - pyperclip >= 1.8.0

## Usage

### Basic Commands

#### Add a snippet
```bash
snip add --title "Python Loop" --language python -d "Example for loop" --tags "python,loops"
# Then paste your code and press Ctrl+D when done
```

Or from a file:
```bash
snip add --title "Hello World" --language python --file path/to/code.py
```

#### List snippets
```bash
snip list
snip list --language python
snip list --tag loops
```

#### Show snippet details
```bash
snip show 1
```

#### Search snippets
```bash
snip search "def function"
```

#### Copy to clipboard
```bash
snip copy 1
```

#### Delete a snippet
```bash
snip delete 1
```

#### Update a snippet
```bash
snip update 1 --title "New Title" --code "new code"
```

#### View statistics
```bash
snip stats
```

#### Export snippets
```bash
snip export --output backup.json
```

#### Import snippets
```bash
snip import --file backup.json
```

## Development

### Setup Development Environment

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=snip --cov-report=html
```

### Project Structure

```
snip/
├── snip/
│   ├── __init__.py
│   ├── cli.py          # Click CLI commands
│   ├── db.py           # Database initialization
│   ├── models.py       # Snippet model
│   └── repository.py   # Data access layer
├── tests/
│   ├── test_cli.py
│   ├── test_db.py
│   └── test_repository.py
├── pyproject.toml
└── README.md
```

## Architecture

### Repository Pattern

The project uses the Repository pattern to encapsulate data access:

- **SnippetRepository**: Manages all database operations for snippets
- **Snippet Model**: Represents a single code snippet
- **SQLite Database**: Local persistent storage with FTS5 full-text search

### Database Schema

```sql
CREATE TABLE snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'text',
    tags TEXT DEFAULT '',
    description TEXT DEFAULT '',
    code TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE snippets_fts USING fts5(
    title,
    description,
    code,
    content=snippets,
    content_rowid=id
);
```

## Testing

The project includes comprehensive test coverage (88%+):

- **Unit Tests**: Test individual repository operations
- **Integration Tests**: Test CLI commands with in-memory database
- **Database Tests**: Test schema initialization and connection management

Run tests with coverage:
```bash
pytest --cov=snip --cov-report=term-missing
```

## License

MIT License - see LICENSE file for details

## Author

Paul Hong (paul@secuware.co.kr)
