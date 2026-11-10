from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import connect_db, disconnect_db
from routers import telemetry, websockets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conecta a la base de datos al encender el servidor
    await connect_db()
    yield
    # Desconecta de forma segura al apagar
    await disconnect_db()

app = FastAPI(
    title="SquashAnalytics Pro API",
    version="1.0.0",
    lifespan=lifespan
)

# Registramos las rutas
app.include_router(telemetry.router)
app.include_router(websockets.router)

@app.get("/")
async def root():
    return {"message": "SquashAnalytics Pro Backend activo y conectado correctamente."}
