from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import connect_db, disconnect_db
from routers import (
    clinical_profile,
    events,
    nutrition,
    rm_calculator,
    tablet_ui,
    tactics_points,
    telemetry,
    training_plan,
    websockets,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    try:
        yield
    finally:
        await disconnect_db()


app = FastAPI(title="SquashAnalytics Pro API", version="1.0.0", lifespan=lifespan)

app.include_router(clinical_profile.router)
app.include_router(tablet_ui.router)
app.include_router(rm_calculator.router)
app.include_router(tactics_points.router)
app.include_router(telemetry.router)
app.include_router(websockets.router)
app.include_router(events.router)
app.include_router(nutrition.router)
app.include_router(training_plan.router)


@app.get("/")
async def root():
    return {"message": "SquashAnalytics Pro Backend activo y conectado correctamente."}
