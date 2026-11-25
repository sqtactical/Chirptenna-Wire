// Interfaz de Chirptenna Wire web (sin frameworks). Python corre en un Web Worker (motor.js).
// Chirptenna Wire · AGPL-3.0
'use strict';
const $ = (id) => document.getElementById(id);
const trabajador = new Worker('motor.js');
const pendientes = new Map();
let siguiente = 1;
let actual = null;       // {entrada, plano}
let hojaActual = 0;
let coaxial = { tipos: [], cables: [] };

trabajador.onmessage = (ev) => {
  const m = ev.data;
  if (m.progreso) { $('progreso').textContent = m.progreso; return; }
  if (m.listo) { $('progreso').textContent = 'Listo.'; $('generar').disabled = false; iniciar(); return; }
  if (m.fallo) { $('progreso').textContent = 'No se pudo cargar Python: ' + m.fallo; return; }
  const p = pendientes.get(m.id);
  if (!p) return;
  pendientes.delete(m.id);
  m.ok ? p.resolve(m.resultado) : p.reject(new Error(m.error));
};

function llamar(fn, arg) {
  return new Promise((resolve, reject) => {
    const id = siguiente++;
    pendientes.set(id, { resolve, reject });
    trabajador.postMessage({ id, fn, arg });
  });
}

function guardar(nombre, contenido, tipo) {
  const url = URL.createObjectURL(new Blob([contenido], { type: tipo }));
  const a = document.createElement('a');
  a.href = url; a.download = nombre; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

function entrada() {
  return JSON.stringify({ tipo: $('tipo').value, f_MHz: parseFloat($('f').value), diametro_mm: parseFloat($('diametro').value),
                          papel: $('papel').value, unidades: $('unidades').value,
                          cable: $('cable').value || null, vf_medido: $('vf').value ? parseFloat($('vf').value) : null });
}

async function iniciar() {
  const c = await llamar('catalogo');
  $('tipo').innerHTML = c.tipos.map((t) => `<option value="${t.clave}">${t.nombre}</option>`).join('');
  $('banda').innerHTML += c.bandas.map((b) => `<option value="${(b.f_min + b.f_max) / 2}">${b.nombre} (${b.f_min}–${b.f_max} MHz)</option>`).join('');
  coaxial = c.coaxial;
  $('cable').innerHTML = c.coaxial.cables.map((k) => `<option value="${k.nombre}">${k.nombre} (VF ${k.vf})</option>`).join('');
  $('papel').innerHTML = c.plano.papel.map((p) => `<option>${p}</option>`).join('');
  $('unidades').innerHTML = c.plano.unidades.map((p) => `<option>${p}</option>`).join('');
  generar();
}

function mostrar(plano) {
  hojaActual = Math.min(hojaActual, plano.hojas.length - 1);
  $('titulo').textContent = `${plano.tipo} · ${plano.f_MHz} MHz`;
  $('estado').textContent = plano.estado;
  $('cabecera').classList.remove('oculto');
  $('hojas').innerHTML = plano.hojas.map((_, i) => `<button data-i="${i}"${i === hojaActual ? ' disabled' : ''}>Hoja ${i + 1}</button>`).join('');
  $('hojas').classList.toggle('oculto', plano.hojas.length < 2);
  $('vista').innerHTML = plano.hojas[hojaActual];
  $('descargas').classList.remove('oculto');
}

async function generar(textoEntrada) {
  $('generar').disabled = true;
  try {
    const e = textoEntrada || entrada();
    const plano = await llamar('plano_svg', e);
    actual = { entrada: textoEntrada ? e : JSON.stringify({ diseno: plano.diseno }), plano };
    mostrar(plano);
  } catch (err) {
    $('progreso').textContent = 'Error: ' + err.message;
  } finally {
    $('generar').disabled = false;
  }
}

$('tipo').onchange = () => $('coaxial').classList.toggle('oculto', !coaxial.tipos.includes($('tipo').value));
$('generar').onclick = () => { hojaActual = 0; generar(); };
$('banda').onchange = () => { if ($('banda').value) $('f').value = parseFloat($('banda').value).toFixed(3); };
$('hojas').onclick = (ev) => { const i = ev.target.dataset && ev.target.dataset.i; if (i !== undefined) { hojaActual = +i; mostrar(actual.plano); } };
$('abrir').onclick = () => $('archivo').click();
$('archivo').onchange = async () => {
  const f = $('archivo').files[0];
  if (!f) return;
  try {
    const datos = JSON.parse(await f.text());
    hojaActual = 0;
    await generar(JSON.stringify({ diseno: datos }));
    const d = actual.plano.diseno;
    $('tipo').value = d.tipo; $('tipo').onchange(); if (d.cable) { $('cable').value = d.cable.nombre; $('vf').value = d.cable.vf_origen === 'medido' ? d.cable.vf : ''; }
    $('f').value = d.f_MHz; $('diametro').value = d.diametro_mm;
    $('papel').value = d.plano.papel; $('unidades').value = d.plano.unidades;
  } catch (err) {
    $('progreso').textContent = 'No se pudo abrir el diseño: ' + err.message;
  }
  $('archivo').value = '';
};
$('d-pdf').onclick = async () => guardar(actual.plano.nombre + '.pdf', await llamar('plano_pdf', actual.entrada), 'application/pdf');
$('d-svg').onclick = () => guardar(`${actual.plano.nombre}_hoja${hojaActual + 1}.svg`, actual.plano.hojas[hojaActual], 'image/svg+xml');
$('d-nec').onclick = async () => guardar(actual.plano.nombre + '.nec', await llamar('nec_texto', actual.entrada), 'text/plain');
$('d-json').onclick = () => guardar(actual.plano.nombre + '.json', JSON.stringify(actual.plano.diseno, null, 2), 'application/json');

$('tema').onclick = () => {
  const raiz = document.documentElement;
  const oscuro = raiz.dataset.tema ? raiz.dataset.tema === 'oscuro' : matchMedia('(prefers-color-scheme: dark)').matches;
  raiz.dataset.tema = oscuro ? 'claro' : 'oscuro';
  try { localStorage.setItem('tema', raiz.dataset.tema); } catch (e) { /* sin almacenamiento */ }
};
try { const t = localStorage.getItem('tema'); if (t) document.documentElement.dataset.tema = t; } catch (e) { /* sin almacenamiento */ }
