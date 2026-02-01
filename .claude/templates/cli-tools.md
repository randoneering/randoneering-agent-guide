# CLI Tool Project

## Project Context

**Project Name:** [Tool Name]

**Description:** [What this CLI does]

**Tech Stack:**
- Python 3.11+
- Click or Typer (CLI framework)
- Rich (terminal output)

---

## Project Structure

```
src/
├── cli/
│   ├── __init__.py
│   ├── main.py           # Entry point, command groups
│   ├── commands/         # Subcommand modules
│   │   ├── __init__.py
│   │   ├── init.py
│   │   └── run.py
│   └── utils/
│       ├── config.py     # Config file handling
│       └── output.py     # Formatted output helpers
tests/
├── conftest.py
├── test_commands.py
└── test_utils.py
pyproject.toml
```

---

## Development Guidelines

### Package Management

```bash
uv venv && source .venv/bin/activate
uv sync
uv add click  # or typer
uv add rich
uv add --dev pytest pytest-cov
```

### Entry Point Setup

```toml
# pyproject.toml
[project.scripts]
mytool = "cli.main:main"
```

### Install for Development

```bash
uv pip install -e .
mytool --help
```

---

## CLI Patterns (Click)

### Basic Structure

```python
# cli/main.py
import click

@click.group()
@click.version_option()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def main(ctx, verbose):
    """My CLI tool description."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose

@main.command()
@click.argument('name')
@click.option('--count', '-c', default=1, help='Number of times')
@click.pass_context
def greet(ctx, name, count):
    """Greet someone."""
    for _ in range(count):
        click.echo(f'Hello, {name}!')

if __name__ == '__main__':
    main()
```

### Subcommand Groups

```python
# cli/commands/db.py
import click

@click.group()
def db():
    """Database commands."""
    pass

@db.command()
def migrate():
    """Run migrations."""
    click.echo('Running migrations...')

@db.command()
def seed():
    """Seed database."""
    click.echo('Seeding...')

# In main.py
from cli.commands.db import db
main.add_command(db)
```

### Input/Output

```python
# Prompts
name = click.prompt('Enter your name')
password = click.prompt('Password', hide_input=True)
confirm = click.confirm('Continue?', default=True)

# Colored output
click.secho('Success!', fg='green', bold=True)
click.secho('Warning!', fg='yellow')
click.secho('Error!', fg='red', err=True)

# Progress bar
with click.progressbar(items, label='Processing') as bar:
    for item in bar:
        process(item)
```

### File Arguments

```python
@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def convert(input_file, output_file):
    """Convert INPUT_FILE to OUTPUT_FILE."""
    pass

# Or use File type for automatic open/close
@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w'))
def process(input, output):
    output.write(input.read().upper())
```

---

## CLI Patterns (Typer)

### Basic Structure

```python
# cli/main.py
import typer
from typing import Optional

app = typer.Typer(help="My CLI tool description.")

@app.command()
def greet(
    name: str,
    count: int = typer.Option(1, "--count", "-c", help="Number of times"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Greet someone."""
    for _ in range(count):
        typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
```

### Subcommand Groups

```python
# cli/commands/db.py
import typer

app = typer.Typer(help="Database commands.")

@app.command()
def migrate():
    """Run migrations."""
    typer.echo("Running migrations...")

# In main.py
from cli.commands import db
app.add_typer(db.app, name="db")
```

---

## Rich Output

```python
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

# Tables
table = Table(title="Results")
table.add_column("Name", style="cyan")
table.add_column("Status", style="green")
table.add_row("Task 1", "Complete")
console.print(table)

# Progress
for item in track(items, description="Processing..."):
    process(item)

# Panels and formatting
from rich.panel import Panel
console.print(Panel("Important message", title="Notice"))

# Errors to stderr
console.print("[red]Error:[/red] Something failed", stderr=True)
```

---

## Configuration Files

```python
# cli/utils/config.py
from pathlib import Path
import tomllib
import json

def get_config_dir() -> Path:
    """Get XDG-compliant config directory."""
    xdg = os.environ.get('XDG_CONFIG_HOME')
    if xdg:
        base = Path(xdg)
    else:
        base = Path.home() / '.config'
    return base / 'mytool'

def load_config() -> dict:
    """Load config from file."""
    config_file = get_config_dir() / 'config.toml'
    if config_file.exists():
        with open(config_file, 'rb') as f:
            return tomllib.load(f)
    return {}

def save_config(config: dict) -> None:
    """Save config to file."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / 'config.toml'
    # Note: tomllib is read-only, use tomli-w for writing
    # Or use JSON for simpler read/write
```

---

## Testing CLI

```python
# tests/test_commands.py
from click.testing import CliRunner
from cli.main import main

def test_greet():
    runner = CliRunner()
    result = runner.invoke(main, ['greet', 'World'])
    assert result.exit_code == 0
    assert 'Hello, World!' in result.output

def test_greet_with_count():
    runner = CliRunner()
    result = runner.invoke(main, ['greet', 'World', '--count', '3'])
    assert result.exit_code == 0
    assert result.output.count('Hello, World!') == 3

def test_file_input(tmp_path):
    """Test command with file input."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        with open('input.txt', 'w') as f:
            f.write('test content')
        result = runner.invoke(main, ['process', 'input.txt'])
        assert result.exit_code == 0
```

### Typer Testing

```python
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()

def test_greet():
    result = runner.invoke(app, ["greet", "World"])
    assert result.exit_code == 0
```

---

## Error Handling

```python
import sys
import click

class ToolError(Exception):
    """Base exception for this tool."""
    pass

def handle_errors(func):
    """Decorator to handle errors gracefully."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ToolError as e:
            click.secho(f"Error: {e}", fg='red', err=True)
            sys.exit(1)
        except KeyboardInterrupt:
            click.echo("\nAborted.", err=True)
            sys.exit(130)
    return wrapper

@main.command()
@handle_errors
def run():
    """Run something that might fail."""
    raise ToolError("Something went wrong")
```

---

## Common Tasks

### Add New Command

1. Create function with `@click.command()` or `@app.command()`
2. Add to command group: `main.add_command(new_cmd)`
3. Add tests in `tests/test_commands.py`
4. Update help text

### Add Subcommand Group

1. Create new file in `cli/commands/`
2. Define group with `@click.group()` or `typer.Typer()`
3. Import and add to main: `main.add_command(group)`

---

## Do Not

- Print to stdout for errors (use stderr via `err=True`)
- Hardcode paths (use `Path.home()` or XDG dirs)
- Swallow exceptions silently
- Use `print()` directly (use click.echo or rich)
- Exit with code 0 on failure

---

## Verification Before Completion

```bash
ruff check --fix .
ruff format .
pyright
pytest --cov=cli

# Manual smoke test
mytool --help
mytool command --help
mytool command arg
```
