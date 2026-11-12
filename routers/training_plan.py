import asyncpg
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from database import db

router = APIRouter(prefix="/training-plan", tags=["Resumen post-partido"])


@router.get("/{partido_id}/{jugador_id}")
async def generar_resumen_post_partido(partido_id: int, jugador_id: int):
    """Combine match events and telemetry into descriptive stats and cautious training ideas."""
    if partido_id < 1 or jugador_id < 1:
        raise HTTPException(status_code=422, detail="Los identificadores deben ser positivos.")
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    try:
        async with db.pool.acquire() as connection:
            event_summary = await connection.fetchrow(
                """
                SELECT COUNT(*) AS total_eventos,
                       COUNT(*) FILTER (WHERE tipo_resultado = 'ganador') AS ganadores,
                       COUNT(*) FILTER (WHERE tipo_resultado = 'error_no_forzado') AS errores_no_forzados,
                       COUNT(*) FILTER (WHERE tipo_resultado = 'stroke') AS strokes,
                       COUNT(*) FILTER (WHERE tipo_resultado = 'let') AS lets,
                       COUNT(*) FILTER (WHERE tipo_tactica = 'ataque') AS ataques,
                       COUNT(*) FILTER (WHERE tipo_tactica = 'defensa') AS defensas,
                       COUNT(*) FILTER (WHERE llegada_t = TRUE) AS llegadas_t
                FROM eventos_puntos
                WHERE partido_id = $1 AND jugador_id = $2
                """,
                partido_id,
                jugador_id,
            )
            shots = await connection.fetch(
                """
                SELECT tipo_golpe,
                       COUNT(*) AS intentos,
                       COUNT(*) FILTER (WHERE tipo_resultado = 'ganador') AS ganadores,
                       COUNT(*) FILTER (WHERE tipo_resultado = 'error_no_forzado') AS errores
                FROM eventos_puntos
                WHERE partido_id = $1 AND jugador_id = $2 AND tipo_golpe IS NOT NULL
                GROUP BY tipo_golpe
                ORDER BY intentos DESC, tipo_golpe
                """,
                partido_id,
                jugador_id,
            )
            tactics = await connection.fetch(
                """
                SELECT tipo_tactica,
                       COUNT(*) AS eventos,
                       COUNT(*) FILTER (WHERE tipo_resultado = 'ganador') AS ganadores,
                       COUNT(*) FILTER (WHERE tipo_resultado = 'error_no_forzado') AS errores
                FROM eventos_puntos
                WHERE partido_id = $1 AND jugador_id = $2 AND tipo_tactica IS NOT NULL
                GROUP BY tipo_tactica
                """,
                partido_id,
                jugador_id,
            )
            telemetry = await connection.fetchrow(
                """
                SELECT COUNT(*) AS muestras,
                       AVG(angulo_valgo_rodilla_deg) AS valgo_rodilla_promedio,
                       AVG(flexion_lumbar_deg) AS flexion_lumbar_promedio,
                       AVG(simetria_zancada_abi) AS asimetria_zancada_promedio,
                       MIN(time) AS inicio,
                       MAX(time) AS fin
                FROM telemetria_frames
                WHERE partido_id = $1 AND jugador_id = $2
                """,
                partido_id,
                jugador_id,
            )
    except asyncpg.UndefinedColumnError as exc:
        raise HTTPException(
            status_code=503,
            detail="Falta aplicar las migraciones de eventos tácticos o telemetría.",
        ) from exc
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(status_code=503, detail="Falta una tabla requerida para el resumen.") from exc
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=503, detail=f"Error consultando datos: {exc.__class__.__name__}.") from exc

    event_count = int(event_summary["total_eventos"] or 0)
    telemetry_count = int(telemetry["muestras"] or 0)
    if event_count == 0 and telemetry_count == 0:
        raise HTTPException(status_code=404, detail="No hay eventos ni telemetría para ese partido y jugador.")

    def as_int(value):
        return int(value or 0)

    def rounded(value):
        return round(float(value), 2) if value is not None else None

    shot_stats = []
    recommendations = []
    for row in shots:
        attempts = as_int(row["intentos"])
        wins = as_int(row["ganadores"])
        errors = as_int(row["errores"])
        shot_stats.append({
            "tipo_golpe": row["tipo_golpe"],
            "intentos": attempts,
            "ganadores": wins,
            "errores_no_forzados": errors,
            "porcentaje_ganador": round(100 * wins / attempts, 1) if attempts else 0,
            "porcentaje_error": round(100 * errors / attempts, 1) if attempts else 0,
        })
        if attempts >= 3 and errors > wins:
            recommendations.append(
                f"En {row['tipo_golpe']} se registraron más errores no forzados que ganadores ({errors}/{attempts} errores, {wins}/{attempts} ganadores). Revisar selección del golpe, preparación y ejecución con el entrenador; practicar primero con control y progresar según técnica."
            )

    tactic_stats = []
    for row in tactics:
        count = as_int(row["eventos"])
        wins = as_int(row["ganadores"])
        errors = as_int(row["errores"])
        tactic_stats.append({
            "tipo_tactica": row["tipo_tactica"],
            "eventos": count,
            "ganadores": wins,
            "errores_no_forzados": errors,
            "porcentaje_ganador": round(100 * wins / count, 1) if count else 0,
        })
        if count >= 5 and errors > wins:
            recommendations.append(
                f"En situaciones registradas como {row['tipo_tactica']} hubo más errores no forzados que ganadores. Trabajar lectura de la situación y elección entre mantener, presionar o recuperar la posición, revisando vídeo con el entrenador."
            )

    t_returns = as_int(event_summary["llegadas_t"])
    if event_count >= 5:
        t_rate = round(100 * t_returns / event_count, 1)
        recommendations.append(
            f"Se anotaron {t_returns} llegadas a la T en {event_count} eventos ({t_rate}% de los eventos registrados tenían la marca). Revisar cobertura y recuperación al centro en vídeo; esta proporción depende de cómo se registró cada jugada y no es una norma de rendimiento."
        )

    if not recommendations and event_count:
        recommendations.append(
            "No aparece una señal de mejora táctica suficientemente clara en los eventos registrados. Mantener el plan habitual y revisar el vídeo y el contexto del partido antes de cambiar el entrenamiento."
        )
    if not event_count:
        recommendations.append(
            "No hay eventos tácticos registrados. Completar el registro de golpes, resultados e итinerarios de vuelta a la T para obtener recomendaciones basadas en el partido."
        )
    if telemetry_count:
        recommendations.append(
            "Las métricas biomecánicas se muestran como promedios experimentales de telemetría; verificar la calidad del dato y la técnica en vídeo. No usarlas por sí solas para diagnosticar ni prescribir ejercicios correctivos."
        )

    return {
        "status": "resumen_post_partido_descriptivo",
        "partido_id": partido_id,
        "jugador_id": jugador_id,
        "estadisticas_partido": {
            "eventos_registrados": event_count,
            "ganadores": as_int(event_summary["ganadores"]),
            "errores_no_forzados": as_int(event_summary["errores_no_forzados"]),
            "strokes": as_int(event_summary["strokes"]),
            "lets": as_int(event_summary["lets"]),
            "ataques": as_int(event_summary["ataques"]),
            "defensas": as_int(event_summary["defensas"]),
            "llegadas_a_la_t": t_returns,
        },
        "estadisticas_por_golpe": shot_stats,
        "estadisticas_por_intencion": tactic_stats,
        "telemetria": {
            "muestras": telemetry_count,
            "periodo_inicio": telemetry["inicio"].isoformat() if telemetry["inicio"] else None,
            "periodo_fin": telemetry["fin"].isoformat() if telemetry["fin"] else None,
            "promedios_experimentales": {
                "valgo_rodilla_deg": rounded(telemetry["valgo_rodilla_promedio"]),
                "flexion_lumbar_proxy_deg": rounded(telemetry["flexion_lumbar_promedio"]),
                "asimetria_zancada_pct": rounded(telemetry["asimetria_zancada_promedio"]),
            },
        },
        "sugerencias_estrategicas_entrenamiento": recommendations,
        "nota": "Análisis descriptivo y orientativo basado en los datos registrados; no es diagnóstico ni prescripción. La ausencia de una marca puede reflejar falta de registro, no necesariamente ausencia de la acción.",
    }


