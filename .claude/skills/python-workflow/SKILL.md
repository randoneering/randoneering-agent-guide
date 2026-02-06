---
name: python-workflow
description: "Python project workflow guidelines. Triggers: .py, pyproject.toml, uv, pip, pytest, Python. Covers package management, virtual environments, code style, type safety, testing, configuration, CQRS patterns, and Python-specific development tasks."
---

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

# Python Projects Workflow

Guidelines for working with Python projects across different package managers, code styles, and architectural patterns using modern tooling (uv, Python 3.9+).

## Tool Grid

| Task | Tool | Command |
|------|------|---------|
| Lint | Ruff | `uv run ruff check . --fix` |
| Format | Ruff | `uv run ruff format .` |
| Type check | Mypy | `uv run mypy src/` |
| Type check | Pyright | `uv run pyright` |
| Security | Bandit | `uv run bandit -r src/` |
| Dead code | Vulture | `uv run vulture src/` |
| Coverage | pytest-cov | `uv run pytest --cov=src` |
| Complexity | Radon | `uv run radon cc src/ -a` |

## CRITICAL: Virtual Environment Best Practices

**MUST NOT reference .venv paths manually** (e.g., `.venv/Scripts/python.exe` or `../../../.venv/`) - causes cross-platform issues and breaks on structure changes.

**MUST use `uv run python`** in uv-based projects (auto-finds venv, works cross-platform, no activation needed):

```bash
# BAD: ../../../.venv/Scripts/python.exe script.py
# GOOD: uv run python script.py

uv run python -m module.cli
```

**Prefer shared root .venv** unless isolation required (saves ~7GB per environment).

## Tooling and Package Management

### UV Package Manager (Preferred)
- **Use `uv` exclusively** for modern Python projects
- **Installation commands:**
  - Production: `uv add <package>`
  - Development: `uv add --dev <package>`
  - Optional groups: `uv add --group <group-name> <package>` (e.g., notebook, docs)
- **Execution:** `uv run python script.py` or `uv run pytest`
- **MUST NOT call python/pytest directly** - MUST use `uv run`
- MUST use `uv run python` in uv-based projects
- Run `uv sync` before executing code in new projects

### Alternative: Traditional Tools
- If not using uv, use pip with requirements files
- Maintain `requirements.txt` and `requirements-dev.txt`
- Use virtual environments (`.venv`) and activate before operations

### General Package Management
- Respect the project's chosen package manager (uv, pip, poetry, pipenv)
- Check `pyproject.toml` for project configuration
- MUST NOT mix package managers in the same project

## Python Module CLI Syntax

**Use `-m` flag** when running modules as CLIs (tells Python to run module as script, not file):

```bash
# GOOD: uv run python -m module.cli
# BAD: uv run python module.cli  # fails - treats as file path
```

## Code Style and Formatting

### PEP 8 Compliance
- Follow **PEP 8** style guide
- Line length: **88 characters** (Ruff/Black standard)
- Indentation: **4 spaces** per level
- Two blank lines before top-level function/class definitions
- One blank line between methods in a class

### Automated Formatters
- **Ruff** - Primary tool for linting AND formatting (replaces Black, isort, flake8)
  - Linting: `uv run ruff check . --fix`
  - Formatting: `uv run ruff format .`
- Configure in `pyproject.toml` under `[tool.ruff]`
- Use `ruff.toml` for standalone configuration

### Style Guidelines
- Follow project's existing style (check `pyproject.toml`, `.editorconfig`)
- Default to PEP 8 if no project style defined
- Use type hints when writing new Python code
- Prefer f-strings over `.format()` or `%` formatting

### Configuration Files
Check these files for style preferences:
- `pyproject.toml` - Modern Python project configuration
- `ruff.toml` - Ruff-specific configuration
- `.editorconfig` - Editor-agnostic style settings

