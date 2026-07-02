"""Bronze ingestion CLI: `python -m footballiq.infrastructure.ingestion`."""

from __future__ import annotations

import sys

from sqlalchemy import create_engine

from footballiq.infrastructure.config import load_settings
from footballiq.infrastructure.ingestion.bronze import BronzeLoader
from footballiq.infrastructure.ingestion.manifest import SOURCES


def main() -> int:
    settings = load_settings()
    engine = create_engine(settings.database_url)
    loader = BronzeLoader(engine)
    total = 0
    for source in SOURCES:
        result = loader.load(source, settings.data_dir)
        status = "SKIP (unchanged)" if result.skipped else f"{result.rows} rows"
        print(f"  bronze.{source.bronze_table:<28} {status}")
        total += result.rows
    print(f"Ingestion complete: {total} rows across {len(SOURCES)} sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
