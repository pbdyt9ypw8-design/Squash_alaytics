from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Interfaz de tablet"])


@router.get("/tablet/clinical-profile", response_class=HTMLResponse, include_in_schema=False)
async def clinical_profile_page():
    """Tablet-friendly starter UI for patient profile and VO2max estimation."""
    return HTMLResponse(
        content=r'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ficha clínica | SquashAnalytics Pro</title>
  <style>
    :root { color-scheme: dark; --bg:#101820; --panel:#192630; --line:#314653; --text:#edf5f7; --muted:#a9bdc6; --accent:#7be0ad; --warn:#ffd37a; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--text); font:16px/1.5 system-ui,sans-serif; }
    header { padding:18px clamp(16px,4vw,48px); border-bottom:1px solid var(--line); display:flex; justify-content:space-between; align-items:center; gap:16px; }
    header a { color:var(--accent); text-decoration:none; }
    main { max-width:1100px; margin:auto; padding:24px clamp(14px,4vw,40px) 48px; }
    h1 { margin:0 0 6px; font-size:clamp(1.6rem,3vw,2.2rem); }
    h2 { margin-top:0; font-size:1.2rem; }
    .muted { color:var(--muted); }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr)); gap:18px; margin-top:22px; }
    section { background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:20px; }
    label { display:block; font-weight:650; margin:12px 0 6px; }
    input,select { width:100%; min-height:48px; padding:10px 12px; color:var(--text); background:#101a21; border:1px solid #49606c; border-radius:9px; font:inherit; }
    button { min-height:48px; padding:10px 16px; border:0; border-radius:9px; background:var(--accent); color:#10231a; font-weight:750; font:inherit; cursor:pointer; }
    .actions { display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }
    .result { margin-top:16px; padding:14px; border-radius:10px; background:#10231a; border:1px solid #38644d; }
    .notice { margin-top:18px; padding:14px; border-left:4px solid var(--warn); background:#30291b; border-radius:6px; }
    [hidden] { display:none !important; }
    @media (max-width:600px) { header { align-items:flex-start; flex-direction:column; } section { padding:16px; } }
  </style>
</head>
<body>
<header><strong>SquashAnalytics Pro</strong><a href="/docs">Abrir API docs</a></header>
<main>
  <h1>Ficha clínica del paciente</h1>
  <p class="muted">Perfil deportivo y estimación orientativa de VO₂ máx. Completa solo datos necesarios y con consentimiento.</p>
  <form id="profile-form">
    <div class="grid">
      <section>
        <h2>Datos del paciente</h2>
        <label for="name">Nombre</label><input id="name" name="name" autocomplete="name" required maxlength="200">
        <label for="age">Edad</label><input id="age" name="age" type="number" min="1" max="120" required>
        <label for="sport">Deporte</label><input id="sport" name="sport" value="Squash" required maxlength="120">
        <label for="gender">Género para la ecuación seleccionada</label>
        <select id="gender" name="gender"><option value="femenino">Femenino</option><option value="masculino">Masculino</option><option value="otro">Otro / prefiero no indicar</option></select>
        <div id="cycle-fields" hidden>
          <label for="cycle">Fase/día del ciclo (opcional, según lo que la paciente quiera compartir)</label>
          <select id="cycle" name="cycle"><option value="">No especificar</option><option value="1-14">Días 1–14 (orientativo)</option><option value="15-28">Días 15–28 (orientativo)</option><option value="variable">Variable / otra duración</option></select>
          <p id="cycle-guidance" class="muted" aria-live="polite">Las fases y duración varían entre personas y ciclos. Ajustar la carga según síntomas, recuperación y criterio profesional.</p>
        </div>
      </section>
      <section>
        <h2>Estimación de VO₂ máx.</h2>
        <label for="method">Método</label>
        <select id="method"><option value="cooper">Cooper (12 minutos)</option><option value="rockport">Rockport (1 milla caminando)</option><option value="beep">Beep test (mostrar fórmula, cálculo pendiente)</option></select>
        <div id="cooper-inputs"><label for="distance">Distancia en 12 minutos (metros)</label><input id="distance" type="number" min="1" step="1" placeholder="Ej. 2400"></div>
        <div id="rockport-inputs" hidden>
          <label for="weight">Peso (kg)</label><input id="weight" type="number" min="1" step="0.1">
          <label for="mile-time">Tiempo de 1 milla (minutos decimales)</label><input id="mile-time" type="number" min="1" step="0.01">
          <label for="hr">Frecuencia cardíaca al final (lpm)</label><input id="hr" type="number" min="30" max="250">
        </div>
        <div id="beep-inputs" hidden><p>El cálculo requiere elegir una ecuación validada para el protocolo y la población utilizados. No se calcula automáticamente para evitar una estimación engañosa.</p></div>
        <div class="actions"><button type="button" id="calculate">Calcular VO₂ máx.</button><button type="submit">Guardar en este dispositivo</button></div>
        <div id="vo2-result" class="result" aria-live="polite" hidden></div>
      </section>
    </div>
  </form>
  <div class="notice"><strong>Nota de salud:</strong> el VO₂ máx. es una estimación de campo, no un diagnóstico. La recomendación de ejercicio y el ciclo menstrual no deben basarse solo en rangos fijos de días; adaptar el entrenamiento a síntomas, respuesta individual y evaluación profesional.</div>
  <section style="margin-top:18px">
    <h2>Integración de partido</h2>
    <p class="muted">El resumen de zonas existente se consulta desde <code>/events/matches/{partido_id}/court-zones</code>. Introduce un ID de partido para abrir ese recurso.</p>
    <label for="match-id">ID del partido</label><input id="match-id" type="number" min="1" placeholder="Ej. 1">
    <div class="actions"><button type="button" id="open-zones">Ver estadísticas de zonas</button></div>
  </section>
</main>
<script>
const gender = document.querySelector('#gender');
const cycleFields = document.querySelector('#cycle-fields');
const cycle = document.querySelector('#cycle');
const guidance = document.querySelector('#cycle-guidance');
const method = document.querySelector('#method');
const result = document.querySelector('#vo2-result');
function updateCycle() { cycleFields.hidden = gender.value !== 'femenino'; }
gender.addEventListener('change', updateCycle); updateCycle();
cycle.addEventListener('change', () => {
  const messages = {
    '1-14': 'Orientación opcional: considerar fuerza y aeróbico moderado si la paciente se siente bien; ajustar intensidad individualmente.',
    '15-28': 'Orientación opcional: incluir resistencia o intervalos si hay buena recuperación; no asumir que esta fase permite alta intensidad a todas.',
    'variable': 'Los ciclos varían: ajustar según síntomas, recuperación y preferencia individual.',
    '': 'Las fases y duración varían entre personas y ciclos. Ajustar la carga según síntomas, recuperación y criterio profesional.'
  };
  guidance.textContent = messages[cycle.value] || messages[''];
});
method.addEventListener('change', () => {
  document.querySelector('#cooper-inputs').hidden = method.value !== 'cooper';
  document.querySelector('#rockport-inputs').hidden = method.value !== 'rockport';
  document.querySelector('#beep-inputs').hidden = method.value !== 'beep';
  result.hidden = true;
});
document.querySelector('#calculate').addEventListener('click', () => {
  let vo2;
  if (method.value === 'cooper') {
    const meters = Number(document.querySelector('#distance').value);
    if (!meters || meters <= 0) return alert('Ingresa la distancia recorrida en metros.');
    // Ecuación Cooper: VO2max = (distancia en metros - 504.9) / 44.73.
    vo2 = (meters - 504.9) / 44.73;
  } else if (method.value === 'rockport') {
    const age = Number(document.querySelector('#age').value);
    const kg = Number(document.querySelector('#weight').value);
    const time = Number(document.querySelector('#mile-time').value);
    const hr = Number(document.querySelector('#hr').value);
    if (!age || !kg || !time || !hr) return alert('Completa edad, peso, tiempo y frecuencia cardíaca.');
    const sexCoefficient = gender.value === 'masculino' ? 1 : 0;
    const pounds = kg * 2.2046226218;
    // Rockport estimate; sex coefficient is 1 male, 0 female in this equation.
    vo2 = 132.853 - 0.0769 * pounds - 0.3877 * age + 6.315 * sexCoefficient - 3.2649 * time - 0.1565 * hr;
  } else {
    return alert('Elige Cooper o Rockport para un cálculo. El Beep test queda como opción hasta configurar el protocolo y una ecuación validada.');
  }
  result.textContent = `VO₂ máx. estimado: ${Math.max(0, vo2).toFixed(1)} ml/kg/min. Resultado orientativo; la ecuación Cooper es la misma para todos los géneros y Rockport incorpora su coeficiente según su fórmula.`;
  result.hidden = false;
});
document.querySelector('#profile-form').addEventListener('submit', event => {
  event.preventDefault();
  const data = {
    nombre: document.querySelector('#name').value.trim(), edad: Number(document.querySelector('#age').value),
    deporte: document.querySelector('#sport').value.trim(), genero: gender.value,
    fase_ciclo_menstrual: gender.value === 'femenino' ? (cycle.value || null) : null,
    vo2max_metodo: method.value, vo2max_estimado: result.hidden ? null : result.textContent,
    guardado_en: new Date().toISOString()
  };
  const profiles = JSON.parse(localStorage.getItem('squash-clinical-profiles') || '[]');
  profiles.push(data); localStorage.setItem('squash-clinical-profiles', JSON.stringify(profiles));
  alert('Ficha guardada en este dispositivo. Aún no se sincroniza con el servidor.');
});
document.querySelector('#open-zones').addEventListener('click', () => {
  const id = Number(document.querySelector('#match-id').value);
  if (!id) return alert('Ingresa un ID de partido.');
  window.open(`/events/matches/${id}/court-zones`, '_blank', 'noopener');
});
</script>
</body>
</html>'''
    )
