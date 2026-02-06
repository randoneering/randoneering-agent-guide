---
name: api-script
description: Use when creating Python scripts that fetch data from REST APIs, when adding new API integrations, or when the user asks for help grabbing data from weather, IoT, or external services
---

# API Script Generator

## Overview

Create single-file Python scripts that fetch data from REST APIs and store results in PostgreSQL. Scripts follow project patterns: requests for HTTP, dual logging, argparse CLI with subcommands, upsert storage, and Gotify/Slack alerts.

## When to Use

- Creating a new script to pull data from an API
- Adding a weather, IoT sensor, or general REST data source
- User mentions "API", "fetch", "grab data from", "pull from"

## Script Structure

Single `.py` file, 300-600 lines, following this order:

```python
#!/usr/bin/env python3
# script_name: Brief description of data source.
#
# Usage:
#     uv run python py_source.py daily              # Yesterday's data (for cron)
#     uv run python py_source.py range 20240101 20240131  # Specific date range
#     uv run python py_source.py last 7             # Last N days

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import psycopg2
import requests
from psycopg2 import OperationalError

from config import load_config

if TYPE_CHECKING:
    from psycopg2.extensions import cursor as Cursor
```

## Reference: py_weather.py

Use `py_weather.py` as the canonical example:

| Component | Lines | Description |
|-----------|-------|-------------|
| Logging setup | 33-57 | Dual console + file handler |
| Secret decryption | 65-89 | Fernet-based password decryption |
| Date range helpers | 94-121 | `daily`, `range`, `last` date calculations |
| API fetch | 131-161 | HTTP GET with timeout, error checking |
| Upsert station | 215-246 | `ON CONFLICT DO UPDATE` pattern |
| Upsert observations | 255-340 | Bulk insert with conflict handling |
| DB ingest | 350-401 | Connection, transaction, commit flow |
| CLI/main | 512-628 | argparse with subparsers |

## Authentication Patterns

Support multiple auth types via `config.yaml`:

```yaml
api_name:
  base_url: "https://api.example.com"
  auth_type: "header"  # "header", "query", or "bearer"
  api_key_file: "/path/to/encrypted/key"
  # Or for query param auth:
  # auth_type: "query"
  # auth_param: "api_key"
```

Build auth in fetch function:

```python
def build_auth(config: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    # Returns (headers, params) based on auth_type
    auth_type = config["api"].get("auth_type", "query")
    api_key = decrypt_api_key(config)

    if auth_type == "header":
        return {"X-API-Key": api_key}, {}
    elif auth_type == "bearer":
        return {"Authorization": f"Bearer {api_key}"}, {}
    else:  # query
        param_name = config["api"].get("auth_param", "token")
        return {}, {param_name: api_key}
```

## Upsert Pattern

Idempotent inserts - safe to re-run:

```python
cur.execute("""
    INSERT INTO readings (station_id, timestamp, value)
    VALUES (%s, %s, %s)
    ON CONFLICT (station_id, timestamp) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = CURRENT_TIMESTAMP
""", (station_id, timestamp, value))
```

Requires unique constraint on conflict columns in `schema.sql`.

## Anomaly Detection

Check expected vs actual record counts:

```python
def check_data_anomalies(
    records: list[dict[str, Any]],
    expected_count: int,
    logger: logging.Logger,
    config: dict[str, Any],
) -> None:
    actual = len(records)
    threshold = 0.9  # Alert if less than 90% of expected

    if actual < expected_count * threshold:
        message = f"Data anomaly: received {actual}/{expected_count} records"
        logger.warning(message)
        send_alert(config, "Data Anomaly", message, priority=7)
```

## Alerting: Gotify + Slack

Unified alert function (reference: `ubuntu_package_updater.py:171-215`):

```python
def send_alert(
    config: dict[str, Any],
    title: str,
    message: str,
    priority: int = 5,
) -> None:
    # Send to Gotify
    gotify = config.get("gotify", {})
    if gotify.get("enabled", False):
        url = gotify.get("url", "").rstrip("/")
        token = gotify.get("token", "")
        if url and token:
            try:
                requests.post(
                    f"{url}/message",
                    params={"token": token},
                    json={"title": title, "message": message, "priority": priority},
                    timeout=10,
                )
            except Exception as e:
                logging.error(f"Gotify alert failed: {e}")

    # Send to Slack
    slack = config.get("slack", {})
    if slack.get("enabled", False):
        webhook_url = slack.get("webhook_url", "")
        if webhook_url:
            try:
                requests.post(
                    webhook_url,
                    json={"text": f"*{title}*\n{message}"},
                    timeout=10,
                )
            except Exception as e:
                logging.error(f"Slack alert failed: {e}")
```

Config for alerting:

```yaml
gotify:
  enabled: true
  url: https://gotify.example.com
  token: "your-app-token"
  priority: 5

slack:
  enabled: true
  webhook_url: https://hooks.slack.com/services/xxx/yyy/zzz
```

## CLI Subcommands

Standard pattern for data collection scripts:

```python
def main() -> None:
    parser = argparse.ArgumentParser(
        description="py_source: Collect data from Source API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s daily                        # Yesterday's data
    %(prog)s range 20240101 20240131      # Date range
    %(prog)s last 7                       # Last 7 days
        """,
    )

    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")
    subparsers.add_parser("daily", help="Fetch yesterday's data")

    range_parser = subparsers.add_parser("range", help="Fetch date range")
    range_parser.add_argument("start_date", help="Start date (YYYYMMDD)")
    range_parser.add_argument("end_date", help="End date (YYYYMMDD)")

    last_parser = subparsers.add_parser("last", help="Fetch last N days")
    last_parser.add_argument("days", type=int, help="Number of days")

    args = parser.parse_args()
```

## Systemd Integration

Create `systemd/` directory with:

**`systemd/py-source.service`:**
```ini
[Unit]
Description=py_source daily data collection
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=oneshot
User=username
WorkingDirectory=/home/username/code/project
ExecStart=/home/username/.local/bin/uv run python py_source.py daily
StandardOutput=journal
StandardError=journal
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

**`systemd/py-source.timer`:**
```ini
[Unit]
Description=Run py_source daily at 6:00 AM

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

## Schema Template

Create `schema.sql` with:

```sql
CREATE TABLE IF NOT EXISTS source_data (
    id BIGSERIAL PRIMARY KEY,
    source_id VARCHAR(50) NOT NULL,
    observation_time TIMESTAMPTZ NOT NULL,
    -- data columns here
    value NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, observation_time)
);

CREATE INDEX IF NOT EXISTS idx_source_data_time
    ON source_data(observation_time);
CREATE INDEX IF NOT EXISTS idx_source_data_source
    ON source_data(source_id);
```

## Implementation Checklist

1. Ask user for: API name, endpoint, auth method, data fields
2. Create `py_source.py` following structure above
3. Add API config to `config.yaml`
4. Create `schema.sql` with table definition
5. Add `systemd/` service and timer files
6. Update `pyproject.toml` if new dependencies needed
7. Test with `uv run python py_source.py daily`

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Hardcoded credentials | Use config.yaml + Fernet encryption |
| No HTTP timeout | Always set `timeout=30` or higher |
| Silent failures | Log errors, send alerts, exit non-zero |
| Missing upsert constraint | Add UNIQUE constraint for ON CONFLICT |
| No anomaly detection | Check record counts, alert on gaps |
