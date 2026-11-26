// Interfaz de Chirptenna Wire web (sin frameworks). Python corre en un Web Worker (motor.js).
// Chirptenna Wire · AGPL-3.0
'use strict';
const $ = (id) => document.getElementById(id);
const trabajador = new Worker('motor.js');
const pendientes = new Map();
let siguiente = 1;
let actual = null;       // {entrada, plano}
let hojaActual = 0;
let tiposCatalogo = [];
let coaxial = { tipos: [], cables: [] };
let plantilla3d = [];
let categorias = [];
let tiposHF = [];
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
                          cable: $('cable').value || null, conector: $('tipo').value === 'gp' ? $('conector').value : null, vf_medido: $('vf').value ? parseFloat($('vf').value) : null,
                          elementos: $('tipo').value === 'yagi' ? parseInt($('elementos').value, 10) : null,
                          relacion: $('tipo').value === 'efhw' ? parseInt($('relacion').value, 10) : null,
                          altura_m: tiposHF.includes($('tipo').value) ? parseFloat($('altura').value) : null,
                          suelo: tiposHF.includes($('tipo').value) ? $('suelo').value : null,
                          bandas: ['abanico', 'trampas'].includes($('tipo').value) ? $('bandas').value.split(',').map((s) => s.trim()).filter(Boolean) : null,
                          potencia_w: $('tipo').value === 'efhw' ? parseFloat($('potencia').value) : null,
                          largo_max_m: $('tipo').value === 'efhw' && $('largo-max').value ? parseFloat($('largo-max').value) : null,
                          eje: $('tipo').value === 'yagi' ? $('eje').value : null,
                          eje_mm: $('tipo').value === 'yagi' && $('eje').value !== 'ninguno' && $('eje-mm').value ? parseFloat($('eje-mm').value) : null });
}

function pintarGaleria() {
  const carta = (k) => `<button type="button" class="carta" data-tipo="${k.clave}" title="${k.resumen}" aria-pressed="${k.clave === $('tipo').value}">` +
    `${k.miniatura}<b>${k.nombre}</b><small>${k.estado}</small></button>`;
  // por categorías (HF, VHF/UHF, coaxial, banda ancha); los tipos que ninguna recoja van al final
  const vistos = new Set();
  let html = categorias.map((c) => {
    const tipos = c.tipos.map((t) => tiposCatalogo.find((k) => k.clave === t)).filter(Boolean);
    tipos.forEach((k) => vistos.add(k.clave));
    return tipos.length ? `<h3 class="categoria">${c.nombre}</h3>${tipos.map(carta).join('')}` : '';
  }).join('');
  html += tiposCatalogo.filter((k) => !vistos.has(k.clave)).map(carta).join('');
  $('galeria').innerHTML = html;
}