### Example Formatting
```python
from typing import Any

import pandas as pd
from pydantic import BaseModel


# Example data model with proper spacing
class DataModel(BaseModel):
    field_one: str
    field_two: int


# Process input data and return DataFrame
# Args: input_data - List of dictionaries containing raw data
# Returns: Processed pandas DataFrame
def process_data(input_data: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(input_data)
```

## Type Safety and Annotations

### Type Hints
- **Strong type hints** for all parameters and return values
- Use modern generic types: `list[str]`, `dict[str, Any]` (Python 3.9+)
- For older Python: `from typing import List, Dict`
- Use `typing` module for complex types: `Union`, `Optional`, `Literal`, `Protocol`

### Data Validation
- **Use Pydantic** for data validation and serialization
- Use `dataclasses` for simple data containers when Pydantic is overkill
- Use `attrs` for enhanced dataclasses if preferred

### Example Type Usage
```python
from typing import Any, Protocol
from pydantic import BaseModel


# Protocol defining repository interface
class Repository(Protocol):
    def get(self, id: str) -> dict[str, Any] | None:
        ...


# User model with validation
class User(BaseModel):
    username: str
    email: str
    age: int | None = None


# Fetch user from repository with type safety
def fetch_user(repo: Repository, user_id: str) -> User | None:
    data = repo.get(user_id)
    return User(**data) if data else None
```

## Naming Conventions

### Standard Conventions
- **Class names:** PascalCase (`UserService`, `DatabaseConnection`)
- **Function/variable names:** snake_case (`get_user_data`, `connection_pool`)
- **Constants:** UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private methods/variables:** Leading underscore (`_internal_method`, `_cache`)

### Critical: Avoid Test Name Conflicts
- **MUST NOT name classes with "Test" prefix** unless they are actual pytest test classes
- Use descriptive names: `MockComponent`, `HelperClass`, `UtilityFunction` instead of `TestComponent`
- Pytest collects classes starting with "Test" as test classes, causing confusion

### File Naming
- Python files SHOULD be snake_case version of the primary class
- Examples:
  - `DNSRecordHandler` → `dns_record_handler.py`
  - `ComponentFactory` → `component_factory.py`
- For modules with multiple classes or functional code, name for the module's purpose

## Documentation and Comments

### Comment Style
- **MUST use single-line `#` comments** instead of multi-line `""" """` strings
- Keep comments concise and to the point
- Place comments on the line above the code they describe
- Use inline comments sparingly for brief clarifications

### Comment Philosophy
- Comment to explain **WHY**, not **WHAT**
- Prefer clear names and structure over comments
- Use comments for complex business logic, algorithms, and non-obvious decisions
- Avoid obvious, redundant, or outdated comments

### Example Documentation
```python
# Calculate compound interest using the standard formula
# Args:
#   principal: Initial amount invested
#   rate: Annual interest rate as decimal (e.g., 0.05 for 5%)
#   time: Time period in years
#   compound_frequency: Times per year interest compounds (default: 1)
# Returns: Final amount after compound interest
# Raises: ValueError if principal, rate, or time is negative
def calculate_compound_interest(
    principal: float,
    rate: float,
    time: int,
    compound_frequency: int = 1
) -> float:
    if principal < 0 or rate < 0 or time < 0:
        raise ValueError("Values must be non-negative")

    # Using compound interest formula: A = P(1 + r/n)^(nt)
    return principal * (1 + rate / compound_frequency) ** (compound_frequency * time)
```

## Error Handling

### Exception Best Practices
- Use **specific exception types** (ValueError, KeyError) over generic Exception
- Provide **meaningful error messages** that help debugging
- Use Python's `logging` module with structured logging
- Handle edge cases explicitly (empty inputs, None values, invalid types)
- **CRITICAL:** MUST NOT remove public methods for lint fixes - preserve API stability