@router.get("/tablet", response_class=HTMLResponse, include_in_schema=False)
async def pagina_resumen_post_partido():
    """Simple post-match dashboard that loads the combined report endpoint."""
    return HTMLResponse(content=r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Plan post-partido | SquashAnalytics Pro</title>
<style>
:root{color-scheme:dark;--bg:#101820;--panel:#192630;--line:#314653;--text:#edf5f7;--muted:#a9bdc6;--accent:#7be0ad;--warn:#ffd37a}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,sans-serif}main{max-width:1000px;margin:auto;padding:24px clamp(14px,4vw,36px)}section{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin:16px 0}h1{margin-top:0}label{display:block;margin:10px 0 5px}input{min-height:44px;padding:8px 10px;border-radius:8px;border:1px solid #49606c;background:#101a21;color:var(--text);font:inherit}button{min-height:44px;padding:8px 14px;border:0;border-radius:8px;background:var(--accent);font:inherit;font-weight:700;cursor:pointer}.row,.cards{display:flex;gap:12px;flex-wrap:wrap}.card{flex:1 1 190px;background:#102128;border:1px solid var(--line);border-radius:10px;padding:12px}.muted{color:var(--muted)}li{margin:8px 0}.notice{border-left:4px solid var(--warn);padding:12px;background:#30291b}.status{margin-top:12px}.small{font-size:.9rem;color:var(--muted)}a{color:var(--accent)}
</style></head><body><main><p><a href="/tablet/tactics-points">← Táctica y puntos</a></p><h1>Plan post-partido</h1><p class="muted">Estadísticas del juego y sugerencias de mejora táctica basadas en los eventos realmente registrados.</p>
<section><div class="row"><div><label for="match">ID del partido</label><input id="match" type="number" min="1"></div><div><label for="player">ID del jugador</label><input id="player" type="number" min="1"></div><div style="align-self:end"><button id="load">Generar resumen</button></div></div><div id="status" class="status" aria-live="polite"></div></section>
<div id="report" hidden><section><h2>Resumen estadístico</h2><div id="metrics" class="cards"></div></section><section><h2>Rendimiento por golpe</h2><div id="shots"></div></section><section><h2>Comparación por intención táctica</h2><div id="tactics"></div></section><section><h2>Telemetría experimental</h2><div id="telemetry"></div></section><section><h2>Sugerencias de entrenamiento estratégico</h2><ul id="recommendations"></ul><p id="note" class="notice"></p></section></div>
<script>
const $=s=>document.querySelector(s);function esc(s){const d=document.createElement('div');d.textContent=s??'';return d.innerHTML}function metric(k,v){return `<div class="card"><strong>${esc(k)}</strong><br>${esc(v)}</div>`}
$('#load').addEventListener('click',async()=>{const match=Number($('#match').value),player=Number($('#player').value);if(!match||!player){$('#status').textContent='Ingresa un ID de partido y de jugador.';return}$('#status').textContent='Consultando datos…';try{const r=await fetch(`/training-plan/${match}/${player}`),d=await r.json();if(!r.ok)throw Error(d.detail||'No se pudo generar el resumen');const s=d.estadisticas_partido;$('#metrics').innerHTML=[metric('Eventos',s.eventos_registrados),metric('Ganadores',s.ganadores),metric('Errores no forzados',s.errores_no_forzados),metric('Ataques / defensas',`${s.ataques} / ${s.defensas}`),metric('Llegadas a la T',s.llegadas_a_la_t),metric('Strokes / lets',`${s.strokes} / ${s.lets}`)].join('');$('#shots').innerHTML=d.estadisticas_por_golpe.length?'<ul>'+d.estadisticas_por_golpe.map(x=>`<li><strong>${esc(x.tipo_golpe)}</strong>: ${x.intentos} intentos · ${x.ganadores} ganadores (${x.porcentaje_ganador}%) · ${x.errores_no_forzados} errores (${x.porcentaje_error}%)</li>`).join('')+'</ul>':'<p class="small">Sin golpes clasificados.</p>';$('#tactics').innerHTML=d.estadisticas_por_intencion.length?'<ul>'+d.estadisticas_por_intencion.map(x=>`<li><strong>${esc(x.tipo_tactica)}</strong>: ${x.eventos} eventos · ${x.ganadores} ganadores · ${x.errores_no_forzados} errores no forzados</li>`).join('')+'</ul>':'<p class="small">Sin intención táctica registrada.</p>';const t=d.telemetria;$('#telemetry').textContent=`Muestras: ${t.muestras}; promedio experimental rodilla: ${t.promedios_experimentales.valgo_rodilla_deg??'—'}°; flexión lumbar proxy: ${t.promedios_experimentales.flexion_lumbar_proxy_deg??'—'}°; asimetría de zancada: ${t.promedios_experimentales.asimetria_zancada_pct??'—'}%.`;$('#recommendations').innerHTML=d.sugerencias_estrategicas_entrenamiento.map(x=>`<li>${esc(x)}</li>`).join('');$('#note').textContent=d.nota;$('#report').hidden=false;$('#status').textContent='Resumen generado.'}catch(e){$('#report').hidden=true;$('#status').textContent=e.message}});
</script></main></body></html>''')
