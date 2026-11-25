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
let TEXTOS = {};
let IDIOMA = 'es';

// Idiomas: el castellano es el texto fuente y la clave (como en el código Python); wire/idiomas/<código>.json los traduce.
function T(texto, ...args) {
  const t = IDIOMA !== 'es' && TEXTOS[texto] ? TEXTOS[texto] : texto;
  return t.replace(/\{(\d+)\}/g, (m, i) => (args[i] !== undefined ? args[i] : m));
}
const estadoTxt = (e) => ({ 'Sin validar': T('Sin validar'), 'Simulado': T('Simulado'), 'Medido': T('Medido') }[e] || e);

function aplicarIdioma() {
  document.documentElement.lang = IDIOMA;
  document.querySelectorAll('[data-t]').forEach((e) => {
    if (e.dataset.t0 === undefined) e.dataset.t0 = e.getAttribute('data-t') || e.textContent.trim();
    e.innerHTML = T(e.dataset.t0);
  });
  document.querySelectorAll('[data-t-placeholder]').forEach((e) => { e.placeholder = T(e.dataset.tPlaceholder); });
  document.querySelectorAll('[data-t-title]').forEach((e) => { e.title = T(e.dataset.tTitle); });
}

async function cargarIdioma(codigo) {
  TEXTOS = {};
  if (codigo !== 'es') {
    try { TEXTOS = (await (await fetch(`idiomas/${codigo}.json`)).json()).textos; } catch (e) { codigo = 'es'; }
  }
  IDIOMA = codigo;
  $('idioma').value = codigo;
  try { localStorage.setItem('idioma', codigo); } catch (e) { /* sin almacenamiento */ }
  aplicarIdioma();
}

function idiomaInicial() {
  const url = new URLSearchParams(location.search).get('idioma');
  let guardado = null;
  try { guardado = localStorage.getItem('idioma'); } catch (e) { /* sin almacenamiento */ }
  const navegador = (navigator.language || 'es').slice(0, 2);
  return [url, guardado, navegador].find((c) => ['es', 'en', 'fr', 'de'].includes(c)) || 'es';
}

trabajador.onmessage = (ev) => {
  const m = ev.data;
  if (m.progreso) { $('progreso').textContent = T(m.progreso); return; }
  if (m.listo) { $('progreso').textContent = T('Listo.'); $('generar').disabled = false; iniciar().then(() => generar()); return; }
  if (m.fallo) { $('progreso').textContent = T('No se pudo cargar Python: {0}', m.fallo); return; }
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
                          papel: $('papel').value, unidades: $('unidades').value, idioma: IDIOMA,
                          cable: $('cable').value || null, vf_medido: $('vf').value ? parseFloat($('vf').value) : null });
}

async function iniciar() {
  const c = await llamar('catalogo', IDIOMA);
  const tipoActual = $('tipo').value;
  $('tipo').innerHTML = c.tipos.map((t) => `<option value="${t.clave}">${t.nombre}</option>`).join('');
  $('banda').innerHTML = '<option value="" data-t>— otra —</option>' + c.bandas.map((b) => `<option value="${(b.f_min + b.f_max) / 2}">${b.nombre} (${b.f_min}–${b.f_max} MHz)</option>`).join('');
  coaxial = c.coaxial;
  $('cable').innerHTML = c.coaxial.cables.map((k) => `<option value="${k.nombre}">${k.nombre} (VF ${k.vf})</option>`).join('');
  $('papel').innerHTML = c.plano.papel.map((p) => `<option>${p}</option>`).join('');
  $('unidades').innerHTML = c.plano.unidades.map((p) => `<option>${p}</option>`).join('');
  if (tipoActual) $('tipo').value = tipoActual;
  aplicarIdioma();
}

function mostrar(plano) {
  hojaActual = Math.min(hojaActual, plano.hojas.length - 1);
  $('titulo').textContent = `${plano.tipo} · ${plano.f_MHz} MHz`;
  $('estado').textContent = estadoTxt(plano.estado);
  $('cabecera').classList.remove('oculto');
  $('hojas').innerHTML = plano.hojas.map((_, i) => `<button data-i="${i}"${i === hojaActual ? ' disabled' : ''}>${T('Hoja {0}', i + 1)}</button>`).join('');
  $('hojas').classList.toggle('oculto', plano.hojas.length < 2);
  $('vista').innerHTML = plano.hojas[hojaActual];
  $('descargas').classList.remove('oculto');
}

async function generar(textoEntrada) {
  $('generar').disabled = true;
  try {
    const e = textoEntrada ? JSON.stringify({ ...JSON.parse(textoEntrada), idioma: IDIOMA }) : entrada();
    const plano = await llamar('plano_svg', e);
    actual = { entrada: JSON.stringify({ diseno: plano.diseno, idioma: IDIOMA }), plano };
    mostrar(plano);
  } catch (err) {
    $('progreso').textContent = T('Error: {0}', err.message);
  } finally {
    $('generar').disabled = false;
  }
}

$('idioma').onchange = async () => {
  await cargarIdioma($('idioma').value);
  $('progreso').textContent = T('Listo.');
  if (actual) { await iniciar(); await generar(JSON.stringify({ diseno: actual.plano.diseno })); }
};
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
    $('progreso').textContent = T('No se pudo abrir el diseño: {0}', err.message);
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

cargarIdioma(idiomaInicial());