### Example Error Handling
```python
import logging

logger = logging.getLogger(__name__)


# Process user data with proper error handling
# Args: user_id - Unique user identifier
# Returns: Processed user data dictionary
# Raises:
#   ValueError: If user_id is empty or invalid format
#   UserNotFoundError: If user doesn't exist
def process_user_data(user_id: str) -> dict[str, Any]:
    if not user_id or not user_id.strip():
        raise ValueError("user_id cannot be empty")

    try:
        user = fetch_user(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        return process(user)
    except DatabaseError as e:
        logger.error(f"Database error processing user {user_id}: {e}")
        raise
```

## Project Structure

### Package Organization
- Include `__init__.py` in all packages
- Use `__init__.py` to control package exports
- Structure DTOs and handlers logically
- Separate concerns: models, services, repositories, controllers

### Recommended Directory Structure
```
project/
├── src/
│   └── app/
│       ├── __init__.py          # Export main app components
│       ├── core/                # Core business logic
│       │   ├── __init__.py
│       │   ├── commands.py      # Command DTOs
│       │   └── queries.py       # Query DTOs
│       ├── services/            # Business services
│       │   ├── __init__.py
│       │   └── user_service.py
│       ├── repositories/        # Data access
│       │   ├── __init__.py
│       │   └── user_repository.py
│       ├── models/              # Data models
│       │   ├── __init__.py
│       │   └── user.py
│       └── handlers/            # Request handlers
│           ├── __init__.py
│           └── user_handler.py
├── tests/                       # Test files
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pyproject.toml               # Project configuration
└── README.md
```

### Import Patterns
- Use **relative imports** within packages: `from .models import User`
- Use **absolute imports** from other packages: `from app.services import UserService`
- Avoid circular imports through careful module organization

## Script Organization

### Structure Order for Standalone Scripts
Organize standalone Python scripts in the following order:

1. **Imports** - All import statements at the top
2. **Hard-coded variables and constants** - Configuration values, static data
3. **Dictionaries and data structures** - Lookup tables, mappings
4. **Class definitions** - Any classes needed for the script
5. **Functions** - Organized in the order they're called in `main()`
6. **Main execution block** - `if __name__ == "__main__":` with `main()` function

### Example Script Structure
```python
import os
from pathlib import Path
from typing import Any

# Hard-coded variables
API_ENDPOINT = "https://api.example.com"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# Data structures
STATUS_CODES = {
    200: "success",
    404: "not_found",
    500: "server_error"
}

# Classes
class DataProcessor:
    # Process data for the script
    def __init__(self, config: dict[str, Any]):
        self.config = config
    
    def process(self, data: list[dict]) -> list[dict]:
        # Transform input data
        return [self._transform(item) for item in data]
    
    def _transform(self, item: dict) -> dict:
        # Apply transformations
        return item

# Functions in execution order
def load_config() -> dict[str, Any]:
    # Load configuration from file
    config_path = Path.home() / ".config" / "app.json"
    return {}

def fetch_data(endpoint: str) -> list[dict]:
    # Fetch data from API
    return []

def save_results(data: list[dict], output_path: Path) -> None:
    # Save processed results to file
    output_path.write_text(str(data))

def main() -> None:
    # Main execution flow
    config = load_config()
    processor = DataProcessor(config)
    data = fetch_data(API_ENDPOINT)
    results = processor.process(data)
    save_results(results, Path("output.json"))

if __name__ == "__main__":
    main()
```

## Configuration Management

### Environment Variables
- Use **python-dotenv** for development: load from `.env` files
- Use `os.getenv()` with sensible defaults
- Validate configuration at startup
- MUST NOT commit `.env` files to version control

### Configuration Classes
```python
from pydantic import BaseModel, Field
import os


# Application configuration with validation
class AppConfig(BaseModel):
    debug: bool = Field(default=False)
    database_url: str = Field(...)
    max_connections: int = Field(default=10, ge=1, le=100)

    @classmethod
    # Load configuration from environment variables
    def from_env(cls) -> "AppConfig":
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            database_url=os.getenv("DATABASE_URL", ""),
            max_connections=int(os.getenv("MAX_CONNECTIONS", "10"))
        )
```

## File Management

