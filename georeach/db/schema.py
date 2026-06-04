"""PostGIS database schema initialization."""

from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, text

from georeach.config import Config


def init_database(config: Config) -> None:
    """Initialize PostGIS database with extensions and schema."""
    logger.info("Initializing PostGIS database")

    engine = create_engine(config.database.url)

    sql_dir = Path(__file__).parent.parent.parent / "sql"

    sql_files = [
        sql_dir / "01_extensions.sql",
        sql_dir / "02_schema.sql",
    ]

    with engine.connect() as conn:
        for sql_file in sql_files:
            if not sql_file.exists():
                logger.warning(f"SQL file not found: {sql_file}")
                continue

            logger.info(f"Executing {sql_file.name}")
            with open(sql_file) as f:
                sql = f.read()

            for statement in sql.split(";"):
                statement = statement.strip()
                # Skip empty statements and comment-only statements
                if statement and not all(
                    line.strip().startswith("--") or not line.strip()
                    for line in statement.split("\n")
                ):
                    conn.execute(text(statement))
            conn.commit()

    logger.success("Database initialized")
