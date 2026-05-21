"""Block until the local Postgres accepts connections.

Used by ``just bootstrap`` so Alembic isn't run against a still-starting
container. Reads the same URL that the app uses, so changing ``.env`` is
the only place to keep in sync.
"""

from __future__ import annotations

import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from backend.core.config.settings import get_settings

TIMEOUT_SECONDS = 60
POLL_INTERVAL_SECONDS = 1.0


def main() -> int:
    url = get_settings().database_url
    engine = create_engine(url, pool_pre_ping=False)

    deadline = time.monotonic() + TIMEOUT_SECONDS
    attempt = 0
    while True:
        attempt += 1
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Postgres ready after {attempt} attempt(s).")
            return 0
        except OperationalError as exc:
            if time.monotonic() > deadline:
                print(
                    f"Postgres still not reachable after {TIMEOUT_SECONDS}s: {exc}",
                    file=sys.stderr,
                )
                return 1
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