### Working with File Paths
- Use `pathlib.Path` for cross-platform path handling
- Avoid hardcoded paths; use `os.path.expanduser('~/')` for home directories
- MUST handle file encoding explicitly (UTF-8 default)
- Properly close files or use context managers (`with` statement)

### Example File Operations
```python
from pathlib import Path

# Read file
config_path = Path.home() / '.config' / 'app.json'
if config_path.exists():
    content = config_path.read_text(encoding='utf-8')

# Write file with context manager
output_path = Path('output.txt')
with output_path.open('w', encoding='utf-8') as f:
    f.write('content')
```

## Testing and Quality

### Testing Strategy
- Write tests for critical paths and public APIs
- Use **pytest** as the primary test framework
- Organize tests: `tests/unit/`, `tests/integration/`
- Test edge cases: empty inputs, None values, large datasets
- Use fixtures for reusable test setup
- Use `pytest.mark` for test categorization
- Maintain >80% code coverage for critical paths

### Quality Tools
- **Ruff** - Linting and formatting (primary)
- **pytest** - Test framework
- **pytest-cov** - Code coverage measurement
- **mypy/pyright** - Static type checking
- **bandit** - Security scanning

### Example Test with Fixtures
```python
import pytest
from app.services import UserService


@pytest.fixture
# Provide UserService instance for tests
def user_service():
    return UserService()


@pytest.fixture
# Provide sample user data
def sample_user():
    return {"id": "user123", "name": "John Doe"}


# Test successful user retrieval
def test_get_user_success(user_service):
    user = user_service.get_user("user123")
    assert user is not None
    assert user.id == "user123"


# Test user not found raises appropriate exception
def test_get_user_not_found(user_service):
    with pytest.raises(UserNotFoundError):
        user_service.get_user("nonexistent")


# Test user creation with fixture data
def test_create_user(user_service, sample_user):
    user = user_service.create_user(sample_user)
    assert user.name == "John Doe"
```

## Special Patterns

### Flask/FastAPI Applications
- Structure with `app/` package using `__init__.py` exports
- Use blueprints/routers for route organization
- Implement health check endpoints (`/health`, `/status`)
- Use Pydantic for request/response models
- Disable debug mode in production
- Separate routes from business logic

### Command/Query Patterns (CQRS)
- Separate Commands (write operations) and Queries (read operations)
- Use command/query buses for dispatch
- Define DTOs as dataclasses or Pydantic models
- Implement handlers separately from business logic
- Example structure:
  - `core/commands.py` - Command DTOs
  - `core/queries.py` - Query DTOs
  - `handlers/command_handler.py` - Command processing
  - `handlers/query_handler.py` - Query processing

### Async/Await
- Use `async def` for I/O-bound operations
- Use `await` for async calls
- Use `asyncio` for concurrent operations
- Be aware of event loop management
- Example:
```python
import asyncio

# Fetch data asynchronously
async def fetch_data(url: str) -> dict:
    # Use aiohttp or similar for actual HTTP calls
    await asyncio.sleep(1)
    return {"status": "success"}

# Run multiple async operations concurrently
async def main():
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2")
    )
    return results
```

## Systemd Service and Timer

For Python scripts that run on a schedule (data collection, backups, ETL jobs), use systemd services with timers.

### Directory Structure

```
project/
├── systemd/
│   ├── project-name.service    # Service unit file
│   ├── project-name.timer      # Timer unit file
│   └── README.md               # Installation instructions
├── script.py
├── config.yaml
└── pyproject.toml
```

### Service File Template

Create `systemd/project-name.service`:

