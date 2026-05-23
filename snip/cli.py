import sys
import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import pyperclip
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

from snip.repository import SnippetRepository
from snip.models import Snippet

console = Console()


@click.group()
def cli():
    """snip: A developer code snippet CLI manager."""
    pass


@cli.command()
@click.option("-t", "--title", required=True, help="Snippet title")
@click.option("-l", "--language", default="text", help="Programming language (default: text)")
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("-d", "--description", default="", help="Snippet description")
@click.option("-f", "--file", type=click.Path(exists=True), help="Read code from file")
def add(title: str, language: str, tags: str, description: str, file: Optional[str]):
    """Add a new snippet."""
    try:
        # Read code from file or stdin
        if file:
            code = Path(file).read_text()
        else:
            console.print("Enter code (press Ctrl+D when done):")
            code = sys.stdin.read()

        if not code.strip():
            click.echo("Error: Code cannot be empty", err=True)
            sys.exit(1)

        snippet = Snippet(
            title=title,
            language=language,
            code=code,
            tags=tags,
            description=description
        )

        repo = SnippetRepository(db_path=None)
        created = repo.create(snippet)

        console.print(f"[green]✓ Snippet added with ID {created.id}[/green]")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command("list")
@click.option("-l", "--language", help="Filter by language")
@click.option("-t", "--tag", help="Filter by tag")
def list_snippets(language: Optional[str], tag: Optional[str]):
    """List all snippets."""
    try:
        repo = SnippetRepository(db_path=None)
        snippets = repo.get_all(language=language, tag=tag)

        if not snippets:
            console.print("[yellow]No snippets found[/yellow]")
            return

        table = Table(title="Snippets")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Language", style="green")
        table.add_column("Tags", style="yellow")
        table.add_column("Created", style="blue")

        for snippet in snippets:
            table.add_row(
                str(snippet.id),
                snippet.title,
                snippet.language,
                snippet.tags or "-",
                snippet.created_at or "-"
            )

        console.print(table)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("id", type=int)
def show(id: int):
    """Show snippet details with syntax highlighting."""
    try:
        repo = SnippetRepository(db_path=None)
        snippet = repo.get_by_id(id)

        if not snippet:
            click.echo(f"Error: Snippet #{id} not found", err=True)
            sys.exit(1)

        # Determine lexer for syntax highlighting
        try:
            lexer = get_lexer_by_name(snippet.language)
        except ClassNotFound:
            try:
                lexer = guess_lexer(snippet.code)
            except ClassNotFound:
                lexer = None

        # Format code with syntax highlighting
        if lexer:
            syntax = Syntax(snippet.code, lexer.name, theme="monokai", line_numbers=True)
        else:
            syntax = Syntax(snippet.code, "text", theme="monokai", line_numbers=True)

        # Create panel with snippet details
        title_str = f"[bold cyan]{snippet.title}[/bold cyan] [dim]#{snippet.id}[/dim]"
        panel_content = f"[yellow]Language:[/yellow] {snippet.language}\n"
        if snippet.tags:
            panel_content += f"[yellow]Tags:[/yellow] {snippet.tags}\n"
        if snippet.description:
            panel_content += f"[yellow]Description:[/yellow] {snippet.description}\n"
        panel_content += f"[yellow]Created:[/yellow] {snippet.created_at}\n"
        if snippet.updated_at and snippet.updated_at != snippet.created_at:
            panel_content += f"[yellow]Updated:[/yellow] {snippet.updated_at}\n"

        console.print(Panel(panel_content, title=title_str, expand=False))
        console.print("\n[bold]Code:[/bold]")
        console.print(syntax)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("query")
def search(query: str):
    """Search snippets by title, description, or code."""
    try:
        repo = SnippetRepository(db_path=None)
        snippets = repo.search(query)

        if not snippets:
            console.print("[yellow]No snippets found[/yellow]")
            return

        table = Table(title=f"Search results for '{query}'")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Language", style="green")
        table.add_column("Tags", style="yellow")
        table.add_column("Created", style="blue")

        for snippet in snippets:
            table.add_row(
                str(snippet.id),
                snippet.title,
                snippet.language,
                snippet.tags or "-",
                snippet.created_at or "-"
            )

        console.print(table)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("id", type=int)
def delete(id: int):
    """Delete a snippet."""
    try:
        repo = SnippetRepository(db_path=None)
        deleted = repo.delete(id)

        if not deleted:
            click.echo(f"Error: Snippet #{id} not found", err=True)
            sys.exit(1)

        console.print(f"[green]✓ Snippet #{id} deleted[/green]")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("id", type=int)
def copy(id: int):
    """Copy snippet code to clipboard."""
    try:
        repo = SnippetRepository(db_path=None)
        snippet = repo.get_by_id(id)

        if not snippet:
            click.echo(f"Error: Snippet #{id} not found", err=True)
            sys.exit(1)

        # Try to copy to clipboard
        try:
            pyperclip.copy(snippet.code)
            console.print(f"[green]✓ Snippet #{id} copied to clipboard[/green]")
        except Exception as clipboard_error:
            # Fallback: print to stdout if clipboard fails
            console.print(f"[yellow]⚠ Clipboard unavailable, printing to stdout:[/yellow]")
            click.echo(snippet.code)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command("import")
@click.option("-f", "--file", "filepath", required=True, type=click.Path(exists=True), help="JSON file to import")
def import_snippets(filepath: str):
    """Import snippets from a JSON file."""
    import json
    try:
        data = json.loads(Path(filepath).read_text())
        if not isinstance(data, list):
            click.echo("Error: JSON file must contain a list of snippets", err=True)
            sys.exit(1)

        repo = SnippetRepository(db_path=None)
        imported = 0
        skipped = 0
        for item in data:
            title = item.get("title", "").strip()
            code = item.get("code", "").strip()
            if not title or not code:
                skipped += 1
                continue
            snippet = Snippet(
                title=title,
                language=item.get("language", "text"),
                code=code,
                tags=item.get("tags", ""),
                description=item.get("description", ""),
            )
            repo.create(snippet)
            imported += 1

        console.print(f"[green]✓ Imported {imported} snippet(s), skipped {skipped}[/green]")
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON - {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command("export")
@click.option("-o", "--output", required=True, help="Output JSON file path")
def export_snippets(output: str):
    """Export all snippets to a JSON file."""
    import json
    try:
        repo = SnippetRepository(db_path=None)
        snippets = repo.get_all()

        data = [
            {
                "id": s.id,
                "title": s.title,
                "language": s.language,
                "tags": s.tags,
                "description": s.description,
                "code": s.code,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in snippets
        ]

        Path(output).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        console.print(f"[green]✓ Exported {len(data)} snippet(s) to {output}[/green]")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def stats():
    """Display snippet statistics."""
    try:
        repo = SnippetRepository(db_path=None)
        stats = repo.get_stats()

        # Create stats display
        stats_text = f"[bold cyan]Snippet Statistics[/bold cyan]\n\n"
        stats_text += f"[yellow]Total snippets:[/yellow] {stats['total']}\n"

        if stats['languages']:
            stats_text += f"\n[bold]Languages:[/bold]\n"
            for lang, count in sorted(stats['languages'].items(), key=lambda x: x[1], reverse=True):
                stats_text += f"  {lang}: {count}\n"

        if stats['tags']:
            stats_text += f"\n[bold]Tags:[/bold]\n"
            for tag, count in sorted(stats['tags'].items(), key=lambda x: x[1], reverse=True):
                stats_text += f"  {tag}: {count}\n"

        console.print(Panel(stats_text, expand=False))
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
