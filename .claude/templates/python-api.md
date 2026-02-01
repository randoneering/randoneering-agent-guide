# Python API Project

## Project Context

**Project Name:** [API Name]

**Description:** [What this API does]

**Tech Stack:**
- Python 3.11+
- FastAPI (or Flask)
- PostgreSQL
- SQLAlchemy / asyncpg
- Pydantic for validation

---

## Project Structure

```
src/
├── api/
│   ├── routes/          # Route handlers
│   ├── dependencies/    # Dependency injection
│   └── middleware/      # Request middleware
├── core/
│   ├── config.py        # Settings via pydantic-settings
│   └── security.py      # Auth helpers
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas (request/response)
├── services/            # Business logic
└── repositories/        # Database access layer
tests/
├── conftest.py          # Fixtures
├── unit/
└── integration/
```

---

## Development Guidelines

### Package Management

- Use `uv` for all dependency management
- Virtual environment: `uv venv && source .venv/bin/activate`
- Install deps: `uv sync`
- Add dependency: `uv add <package>`
- Dev dependency: `uv add --dev <package>`

### Code Style

- Type hints required on all functions
- Run `ruff check --fix` before commits
- Run `ruff format` for formatting
- Validate types: `pyright` or `mypy --strict`

### API Patterns

**Request/Response:**
```python
# Separate schemas for create, update, response
class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserUpdate(BaseModel):
    name: str | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    model_config = ConfigDict(from_attributes=True)
```

**Dependency Injection:**
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    ...
```

**Error Handling:**
```python
# Use HTTPException for client errors
raise HTTPException(status_code=404, detail="User not found")

# Custom exceptions for domain errors
class DomainError(Exception):
    pass

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

---

## Database Operations

### Migrations (Alembic)

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one
alembic downgrade -1
```

### Query Patterns

```python
# Use select() for queries
stmt = select(User).where(User.email == email)
result = await session.execute(stmt)
user = result.scalar_one_or_none()

# Eager loading
stmt = select(User).options(selectinload(User.orders))
```

---

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Specific test
pytest tests/unit/test_users.py -v
```

### Test Database

```python
# conftest.py
@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Testing Endpoints

```python
@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_create_user(client):
    response = client.post("/users", json={"email": "test@example.com", "name": "Test"})
    assert response.status_code == 201
```

---

## Configuration

### Environment Variables

```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

### Required .env

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
SECRET_KEY=your-secret-key
```

---

## Common Tasks

### Add New Endpoint

1. Create schema in `schemas/`
2. Add service method in `services/`
3. Create route in `api/routes/`
4. Add tests in `tests/`
5. Update OpenAPI tags if needed

### Add New Model

1. Create model in `models/`
2. Generate migration: `alembic revision --autogenerate -m "add table_name"`
3. Review migration file
4. Apply: `alembic upgrade head`
5. Add repository methods
6. Add tests

---

## Do Not

- Store secrets in code or commit `.env` files
- Use `*` imports
- Skip type hints
- Write raw SQL without parameterization
- Catch generic `Exception` without re-raising
- Mix business logic into route handlers

---

## Verification Before Completion

Before claiming work is done:

```bash
ruff check --fix .
ruff format .
pyright  # or mypy --strict
pytest --cov=src
```

All must pass with no errors.
