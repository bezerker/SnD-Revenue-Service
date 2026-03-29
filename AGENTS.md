# AGENTS.md

Guidance for agentic coding agents working in this repository.

## Project Overview

Python 3.13 Discord bot ("Stand and Deliver Revenue Service") that audits member
join/leave events and optionally assesses join risk via an LLM. Deployed to
Kubernetes. Uses `uv` for dependency management and `hatchling` for builds.

## Build & Run Commands

```bash
# Install all dependencies (production + dev)
uv sync --frozen --all-groups

# Run the bot locally
uv run python -m snd_revenue_service

# Build source distribution
uv build --sdist

# Build Docker image
docker build -t snd-revenue-service:local .
```

## Test Commands

```bash
# Run all tests
uv run pytest -v

# Run a single test file
uv run pytest tests/test_config.py -v

# Run a single test by name
uv run pytest tests/test_config.py::test_load_settings_reads_toml_and_env -v

# Run tests matching a keyword
uv run pytest -k "test_load_settings" -v

# Run with verbose output and no capture
uv run pytest -v -s tests/test_events.py
```

Framework: `pytest` + `pytest-asyncio`. Async tests use `@pytest.mark.asyncio`.

## Lint & Format Commands

```bash
# Lint (ruff, default rules, no custom config in pyproject.toml)
ruff check src/ tests/

# Format check
ruff format --check src/ tests/

# Auto-fix lint issues
ruff check --fix src/ tests/

# Auto-format
ruff format src/ tests/
```

Ruff runs with default configuration: line length 88, double quotes, 4-space
indent. There is no `[tool.ruff]` section in `pyproject.toml`. CI does NOT run
ruff; it only runs tests and Docker build.

## Code Style

### Imports

- PEP 8 grouping: **stdlib** → blank line → **third-party** → blank line →
  **local (`snd_revenue_service.*`)**
- No wildcard imports
- `from __future__ import annotations` only when needed (not universal)
- Each test file uses a `sys.path` hack at the top:
  ```python
  SRC_DIR = Path(__file__).resolve().parents[1] / "src"
  sys.path.insert(0, str(SRC_DIR))
  ```

### Naming Conventions

- **Modules:** `snake_case` (`join_risk.py`, `logging_config.py`)
- **Classes:** `PascalCase` (`JoinRiskService`, `AuditPublisher`, `ConfigError`)
- **Functions:** `snake_case` (`load_settings`, `build_join_event`)
- **Private helpers:** `_leading_underscore` (`_parse_intlike_value`)
- **Constants:** `UPPER_SNAKE_CASE` (`AUDIT_MATCH_WINDOW`, `RISK_DISCLAIMER`)
- **Private module-level data:** `_SYSTEM_PROMPT`, `_CATEGORY_LABELS`

### Type Annotations

- **Full annotations on every function** (parameters and return types)
- Use `X | None` syntax, never `Optional[X]`
- `frozen=True` dataclasses for all data objects:
  ```python
  @dataclass(frozen=True)
  class Settings:
      guild_id: int
      audit_channel_id: int
      discord_token: str
  ```
- `Any` is acceptable for duck-typed Discord objects in function signatures

### Error Handling

- **Custom exception hierarchy:**
  - `ConfigError(ValueError)` — configuration issues
  - `PublishError(RuntimeError)` — audit publish failures
  - `JoinRiskParseError(ValueError)` — LLM response parsing errors
- **Always use `raise ... from exc`** to preserve exception context:
  ```python
  raise ConfigError(f"Invalid TOML in config file: {config_path}") from exc
  ```
- **Fail-fast at startup** (invalid config → `SystemExit`)
- **Resilient at runtime** (publish/event errors are caught and logged, never
  crash the process)
- **Use `logger.exception(...)`** for error logging in runtime handlers

### Code Organization

- **Functional style preferred.** Most logic lives in plain functions. Only
  `AuditPublisher`, `JoinRiskService`, and the Discord `Client` are classes.
- **Dependency injection via function parameters.** `create_client()` accepts
  render/build/snapshot callbacks — this makes testing straightforward.
- **Defensive `getattr`** for accessing Discord object attributes, enabling
  duck-typed test stubs:
  ```python
  display_name = getattr(member, "display_name", None)
  ```
- **Constants at module top level.** Use tuples (not lists) for immutable
  sequences like retry delays.

### Async Patterns

- `asyncio.create_task()` for fire-and-forget background work
- `async with asyncio.timeout()` for LLM API timeouts
- `async for` for iterating Discord audit logs

### Comments & Docstrings

- **Do NOT add comments** unless the user explicitly asks for them
- Docstrings are rare in the codebase; function names and types are expected to
  be self-documenting
- The one docstring style seen is single-line imperative:
  ```python
  """When set, SND_LLM_ENABLED / OPENAI_* / SND_LLM_TIMEOUT_SECONDS override TOML."""
  ```

## Testing Conventions

- **1:1 test-to-source mapping:** `tests/test_foo.py` tests `src/snd_revenue_service/foo.py`
- **No `conftest.py`** — each test file is self-contained
- **Test stubs:** Use `types.SimpleNamespace` for lightweight Discord object
  stubs instead of mocking full Discord models
- **Async mocks:** `unittest.mock.AsyncMock(return_value=...)` and
  `AsyncMock(side_effect=...)`
- **Environment isolation:** `pytest.MonkeyPatch` (`monkeypatch.setenv`,
  `monkeypatch.delenv`) — always clean up env vars; pass `raising=False` to
  `delenv`
- **Temp files:** `tmp_path` fixture for temporary config files
- **Log assertions:** `caplog` fixture with `caplog.at_level("WARNING")`
- **Error assertions:** `pytest.raises(ExpectedError, match="substring")`
- **Test names are long and descriptive:**
  `test_on_raw_member_remove_marks_recent_audit_kick`

## Project Structure

```
src/snd_revenue_service/     # Production code
    __init__.py              # Empty
    __main__.py              # Entry point (load config, create client, run)
    bot.py                   # Discord client & event handlers
    config.py                # TOML config + env var loading → Settings dataclass
    embeds.py                # Discord embed rendering
    events.py                # Audit event dataclasses & builders
    join_profile.py          # Member profile snapshot for LLM
    join_risk.py             # LLM risk assessment service
    logging_config.py        # Basic logging setup
    publisher.py             # Discord channel publish logic
tests/                       # Test files (1:1 mapping to source modules)
k8s/                         # Kubernetes deployment manifests
```

## Key Dependencies

- **Runtime:** `discord.py>=2.7`, `openai>=1.59`
- **Dev:** `pytest>=8.3`, `pytest-asyncio>=0.26`
- **Python:** `>=3.13` (uses `X | None` syntax, `tomllib` stdlib)
- **Build:** `hatchling` backend, `uv` package manager
