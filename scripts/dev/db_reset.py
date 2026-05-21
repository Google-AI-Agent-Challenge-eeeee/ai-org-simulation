"""Drop & recreate the local DB, then re-apply Alembic migrations.

DESTRUCTIVE. Intended only for local development when the schema gets out
of sync (e.g. you switched branches with different migrations applied).

Strategy:
    1. Connect to the maintenance DB (``postgres``) on the same host.
    2. Terminate other sessions to the target DB.
    3. ``DROP DATABASE`` + ``CREATE DATABASE``.
    4. Run ``alembic upgrade head`` to recreate the schema cleanly.
"""

from __future__ import annotations

import subprocess
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

from backend.core.config.settings import get_settings


def main() -> int:
    settings = get_settings()
    url = make_url(settings.database_url)
    target_db = url.database
    if not target_db:
        print("DATABASE_URL has no database name; aborting.", file=sys.stderr)
        return 1

    # Connect to the cluster's maintenance DB ("postgres") so we can drop the target.
    admin_url = url.set(database="postgres")
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    print(f"Resetting database '{target_db}' on {url.host}:{url.port}...")
    with engine.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = :db AND pid <> pg_backend_pid()"
            ),
            {"db": target_db},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{target_db}"'))
        conn.execute(text(f'CREATE DATABASE "{target_db}"'))
    engine.dispose()

    print("Database recreated; running 'alembic upgrade head'...")
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
