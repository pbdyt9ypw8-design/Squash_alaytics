import os
import asyncpg

# Dirección donde vive nuestra base de datos en Docker (la que encendimos en la terminal)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:tu_contraseña@localhost:5432/squash_db")

class Database:
    pool: asyncpg.Pool = None

db = Database()

async def connect_db():
    # Crea un "pool" o grupo de conexiones simultáneas para que la app sea muy rápida
    db.pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)

async def disconnect_db():
    # Cierra las conexiones de forma segura al apagar la app
    if db.pool:
        await db.pool.close()