async function iniciar() {
  const c = await llamar('catalogo', IDIOMA);
  const tipoActual = $('tipo').value;
  tiposCatalogo = c.tipos;
  categorias = c.categorias || [];
  tiposHF = c.tipos_hf || [];
  $('tipo').innerHTML = c.tipos.map((t) => `<option value="${t.clave}">${t.nombre}</option>`).join('');
  $('banda').innerHTML = '<option value="" data-t>— otra —</option>' + c.bandas.map((b) => `<option value="${(b.f_min + b.f_max) / 2}">${b.nombre} (${b.f_min}–${b.f_max} MHz)</option>`).join('');
  coaxial = c.coaxial;
  plantilla3d = c.plantilla3d || [];
  $('conector').innerHTML = c.conectores.map((k) => `<option>${k}</option>`).join('');
  $('cable').innerHTML = c.coaxial.cables.map((k) => `<option value="${k.nombre}">${k.nombre} (VF ${k.vf})</option>`).join('');
  $('papel').innerHTML = c.plano.papel.map((p) => `<option>${p}</option>`).join('');
  $('unidades').innerHTML = c.plano.unidades.map((p) => `<option>${p}</option>`).join('');
  if (tipoActual) $('tipo').value = tipoActual;
  pintarGaleria();
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
  $('d3d').classList.toggle('oculto', !plantilla3d.includes(plano.diseno.tipo));
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
$('galeria').onclick = (ev) => {
  const carta = ev.target.closest('.carta');
  if (!carta) return;
  $('tipo').value = carta.dataset.tipo;
  $('tipo').onchange();
  hojaActual = 0;
  generar();
};
$('tipo').onchange = () => {
  // al pasar de VHF/UHF a HF (o al revés) la frecuencia de antes no sirve: se propone la de 40 m o la de 2 m
  const f = parseFloat($('f').value);
  const hf = tiposHF.includes($('tipo').value);
  if (hf && !(f >= 1.8 && f <= 30)) { $('f').value = 7.1; $('banda').value = ''; }
  else if (!hf && f < 30) { $('f').value = 145; $('banda').value = ''; }
  $('hf').classList.toggle('oculto', !hf);
  $('hf-bandas').classList.toggle('oculto', !['abanico', 'trampas'].includes($('tipo').value));
  if ($('tipo').value === 'vinv_hf' && parseFloat($('altura').value) === 10) $('altura').value = 12;        // el vértice va más alto
  else if ($('tipo').value !== 'vinv_hf' && parseFloat($('altura').value) === 12) $('altura').value = 10;
  if ($('tipo').value === 'trampas') $('bandas').value = '40 m, 20 m';          // las trampas son de dos bandas
  else if ($('tipo').value === 'abanico') $('bandas').value = '40 m, 20 m, 15 m';
  pintarGaleria(); $('gp').classList.toggle('oculto', $('tipo').value !== 'gp'); $('yagi').classList.toggle('oculto', $('tipo').value !== 'yagi'); $('efhw').classList.toggle('oculto', $('tipo').value !== 'efhw'); $('coaxial').classList.toggle('oculto', !coaxial.tipos.includes($('tipo').value)); };
$('generar').onclick = () => { hojaActual = 0; generar(); };
$('banda').onchange = () => { if ($('banda').value) $('f').value = parseFloat($('banda').value).toFixed(3); };
$('hojas').onclick = (ev) => { const i = ev.target.dataset && ev.target.dataset.i; if (i !== undefined) { hojaActual = +i; mostrar(actual.plano); } };
$('abrir').onclick = () => $('archivo').click();
// VF medido con Chirptenna VNA: el archivo `chirptenna-cable` rellena el campo (mismo criterio que wire.cables.leer_cable_medido).
$('vf-archivo').onchange = async () => {
  const aviso = $('vf-aviso'); aviso.textContent = '';
  const f = $('vf-archivo').files[0];
  if (!f) return;
  try {
    const d = JSON.parse((await f.text()).replace(/^﻿/, ''));
    if (!d || d.formato !== 'chirptenna-cable') throw new Error(T('El archivo no es una medida de cable de Chirptenna VNA.'));
    if (!(typeof d.vf === 'number' && d.vf > 0.3 && d.vf <= 1)) throw new Error(T('El factor de velocidad del archivo no es creíble.'));
    $('vf').value = d.vf;
    aviso.textContent = T('VF {0} cargado{1}.', d.vf, d.nombre ? ` (${d.nombre})` : '');
    if (typeof generar === 'function') generar();
  } catch (e) { aviso.textContent = e.message; }
};
$('archivo').onchange = async () => {
  const f = $('archivo').files[0];
  if (!f) return;
  try {
    const datos = JSON.parse(await f.text());
    hojaActual = 0;
    await generar(JSON.stringify({ diseno: datos }));
    const d = actual.plano.diseno;
    $('tipo').value = d.tipo; $('tipo').onchange(); if (d.geometria && d.geometria.conector) $('conector').value = d.geometria.conector; if (d.cable) { $('cable').value = d.cable.nombre; $('vf').value = d.cable.vf_origen === 'medido' ? d.cable.vf : ''; }
    $('f').value = d.f_MHz; $('diametro').value = d.diametro_mm;
    if (tiposHF.includes(d.tipo)) { $('altura').value = d.geometria.altura_mm / 1000; $('suelo').value = d.geometria.suelo; if (d.geometria.bandas) $('bandas').value = d.geometria.bandas.join(', '); }
    if (d.tipo === 'efhw') { $('relacion').value = Math.round(d.geometria.relacion); $('potencia').value = d.geometria.potencia_w || 100; }
    if (d.tipo === 'yagi') { $('elementos').value = d.geometria.n_elementos || 3; $('eje').value = d.geometria.boom || 'ninguno'; $('eje-mm').value = d.geometria.boom && d.geometria.boom !== 'ninguno' ? d.geometria.boom_mm : ''; }
    $('papel').value = d.plano.papel; $('unidades').value = d.plano.unidades;
  } catch (err) {
    $('progreso').textContent = T('No se pudo abrir el diseño: {0}', err.message);
  }
  $('archivo').value = '';
};
$('d-pdf').onclick = async () => guardar(actual.plano.nombre + '.pdf', await llamar('plano_pdf', actual.entrada), 'application/pdf');
$('d-svg').onclick = () => guardar(`${actual.plano.nombre}_hoja${hojaActual + 1}.svg`, actual.plano.hojas[hojaActual], 'image/svg+xml');
$('d-3d').onclick = async () => {
  try {
    const entrada = JSON.stringify({ ...JSON.parse(actual.entrada), cama_mm: parseFloat($('cama').value), holgura_mm: parseFloat($('holgura').value),
      radio_mm: $('radio').value ? parseFloat($('radio').value) : null });
    guardar(actual.plano.nombre + '_plantilla3d.zip', await llamar('plantilla3d_zip', entrada), 'application/zip');
  } catch (err) { $('progreso').textContent = String(err.message || err); }
};
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