```ini
[Unit]
Description=Project Name daily task description
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=oneshot
User=username
Group=username
WorkingDirectory=/home/username/code/project-name
ExecStart=/home/username/.local/bin/uv run python script.py command
StandardOutput=journal
StandardError=journal

# Restart on failure with delay
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

**Key points:**
- Use `network-online.target` with `Wants=` for network-dependent scripts
- Use `uv run python` directly from `~/.local/bin/uv` (MUST NOT use `.venv/bin/python`)
- Set `WorkingDirectory` to the project directory (allows running from repo)
- Use `Type=oneshot` for scripts that run and exit
- Add service dependencies in `After=` (e.g., `postgresql.service`)
- Use `Restart=on-failure` with `RestartSec` delay for transient failures

### Timer File Template

Create `systemd/project-name.timer`:

```ini
[Unit]
Description=Run Project Name daily at 6:00 AM

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

**Key points:**
- `OnCalendar` uses systemd calendar syntax (`*-*-* HH:MM:SS` for daily)
- `Persistent=true` runs missed executions after system boot
- `RandomizedDelaySec` prevents thundering herd on shared systems

### Common Timer Schedules

```ini
# Daily at 6 AM
OnCalendar=*-*-* 06:00:00

# Every 15 minutes
OnCalendar=*:0/15

# Hourly
OnCalendar=hourly

# Weekly on Sunday at midnight
OnCalendar=Sun *-*-* 00:00:00

# First of every month
OnCalendar=*-*-01 00:00:00
```

### Installation README Template

Create `systemd/README.md`:

```markdown
# Systemd Installation

## Setup

1. Copy files to systemd directory:
   ```bash
   sudo cp systemd/project-name.service /etc/systemd/system/
   sudo cp systemd/project-name.timer /etc/systemd/system/
   ```

2. Create config:
   ```bash
   cp config.yaml.example config.yaml
   chmod 600 config.yaml
   # Edit config.yaml with your credentials
   ```

3. Enable and start timer:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable project-name.timer
   sudo systemctl start project-name.timer
   ```

## Commands

Check timer status:
```bash
systemctl list-timers project-name.timer
```

Run manually:
```bash
sudo systemctl start project-name.service
```

View logs:
```bash
journalctl -u project-name.service
```
```

### Service Naming Convention

- Use lowercase with hyphens: `mercury-retrograde`, `py-weather`, `database-backup`
- Match the project directory name when possible
- Service and timer files MUST have matching names (e.g., `foo.service` and `foo.timer`)

## Common Patterns

### Project Structure Recognition
- `pyproject.toml` - Modern Python project (PEP 518)
- `requirements.txt` - Pip dependencies
- `setup.py` - Package definition (legacy or hybrid)
- `Pipfile` - Pipenv projects
- `poetry.lock` - Poetry projects
- `uv.lock` - UV projects

### Testing Framework Detection
- Respect existing test framework (pytest, unittest, nose)
- Look for test configuration in `pyproject.toml` or `pytest.ini`
- Use project's test runner: `uv run pytest`, `poetry run pytest`, etc.

## Out of Scope

- Django specifics → see `django-workflow`
- FastAPI specifics → see `fastapi-workflow`
- Flask specifics → see `flask-workflow`
- Database migrations → see `database-workflow`

## Quick Reference

**Package managers:**
- UV: `uv run`, `uv sync`, `uv add`, `uv add --dev`
- Poetry: `poetry run`, `poetry install`, `poetry add`
- Pip: `pip install`, `python -m pip`

**Key rules:**
- MUST use `uv run python` (MUST NOT use manual .venv paths)
- MUST use `-m` flag for module CLIs
- MUST check `pyproject.toml` for config
- MUST use strong type hints for all parameters/returns
- MUST separate concerns: models, services, repositories
- SHOULD use Pydantic for validation
- SHOULD use pytest with fixtures
- MUST NOT mix package managers
- MUST NOT remove public methods for lint fixes
- MUST NOT name helper classes with "Test" prefix

**Systemd services:**
- MUST use `uv run python` in ExecStart (not `.venv/bin/python`)
- MUST use `network-online.target` with `Wants=` for network scripts
- SHOULD use `Type=oneshot` for run-and-exit scripts
- SHOULD use `Persistent=true` in timers to catch missed runs

---

**Note:** For project-specific Python patterns, check `.claude/CLAUDE.md` in the project directory.
