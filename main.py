from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from database import connect_db, disconnect_db
from routers import telemetry, websockets


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    try:
        yield
    finally:
        await disconnect_db()


app = FastAPI(
    title="SquashAnalytics Pro API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(telemetry.router)
app.include_router(websockets.router)


@app.get("/")
async def root():
    return {"message": "SquashAnalytics Pro Backend activo y conectado correctamente."}


@app.get("/banquillo/{partido_id}", response_class=HTMLResponse)
async def banquillo_view(partido_id: int):
    """Simple live bench display for WebSocket alerts for one match."""
    html = r'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Banquillo — SquashAnalytics Pro</title>
  <style>
    :root { color-scheme: dark; }
    body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 1.25rem; }
    header { display:flex; flex-wrap:wrap; gap:1rem; justify-content:space-between; align-items:center; border-bottom:2px solid #334155; padding-bottom:1rem; }
    h1 { font-size:clamp(1.2rem, 3vw, 1.8rem); }
    .badge { padding:.5rem .85rem; border-radius:999px; background:#eab308; color:#111827; font-weight:700; }
    .card { background:#1e293b; border-left:6px solid #3b82f6; border-radius:12px; padding:1rem; margin-top:1rem; overflow-wrap:anywhere; }
    .alert { border-color:#ef4444; background:#450a0a; }
    p { color:#cbd5e1; }
    .note { font-size:.85rem; color:#94a3b8; }
  </style>
</head>
<body>
  <header>
    <h1>🏓 SquashAnalytics — Banquillo (Partido #__MATCH_ID__)</h1>
    <div id="status" class="badge" role="status" aria-live="polite">Conectando…</div>
  </header>
  <main id="alerts">
    <section class="card"><h2>Estado del sistema</h2><p>Esperando alertas del análisis de telemetría…</p></section>
  </main>
  <p class="note">Panel experimental. No sustituye una valoración profesional ni un protocolo de seguridad.</p>
  <script>
    (() => {
      const status = document.getElementById('status');
      const alerts = document.getElementById('alerts');
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      const socket = new WebSocket(`${protocol}//${location.host}/ws/match/__MATCH_ID__`);
      socket.addEventListener('open', () => {
        status.textContent = 'CONECTADO EN VIVO 🟢';
        status.style.backgroundColor = '#16a34a';
        status.style.color = '#fff';
      });
      socket.addEventListener('close', () => {
        status.textContent = 'DESCONECTADO 🔴';
        status.style.backgroundColor = '#dc2626';
        status.style.color = '#fff';
      });
      socket.addEventListener('error', () => {
        status.textContent = 'ERROR DE CONEXIÓN';
        status.style.backgroundColor = '#dc2626';
        status.style.color = '#fff';
      });
      socket.addEventListener('message', (event) => {
        let message;
        try { message = JSON.parse(event.data); } catch { return; }
        if (message.tipo !== 'ALERTA_CRITICA_FATIGA') return;

        const data = message.data || {};
        const card = document.createElement('section');
        card.className = 'card alert';
        const title = document.createElement('h2');
        title.textContent = '🚨 ALERTA DE CAMBIO BIOMECÁNICO';
        const reason = document.createElement('p');
        reason.textContent = `Motivo: ${data.motivo_alerta ?? 'Sin detalle'}`;
        const readings = document.createElement('p');
        readings.textContent = `Jugador ${data.jugador_id ?? '—'} · Zancada: ${data.zancada_promedio ?? '—'} cm · Asimetría: ${data.asimetria_promedio ?? '—'}% · Flexión lumbar: ${data.flexion_lumbar_promedio ?? '—'}° · FC: ${data.frecuencia_cardiaca ?? '—'} · Zona FC: ${data.zona_fc ?? '—'}`;
        const time = document.createElement('p');
        time.className = 'note';
        time.textContent = `Hora: ${data.tiempo_evaluacion ? new Date(data.tiempo_evaluacion).toLocaleTimeString() : '—'}`;
        card.append(title, reason, readings, time);
        alerts.prepend(card);
      });
    })();
  </script>
</body>
</html>'''
    return HTMLResponse(content=html.replace("__MATCH_ID__", str(partido_id)))
