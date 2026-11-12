from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Interfaz de tablet"])


@router.get("/tablet/clinical-profile", response_class=HTMLResponse, include_in_schema=False)
async def clinical_profile_page():
    """Tablet UI for patient profile, performance guidance, and match statistics."""
    return HTMLResponse(content=r'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SquashAnalytics Pro | Ficha y entrenamiento</title>
<style>
:root{color-scheme:dark;--bg:#101820;--panel:#192630;--line:#314653;--text:#edf5f7;--muted:#a9bdc6;--accent:#7be0ad;--warn:#ffd37a;--danger:#ff9b9b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,sans-serif}
header{padding:16px clamp(16px,4vw,48px);border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}a{color:var(--accent);text-decoration:none}
main{max-width:1200px;margin:auto;padding:24px clamp(14px,4vw,40px) 48px}h1{font-size:clamp(1.6rem,3vw,2.2rem);margin:0}h2{font-size:1.25rem;margin:0 0 12px}h3{font-size:1.05rem;margin:0 0 8px}
.muted,.small{color:var(--muted)}.small{font-size:.88rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:16px;margin-top:18px}
section{background:var(--panel);border:1px solid var(--line);border-radius:15px;padding:20px;margin-top:18px}.grid section{margin:0}
label{display:block;font-weight:650;margin:12px 0 5px}input,select{width:100%;min-height:46px;padding:9px 11px;background:#101a21;color:var(--text);border:1px solid #49606c;border-radius:8px;font:inherit}
button{min-height:46px;padding:9px 14px;border:0;border-radius:8px;background:var(--accent);color:#10231a;font:inherit;font-weight:700;cursor:pointer}.danger{background:#ff9b9b}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}.card{padding:14px;background:#102128;border:1px solid var(--line);border-radius:10px}.notice{padding:14px;border-left:4px solid var(--warn);background:#30291b;border-radius:6px;margin-top:14px}.result{padding:12px;background:#10231a;border:1px solid #38644d;border-radius:9px;margin-top:12px}.alert{color:var(--danger)}[hidden]{display:none!important}
.zone-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.zone{background:#102128;border:1px solid var(--line);border-radius:8px;padding:12px;text-align:center}.status{margin-top:12px;min-height:24px}
</style>
</head>
<body>
<header><strong>SquashAnalytics Pro</strong><nav><a href="/docs">API</a> · <a href="/tablet/rm-calculator">Calculadora 1RM</a></nav></header>
<main>
<h1>Ficha clínica y entrenamiento posterior</h1><p class="muted">Panel de apoyo para el jugador y el equipo técnico. Las recomendaciones son orientativas, no diagnósticas ni prescriptivas.</p>
<form id="profile-form">
<div class="grid">
<section><h2>Área 1 · Ficha clínica del paciente</h2>
<label for="match-id">ID del partido</label><input id="match-id" type="number" min="1" required>
<label for="player-id">ID del jugador</label><input id="player-id" type="number" min="1" required>
<label for="name">Nombre</label><input id="name" maxlength="200" autocomplete="name" required>
<label for="age">Edad</label><input id="age" type="number" min="1" max="120" required>
<label for="sport">Deporte</label><input id="sport" maxlength="120" value="Squash" required>
<label for="gender">Género</label><select id="gender"><option value="femenino">Femenino</option><option value="masculino">Masculino</option><option value="otro">Otro / prefiero no indicar</option></select>
<div id="cycle-fields" hidden><label for="cycle">Fase del ciclo (opcional)</label><select id="cycle"><option value="">No especificar</option><option value="1-14">Días 1–14 (referencia no universal)</option><option value="15-28">Días 15–28 (referencia no universal)</option><option value="variable">Variable / otra duración</option></select><p id="cycle-guidance" class="small">La duración y respuesta varían. Ajustar según síntomas y recuperación.</p></div>
</section>
<section><h2>VO₂ máx. estimado</h2>
<label for="vo2-method">Método</label><select id="vo2-method"><option value="cooper">Cooper, 12 minutos</option><option value="rockport">Rockport, 1 milla</option><option value="beep_test">Beep test (registrar manual)</option><option value="manual">Manual</option></select>
<div id="cooper-fields"><label for="distance">Distancia recorrida (metros)</label><input id="distance" type="number" min="1" step="1"></div>
<div id="rockport-fields" hidden><label for="weight">Peso (kg)</label><input id="weight" type="number" min="1" step=".1"><label for="mile-time">Tiempo de 1 milla (minutos decimales)</label><input id="mile-time" type="number" min="1" step=".01"><label for="heart-rate">Frecuencia cardíaca final (lpm)</label><input id="heart-rate" type="number" min="30" max="250"></div>
<div id="manual-fields" hidden><label for="manual-vo2">VO₂ máx. registrado (ml/kg/min)</label><input id="manual-vo2" type="number" min="0" max="100" step=".1"></div>
<div class="actions"><button type="button" id="calculate-vo2">Calcular / actualizar estimación</button></div><div id="vo2-result" class="result" aria-live="polite" hidden></div>
<p class="small">Cooper: (distancia en metros − 504.9) / 44.73. Rockport: ecuación de campo; usa el coeficiente incluido en la fórmula y no sustituye una prueba clínica. Beep test requiere protocolo/ecuación definidos.</p>
<div class="actions"><button type="submit">Guardar ficha en servidor</button></div>
</section>
</div></form>

<section><h2>Área 2 · Entrenamiento posterior al esfuerzo</h2>
<div class="cards">
<div class="card"><h3>Resumen del rendimiento</h3><label for="speed">Velocidad observada</label><select id="speed"><option>Sin evaluar</option><option>Baja</option><option>Media</option><option>Alta</option></select><label for="explosive">Explosividad</label><select id="explosive"><option>Sin evaluar</option><option>Baja</option><option>Media</option><option>Alta</option></select><label for="endurance">Resistencia</label><select id="endurance"><option>Sin evaluar</option><option>Baja</option><option>Media</option><option>Alta</option></select><p class="small">Demandas mixtas: acciones rápidas/explosivas y capacidad de repetir esfuerzos con recuperación.</p></div>
<div class="card"><h3>Alertas biomecánicas observadas</h3><label><input type="checkbox" class="bio-alert" value="Flexión lumbar"> Flexión lumbar</label><label><input type="checkbox" class="bio-alert" value="Flexión de rodilla"> Flexión de rodilla</label><label><input type="checkbox" class="bio-alert" value="Valgo de tobillo"> Valgo de tobillo</label><label><input type="checkbox" class="bio-alert" value="Hiperflexión de muñeca"> Hiperflexión de muñeca</label><label><input type="checkbox" class="bio-alert" value="Rotación de hombro"> Rotación de hombro</label><label><input type="checkbox" class="bio-alert" value="Rotación de tronco"> Rotación de tronco</label><p class="small">Registrar observaciones técnicas; una alerta no equivale a diagnóstico.</p></div>
</div>
<div class="cards" style="margin-top:14px">
<div class="card"><h3>Plan orientativo de gimnasio</h3><ul><li>Potencia y velocidad, con técnica controlada.</li><li>Fuerza de piernas y core.</li><li>Estabilidad articular y control unilateral.</li></ul></div>
<div class="card"><h3>Plan orientativo de cancha</h3><ul><li>Desplazamientos cortos y cambios de dirección.</li><li>Resistencia específica mediante intervalos adaptados.</li><li>Shadow y patrón técnico con control de la carga.</li></ul></div>
<div class="card"><h3>Grupos musculares clave</h3><p>Cuádriceps · glúteos · isquiosurales · core · gemelos/aductores · hombro/escápula · muñeca/antebrazo.</p></div>
<div class="card"><h3>Rangos orientativos</h3><p>Fuerza principal: 60–80% de 1RM. Potencia: 40–70% de 1RM cuando la técnica y velocidad se mantengan.</p><p>Rodilla: rango funcional sugerido de 20–60° solo si es cómodo y adecuado al ejercicio. Controlar tronco, tobillo y muñeca; no imponer un ángulo único.</p><a href="/tablet/rm-calculator">Calcular 1RM estimado →</a></div>
</div>
<div class="notice"><strong>Base de orientación:</strong><br>Los ejercicios de fuerza, potencia y elasticidad deben priorizar fuerza de piernas, core y hombro, manteniendo desplazamientos y estabilidad articular alineados con el patrón de squash.<br>La combinación de alta velocidad, trabajo explosivo y resistencia específica requiere trabajo de fuerza, potencia y control de recuperación.<br>Las alertas en flexión lumbar, rodilla, tobillo y muñeca deben revisarse como señales de patrón técnico, no solo como dolor aislado.<br><br><strong>Seguridad:</strong> no reemplaza diagnóstico ni prescripción individual. Si hay dolor, síntomas persistentes o pérdida de técnica, detener o adaptar el ejercicio y consultar a un profesional cualificado.</div>
</section>

<section><h2>Estadísticas de caída en cancha</h2><p class="muted">Consulta las 6 zonas del partido seleccionado.</p><div class="actions"><button type="button" id="load-zones">Consultar zonas</button><button type="button" class="danger" id="reset-match">Reiniciar estadísticas del partido</button></div><div id="zones" class="zone-grid" style="margin-top:14px"></div><div id="status" class="status" aria-live="polite"></div></section>
</main>
<script>
const $=s=>document.querySelector(s), gender=$('#gender'), cycleFields=$('#cycle-fields'), method=$('#vo2-method'), vo2Result=$('#vo2-result');
function refreshMethod(){ $('#cooper-fields').hidden=method.value!=='cooper'; $('#rockport-fields').hidden=method.value!=='rockport'; $('#manual-fields').hidden=method.value!=='manual'; }
function refreshGender(){cycleFields.hidden=gender.value!=='femenino';}
method.addEventListener('change',refreshMethod); gender.addEventListener('change',refreshGender); refreshMethod(); refreshGender();
$('#cycle').addEventListener('change',()=>{$('#cycle-guidance').textContent=$('#cycle').value==='1-14'?'Referencia general 1–14: considerar fuerza y aeróbico moderado según síntomas y recuperación.':$('#cycle').value==='15-28'?'Referencia general 15–28: resistencia o intervalos solo si la respuesta individual y recuperación lo permiten.':'La duración y respuesta varían; adaptar a síntomas y preferencia.';});
$('#calculate-vo2').addEventListener('click',()=>{let value=null;if(method.value==='cooper'){const d=Number($('#distance').value);if(!d)return alert('Ingresa la distancia de Cooper.');value=(d-504.9)/44.73;}else if(method.value==='rockport'){const age=Number($('#age').value),kg=Number($('#weight').value),time=Number($('#mile-time').value),hr=Number($('#heart-rate').value);if(!age||!kg||!time||!hr)return alert('Completa edad, peso, tiempo y frecuencia cardíaca.');value=132.853-.0769*(kg*2.2046226218)-.3877*age+6.315*(gender.value==='masculino'?1:0)-3.2649*time-.1565*hr;}else if(method.value==='manual'){value=Number($('#manual-vo2').value);if(!Number.isFinite(value)||value<0)return alert('Ingresa un VO₂ máx. válido.');}else return alert('Para Beep test, registra un resultado manual hasta definir protocolo y ecuación.');vo2Result.textContent=`VO₂ máx. estimado: ${Math.max(0,value).toFixed(1)} ml/kg/min`;vo2Result.hidden=false;});
$('#profile-form').addEventListener('submit',async e=>{e.preventDefault();const partido_id=Number($('#match-id').value),jugador_id=Number($('#player-id').value);if(!partido_id||!jugador_id)return alert('Completa ID del partido y del jugador.');const val=vo2Result.hidden?null:Number((vo2Result.textContent.match(/[0-9]+(?:\.[0-9]+)?/)||[])[0]);const data={partido_id,jugador_id,nombre:$('#name').value.trim(),edad:Number($('#age').value),deporte:$('#sport').value.trim(),genero:gender.value,fase_ciclo_menstrual:gender.value==='femenino'?($('#cycle').value||null):null,descripcion_fase:null,entrenamiento_sugerido:null,vo2max_metodo:method.value,vo2max_valor:val,vo2max_formula_hombre:null,vo2max_formula_mujer:null};try{const r=await fetch('/clinical-profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const body=await r.json();if(!r.ok)throw new Error(body.detail||'Error guardando ficha');$('#status').textContent='Ficha guardada en el servidor.';}catch(err){$('#status').textContent=`No se pudo guardar: ${err.message}`;}});
$('#load-zones').addEventListener('click',async()=>{const id=Number($('#match-id').value);if(!id)return alert('Completa el ID del partido.');try{const r=await fetch(`/events/matches/${id}/court-zones`);const data=await r.json();if(!r.ok)throw new Error(data.detail||'Error consultando zonas');$('#zones').innerHTML=data.zonas.map(z=>`<div class="zone"><strong>${z.nombre}</strong><br>${z.porcentaje_caidas}% de caídas<br>Aciertos ${z.aciertos} · Errores ${z.errores}<br><span class="small">Éxito ${z.porcentaje_acierto}%</span></div>`).join('');$('#status').textContent=`Total de caídas: ${data.total_caidas}`;}catch(err){$('#status').textContent=`No se pudo consultar: ${err.message}`;}});
$('#reset-match').addEventListener('click',async()=>{const id=Number($('#match-id').value);if(!id)return alert('Completa el ID del partido.');if(!confirm(`¿Reiniciar los eventos de puntos del partido ${id}? Esta acción no se puede deshacer.`))return;try{const r=await fetch(`/events/matches/${id}/reset`,{method:'DELETE'});const body=await r.json();if(!r.ok)throw new Error(body.detail||'Error reiniciando');$('#zones').innerHTML='';$('#status').textContent=body.mensaje||'Estadísticas reiniciadas.';}catch(err){$('#status').textContent=`No se pudo reiniciar: ${err.message}`;}});
</script>
</body></html>''')
