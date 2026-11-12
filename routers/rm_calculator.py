from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Calculadora de fuerza"])


@router.get("/tablet/rm-calculator", response_class=HTMLResponse, include_in_schema=False)
async def rm_calculator_page():
    """Estimate one-repetition maximum (1RM) from a submaximal set."""
    return HTMLResponse(
        content=r'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Calculadora de RM | SquashAnalytics Pro</title>
  <style>
    :root { color-scheme:dark; --bg:#101820; --panel:#192630; --line:#314653; --text:#edf5f7; --muted:#a9bdc6; --accent:#7be0ad; --warn:#ffd37a; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--text); font:16px/1.5 system-ui,sans-serif; }
    header { padding:18px clamp(16px,4vw,48px); border-bottom:1px solid var(--line); }
    header a { color:var(--accent); text-decoration:none; }
    main { max-width:760px; margin:auto; padding:24px clamp(14px,4vw,32px) 48px; }
    section { background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:clamp(16px,4vw,24px); }
    h1 { margin-top:0; font-size:clamp(1.6rem,4vw,2.2rem); }
    label { display:block; font-weight:650; margin:14px 0 6px; }
    input,select { width:100%; min-height:48px; padding:10px 12px; color:var(--text); background:#101a21; border:1px solid #49606c; border-radius:9px; font:inherit; }
    button { min-height:48px; padding:10px 16px; margin-top:18px; border:0; border-radius:9px; background:var(--accent); color:#10231a; font:inherit; font-weight:750; cursor:pointer; }
    .muted { color:var(--muted); }
    .result { margin-top:18px; padding:16px; border-radius:10px; background:#10231a; border:1px solid #38644d; }
    .notice { margin-top:18px; padding:14px; border-left:4px solid var(--warn); background:#30291b; border-radius:6px; }
    table { border-collapse:collapse; width:100%; margin-top:12px; }
    th,td { text-align:left; border-bottom:1px solid var(--line); padding:8px; }
  </style>
</head>
<body>
<header><a href="/tablet/clinical-profile">← Ficha clínica</a></header>
<main>
  <section>
    <h1>Estimación de 1RM</h1>
    <p class="muted">Calcula una repetición máxima estimada usando una serie submáxima. El resultado depende del ejercicio, la técnica y la fatiga.</p>
    <label for="load">Carga levantada (kg)</label>
    <input id="load" type="number" min="0.5" step="0.5" inputmode="decimal" placeholder="Ej. 40">
    <label for="reps">Repeticiones completadas</label>
    <input id="reps" type="number" min="1" max="10" step="1" inputmode="numeric" placeholder="Ej. 8">
    <label for="formula">Fórmula de estimación</label>
    <select id="formula">
      <option value="epley">Epley: 1RM = carga × (1 + repeticiones / 30)</option>
      <option value="brzycki">Brzycki: 1RM = carga × 36 / (37 − repeticiones)</option>
    </select>
    <button id="calculate" type="button">Calcular 1RM estimado</button>
    <div id="result" class="result" aria-live="polite" hidden></div>
    <div class="notice"><strong>Seguridad:</strong> es una estimación, no una indicación para probar el máximo. Usa una serie con técnica correcta, sin dolor y dejando repeticiones en reserva; no hagas una prueba máxima sin supervisión cualificada. Los porcentajes de carga mostrados son referencias generales y deben ajustarse a la persona y al ejercicio.</div>
  </section>
</main>
<script>
document.querySelector('#calculate').addEventListener('click', () => {
  const load = Number(document.querySelector('#load').value);
  const reps = Number(document.querySelector('#reps').value);
  const method = document.querySelector('#formula').value;
  if (!Number.isFinite(load) || load <= 0) return alert('Ingresa una carga mayor que cero.');
  if (!Number.isInteger(reps) || reps < 1 || reps > 10) return alert('Usa entre 1 y 10 repeticiones para esta estimación.');

  const oneRm = method === 'epley'
    ? load * (1 + reps / 30)
    : load * 36 / (37 - reps);
  const roundedRm = Math.round(oneRm * 10) / 10;
  const percentages = [0.5, 0.6, 0.7, 0.8, 0.9];
  const rows = percentages.map(p => `<tr><td>${Math.round(p * 100)}% de 1RM</td><td>${(oneRm * p).toFixed(1)} kg</td></tr>`).join('');
  const formulaText = method === 'epley'
    ? `Epley: ${load} × (1 + ${reps} / 30)`
    : `Brzycki: ${load} × 36 / (37 − ${reps})`;
  const box = document.querySelector('#result');
  box.innerHTML = `<strong>1RM estimado: ${roundedRm} kg</strong><p>${formulaText}</p><table><thead><tr><th>Referencia</th><th>Carga calculada</th></tr></thead><tbody>${rows}</tbody></table><p class="muted">Los porcentajes no sustituyen la selección de carga basada en técnica, esfuerzo percibido y supervisión.</p>`;
  box.hidden = false;
});
</script>
</body>
</html>'''
    )
