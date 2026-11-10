from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from database import connect_db, disconnect_db
from routers import events, telemetry, websockets


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    try:
        yield
    finally:
        await disconnect_db()


app = FastAPI(title="SquashAnalytics Pro API", version="1.0.0", lifespan=lifespan)
app.include_router(telemetry.router)
app.include_router(websockets.router)
app.include_router(events.router)


@app.get("/")
async def root():
    return {"message": "SquashAnalytics Pro Backend activo y conectado correctamente."}


@app.get("/banquillo/{partido_id}", response_class=HTMLResponse)
async def banquillo_view(partido_id: int):
    """Simple live bench display for fatigue and point-event notifications."""
    match_id = int(partido_id)
    html = '''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Banquillo — SquashAnalytics</title>
<style>
:root{color-scheme:dark}body{font-family:system-ui,sans-serif;background:#0f172a;color:#f8fafc;margin:0;padding:1rem}
header{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;border-bottom:2px solid #334155}
.badge,.card{padding:1rem;border-radius:12px}.badge{background:#eab308;color:#111827;font-weight:700}.card{background:#1e293b;border-left:6px solid #3b82f6;margin-top:1rem}.alert{border-color:#ef4444;background:#450a0a}
</style></head><body>
<header><h1>🏓 Banquillo — Partido #MATCH_ID</h1><div id="status" class="badge">Conectando…</div></header>
<main id="alerts"><section class="card">Esperando alertas…</section></main>
<script>
const badge=document.getElementById('status'),container=document.getElementById('alerts');
const scheme=location.protocol==='https:'?'wss:':'ws:';
const ws=new WebSocket(`${scheme}//${location.host}/ws/match/MATCH_ID`);
ws.onopen=()=>{badge.textContent='CONECTADO EN VIVO 🟢';badge.style.background='#16a34a';badge.style.color='white'};
ws.onclose=()=>{badge.textContent='DESCONECTADO 🔴';badge.style.background='#dc2626';badge.style.color='white'};
ws.onmessage=(event)=>{let message;try{message=JSON.parse(event.data)}catch{return}
if(message.tipo!=='ALERTA_CRITICA_FATIGA')return;const data=message.data||{};
const card=document.createElement('section');card.className='card alert';const title=document.createElement('h2');title.textContent='🚨 ALERTA BIOMECÁNICA';
const reason=document.createElement('p');reason.textContent=data.motivo_alerta||'Sin detalle';card.append(title,reason);container.prepend(card)};
</script></body></html>'''
    return HTMLResponse(content=html.replace("MATCH_ID", str(match_id)))
