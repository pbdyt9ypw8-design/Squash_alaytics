import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

from database import connect_db, disconnect_db
from routers import events, nutrition, telemetry, training_plan, websockets


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
app.include_router(events.router)
app.include_router(nutrition.router)
app.include_router(training_plan.router)


@app.get("/")
async def root():
    return {"message": "SquashAnalytics Pro Backend activo y conectado correctamente."}


@app.get("/sw.js")
async def service_worker():
    sw_code = """
    const CACHE_NAME = 'squash-analytics-v1';
    const urlsToCache = [
      '/dashboard',
      '/manifest.json'
    ];

    self.addEventListener('install', event => {
      event.waitUntil(
        caches.open(CACHE_NAME)
          .then(cache => {
            console.log('Archivos cacheados correctamente');
            return cache.addAll(urlsToCache);
          })
      );
    });

    self.addEventListener('fetch', event => {
      if (event.request.method !== 'GET') {
        return;
      }

      event.respondWith(
        caches.open(CACHE_NAME).then(async cache => {
          try {
            const networkResponse = await fetch(event.request);
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          } catch (error) {
            const cachedResponse = await caches.match(event.request);
            if (cachedResponse) {
              return cachedResponse;
            }
            if (event.request.mode === 'navigate') {
              return caches.match('/dashboard');
            }
            return Response.error();
          }
        })
      );
    });

    self.addEventListener('activate', event => {
      event.waitUntil(
        caches.keys().then(cacheNames => {
          return Promise.all(
            cacheNames.map(cacheName => {
              if (cacheName !== CACHE_NAME) {
                console.log('Eliminando caché antigua:', cacheName);
                return caches.delete(cacheName);
              }
            })
          );
        })
      );
    });
    """
    return Response(content=sw_code, media_type="application/javascript")


@app.get("/manifest.json")
async def manifest():
    manifest_data = {
        "name": "SquashAnalytics Pro",
        "short_name": "SquashAnalytics",
        "start_url": "/dashboard",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#0f172a",
        "icons": [
            {
                "src": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return Response(content=json.dumps(manifest_data), media_type="application/json")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html = """
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>SquashAnalytics Pro</title>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#0f172a" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <style>
            :root {
                --bg: #0f172a;
                --panel: #111827;
                --muted: #94a3b8;
                --accent: #38bdf8;
                --text: #e2e8f0;
                --success: #22c55e;
                --warning: #f59e0b;
                --danger: #ef4444;
            }
            * { box-sizing: border-box; }
            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: linear-gradient(180deg, #020817, var(--bg));
                color: var(--text);
            }
            .container {
                max-width: 980px;
                margin: 0 auto;
                padding: 24px 16px 48px;
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 12px;
                padding-bottom: 16px;
                border-bottom: 1px solid rgba(148, 163, 184, 0.2);
            }
            .brand {
                font-size: 1.5rem;
                font-weight: 700;
            }
            .status {
                background: rgba(34, 197, 94, 0.12);
                color: var(--success);
                border: 1px solid rgba(34, 197, 94, 0.45);
                padding: 8px 12px;
                border-radius: 999px;
                font-size: 0.8rem;
            }
            .status.offline {
                background: rgba(245, 158, 11, 0.12);
                color: var(--warning);
                border-color: rgba(245, 158, 11, 0.5);
            }
            .tabs {
                display: flex;
                gap: 12px;
                margin-top: 24px;
                flex-wrap: wrap;
            }
            .tab-btn {
                background: transparent;
                border: 1px solid rgba(148, 163, 184, 0.25);
                color: var(--text);
                padding: 10px 16px;
                border-radius: 10px;
                cursor: pointer;
            }
            .tab-btn.active {
                background: rgba(56, 189, 248, 0.15);
                border-color: var(--accent);
            }
            .panel {
                display: none;
                margin-top: 18px;
                background: rgba(17, 24, 39, 0.9);
                border: 1px solid rgba(148, 163, 184, 0.12);
                border-radius: 16px;
                padding: 18px;
                box-shadow: 0 10px 35px rgba(15, 23, 42, 0.25);
            }
            .panel.active {
                display: block;
            }
            .row {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 14px;
            }
            .metric {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(148, 163, 184, 0.12);
                border-radius: 12px;
                padding: 16px;
            }
            .metric small {
                display: block;
                color: var(--muted);
                margin-bottom: 6px;
            }
            .metric strong {
                font-size: 1.5rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="brand">SquashAnalytics Pro</div>
                <div id="network-status" class="status">Conexión: online</div>
            </div>

            <div class="tabs">
                <button class="tab-btn active" onclick="switchTab(event, 'overview')">Resumen</button>
                <button class="tab-btn" onclick="switchTab(event, 'telemetry')">Telemetría</button>
                <button class="tab-btn" onclick="switchTab(event, 'alerts')">Alertas</button>
            </div>

            <section id="overview" class="panel active">
                <h2>Panel principal</h2>
                <div class="row">
                    <div class="metric">
                        <small>Zancada</small>
                        <strong>128 cm</strong>
                    </div>
                    <div class="metric">
                        <small>Asimetría</small>
                        <strong>4.2%</strong>
                    </div>
                    <div class="metric">
                        <small>FC</small>
                        <strong>146 bpm</strong>
                    </div>
                    <div class="metric">
                        <small>Riesgo</small>
                        <strong>Bajo</strong>
                    </div>
                </div>
            </section>

            <section id="telemetry" class="panel">
                <h2>Telemetría en tiempo real</h2>
                <p>Los datos se sincronizan con el backend principal y se mantienen disponibles aunque haya cortes temporales de red.</p>
                <div class="row">
                    <div class="metric">
                        <small>Velocidad</small>
                        <strong>7.8 m/s</strong>
                    </div>
                    <div class="metric">
                        <small>Rotación</small>
                        <strong>18°</strong>
                    </div>
                    <div class="metric">
                        <small>Fuerza de impacto</small>
                        <strong>9.1</strong>
                    </div>
                </div>
            </section>

            <section id="alerts" class="panel">
                <h2>Alertas</h2>
                <p id="alert-message">No se detectan incidencias críticas. El dashboard queda operativo en modo local mientras se recupera la conexión.</p>
            </section>
        </div>

        <script>
            const networkStatus = document.getElementById('network-status');
            const alertMessage = document.getElementById('alert-message');

            function updateNetworkStatus() {
                const online = navigator.onLine;
                networkStatus.textContent = online ? 'Conexión: online' : 'Conexión: offline';
                networkStatus.classList.toggle('offline', !online);

                if (!online) {
                    alertMessage.textContent = 'Se ha perdido la conectividad. El dashboard sigue funcionando en modo local con la última vista cargada.';
                } else {
                    alertMessage.textContent = 'No se detectan incidencias críticas. El dashboard queda operativo en modo local mientras se recupera la conexión.';
                }
            }

            if ('serviceWorker' in navigator) {
                window.addEventListener('load', () => {
                    navigator.serviceWorker.register('/sw.js')
                        .then(reg => {
                            console.log('Service Worker registrado con éxito en alcance:', reg.scope);
                        })
                        .catch(err => {
                            console.error('Falló el registro del Service Worker:', err);
                        });
                });
            }

            window.addEventListener('online', updateNetworkStatus);
            window.addEventListener('offline', updateNetworkStatus);
            updateNetworkStatus();

            function switchTab(evt, tabId) {
                document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById(tabId).classList.add('active');
                evt.currentTarget.classList.add('active');
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
