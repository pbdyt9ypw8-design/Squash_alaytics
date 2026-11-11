import os
from typing import Optional

import asyncpg


def _build_database_url() -> str:
    """Read the database URL from the environment and add a safe production default."""
    database_url = os.getenv("DATABASE_URL")
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if database_url:
        if environment == "production" and "sslmode=require" not in database_url and "localhost" not in database_url and "127.0.0.1" not in database_url:
            separator = "&" if "?" in database_url else "?"
            return f"{database_url}{separator}sslmode=require"
        return database_url

    if environment == "production":
        raise RuntimeError(
            "DATABASE_URL no está configurada para producción. Define la variable de entorno antes de arrancar la API."
        )

    return "postgresql://postgres:postgrespassword@localhost:5432/squash_db"


DATABASE_URL = _build_database_url()


class Database:
    pool: Optional[asyncpg.Pool] = None


db = Database()


async def connect_db():
    """Create a reusable asyncpg connection pool for FastAPI."""
    if db.pool is not None:
        return

    ssl_mode = "require" if "sslmode=require" in DATABASE_URL or "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL else None
    db.pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=2,
        max_size=10,
        ssl=ssl_mode,
    )


async def disconnect_db():
    """Gracefully close the database pool on shutdown."""
    if db.pool:
        await db.pool.close()
        db.pool = None
