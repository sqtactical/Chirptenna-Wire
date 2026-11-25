"""Maqueta de un plano A4 de Chirptenna Wire (dipolo de 145 MHz) con los datos reales del motor. Todo en mm del papel:
el PDF sale a tamaño real, así que lo marcado «Escala 1:1» mide lo que dice."""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, '..', '..', 'img')
D = json.load(open(os.path.join(AQUI, 'datos_dipolo.json'), encoding='utf-8'))

TINTA, GRIS, COBRE, VERDE = '#1f2a24', '#6d7680', '#c8892b', '#2f6b3a'
CUBIERTA, PVC = '#26292c', '#efeadf'
HUECO, SOBRANTE = 10.0, 15.0
total = D['largo_total_mm']
brazo = (total - HUECO)/2
sens_brazo = D['sens_MHz_por_mm_total']*2


def fmt(v, d=1):
    return f'{v:.{d}f}'.replace('.', ',')


fig = plt.figure(figsize=(210/25.4, 297/25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 210); ax.set_ylim(0, 297); ax.set_aspect('equal'); ax.axis('off')


def t(x, y, s, **k):
    k.setdefault('fontsize', 7); k.setdefault('color', TINTA); k.setdefault('family', 'DejaVu Sans')
    ax.text(x, y, s, **k)


def rect(x, y, w, h, fc='none', ec=TINTA, lw=0.5, **k):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, **k))


def cota(x0, y0, x1, y1, texto, rot=0):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='<|-|>', mutation_scale=5, lw=0.5, color=TINTA))
    t((x0 + x1)/2, (y0 + y1)/2, texto, ha='center', va='center', rotation=rot, fontsize=6.5,
      bbox=dict(fc='white', ec='none', pad=0.6))


def seccion(x, y, titulo, escala, color=GRIS):
    t(x, y, titulo, fontsize=7.5, fontweight='bold')
    t(x, y - 4.5, escala, fontsize=6.3, color=color, style='italic')


rect(10, 10, 190, 277, lw=0.8)                                       # marco
t(14, 279, 'Dipolo de media onda · 145 MHz (banda de 2 m)', fontsize=12, fontweight='bold')
t(14, 273.5, 'Varilla de latón o aluminio de Ø 2 mm · alimentado con coaxial de 50 Ω', fontsize=7.5, color=GRIS)
ax.plot([10, 200], [270, 270], color=TINTA, lw=0.5)

# ---------------- 1. Vista general (sin escala), en horizontal
seccion(14, 264, 'VISTA GENERAL', 'Sin escala · medidas en mm')
yv, xc = 238, 105
ax.plot([22, xc - 5], [yv, yv], color=COBRE, lw=2.4, solid_capstyle='round')
ax.plot([xc + 5, 188], [yv, yv], color=COBRE, lw=2.4, solid_capstyle='round')
rect(xc - 8, yv - 5, 16, 10, fc=PVC)
ax.plot([xc, xc], [yv - 5, 216], color=CUBIERTA, lw=1.6)              # bajada de coaxial
for k in range(4):
    ax.add_patch(Circle((xc, 222 - k*1.8), 3.4, fill=False, lw=0.6, ec=CUBIERTA))
t(xc + 6, 221, 'choke: 6–8 vueltas de coaxial\nsobre Ø 10 cm (orientativo)', fontsize=5.8, va='center')
cota(22, yv + 9, xc - 5, yv + 9, f'brazo {fmt(brazo)}')
cota(xc + 5, yv + 9, 188, yv + 9, f'brazo {fmt(brazo)}')
cota(22, yv + 17, 188, yv + 17, f'longitud total {fmt(total)}')
t(xc, yv - 9.5, f'aislador · hueco {fmt(HUECO, 0)}', fontsize=6, ha='center', va='center',
  bbox=dict(fc='white', ec='none', pad=0.4))

# ---------------- 2. Lista de corte y simulación
seccion(14, 206, 'LISTA DE CORTE', 'Corta con el sobrante y ajusta después', color=VERDE)
cols = [14, 66, 78, 98]
for j, c in enumerate(['Pieza', 'Cant.', 'Final', 'Cortar a']):
    t(cols[j], 194, c, fontsize=6.5, fontweight='bold')
ax.plot([14, 118], [192.5, 192.5], color=TINTA, lw=0.4)
filas = [('Brazo, varilla Ø 2 mm', '2', f'{fmt(brazo)} mm', f'{fmt(brazo + SOBRANTE, 0)} mm'),
         ('Aislador, PVC 60 × 25 × 5', '1', '—', '—'),
         ('Tornillos M3 × 10 con tuerca', '2', '—', '—'),
         ('Coaxial RG-58, bajada + choke', '1', 'a medida', '—')]
for i, f in enumerate(filas):
    for j, c in enumerate(f):
        t(cols[j], 188 - i*5, c, fontsize=6.3)
t(14, 163, f'Ajuste: recorta los dos brazos por igual. Quitar 1 mm de cada brazo\nsube la resonancia ≈ {fmt(sens_brazo, 2)} MHz '
  f'(1 MHz ≈ {fmt(1/sens_brazo, 1)} mm por brazo).', fontsize=6.2, color=VERDE)

seccion(128, 206, 'SIMULADO (NEC2) · SIN MEDIR', 'Modelo del motor de Chirptenna Wire')
t(128, 194, f'Resonancia {fmt(D["f_res_MHz"])} MHz · R = {fmt(D["R_ohm"])} Ω\nGanancia {fmt(D["ganancia_dBi"], 2)} dBi', fontsize=6.3)
axr = fig.add_axes([136/210, 152/297, 60/210, 32/297])
axr.plot(D['f'], D['roe'], color=VERDE, lw=1)
axr.axvspan(144, 146, color=COBRE, alpha=0.2, lw=0)
axr.set_ylim(1, 2.5); axr.set_xlim(140, 150)
axr.set_xlabel('MHz', fontsize=5.5, labelpad=1); axr.set_ylabel('ROE', fontsize=5.5, labelpad=1)
axr.tick_params(labelsize=5, length=2, pad=1); axr.grid(alpha=0.3, lw=0.4)
t(128, 143, 'ROE mínima ≈ 1,44: un dipolo da ~72 Ω, no 50.\nVale tal cual en 2 m; para bajarla, un adaptador.', fontsize=5.6, color=GRIS)

# ---------------- 3. Detalle del centro, a escala 1:1
ax.plot([10, 200], [134, 134], color='#c9cdd2', lw=0.4)
seccion(14, 129, 'DETALLE DEL CENTRO', 'Escala 1:1 · pon las piezas encima del papel para marcar y pelar', color=VERDE)
yd, xa = 104, 105
rect(xa - 30, yd - 12.5, 60, 25, fc=PVC)                                   # aislador real
rect(xa - 80, yd - 1, 80 - HUECO/2, 2, fc=COBRE, ec='none')                # brazo izquierdo (Ø 2 mm)
rect(xa + HUECO/2, yd - 1, 80 - HUECO/2, 2, fc=COBRE, ec='none')           # brazo derecho
for s in (-1, 1):
    ax.add_patch(Circle((xa + s*14, yd), 1.6, fc='white', ec=TINTA, lw=0.4))     # taladro M3
    ax.add_patch(Circle((xa + s*14, yd), 3.0, fill=False, ec=GRIS, lw=0.3, ls=(0, (1, 1))))
cota(xa - HUECO/2, yd + 16, xa + HUECO/2, yd + 16, fmt(HUECO, 0))
cota(xa - 30, yd - 16, xa + 30, yd - 16, '60')
cota(xa + 34, yd - 12.5, xa + 34, yd + 12.5, '25', rot=90)
cota(xa + 14, yd + 7, xa - 14, yd + 7, '28 (taladros Ø 3,2)')
t(xa - 79, yd + 3.5, '← brazo (sigue)', fontsize=5.8); t(xa + 60, yd + 3.5, 'brazo (sigue) →', fontsize=5.8)
yc = 70                                                                     # coaxial pelado a escala
rect(30, yc - 2.5, 50, 5, fc=CUBIERTA, ec='none')
rect(80, yc - 2.3, 12, 4.6, fc=COBRE, ec='none', hatch='xxxx')
rect(92, yc - 1.5, 6, 3, fc='#f1efe6', lw=0.3)
rect(98, yc - 0.5, 12, 1, fc=COBRE, ec='none')
cota(80, yc + 6.5, 92, yc + 6.5, '12'); cota(92, yc + 6.5, 98, yc + 6.5, '6'); cota(98, yc + 6.5, 110, yc + 6.5, '12')
t(30, yc - 8, 'RG-58 a escala: malla (12) al tornillo del brazo izquierdo · dieléctrico (6) · vivo (12) al derecho.\n'
  'Sella el centro con termorretráctil o silicona neutra.', fontsize=5.8)

# ---------------- 4. Regla de comprobación (abajo a la izquierda)
seccion(14, 53, 'COMPRUEBA LA ESCALA', 'Mide antes de usar el detalle 1:1')
rect(14, 30, 80, 0.8, fc=TINTA, ec='none')
for mm in range(0, 81, 10):
    ax.plot([14 + mm, 14 + mm], [28.5, 30.8], color=TINTA, lw=0.4)
    t(14 + mm, 25.5, str(mm), fontsize=4.8, ha='center', color=GRIS)
rect(14, 34, 20, 7, lw=0.4)
t(37, 37.5, '20 × 7 mm', fontsize=5.5, color=GRIS, va='center')
t(14, 15, 'Si la regla no mide 80 mm, imprime al 100 % («tamaño real»,\nsin «ajustar a la página») y vuelve a medir.', fontsize=5.6)

# ---------------- 5. Cajetín (abajo a la derecha)
rect(104, 10, 96, 40, lw=0.8)
rect(170, 10, 30, 40, lw=0.5)
ax.imshow(mpimg.imread(os.path.join(IMG, 'grillo-wire.png')), extent=(172, 198, 17, 49), zorder=5)
t(185, 12.5, 'Chirptenna Wire', fontsize=5.6, ha='center', fontweight='bold')
campos = [('Diseño', 'dipolo_145'), ('Tipo', 'Dipolo de media onda'), ('Frecuencia', '145 MHz · banda 144–146'),
          ('Material', 'varilla Ø 2 mm · RG-58'), ('Escala', 'varias: ver cada vista'), ('Hoja', '1 de 1 · A4'),
          ('Fecha', '25-11-2026'), ('Versión', 'Chirptenna Wire 0.1-dev'), ('Estado', 'Simulado, sin medir'),
          ('Licencia', 'CC BY-NC 4.0')]
for i, (k, v) in enumerate(campos):
    yy = 46.5 - i*3.75
    t(106, yy, k, fontsize=5.3, color=GRIS); t(122, yy, v, fontsize=5.6)
    if i:
        ax.plot([104, 170], [yy + 2.7, yy + 2.7], color='#c9cdd2', lw=0.3)
t(14, 278 - 286 + 297 - 2, '', fontsize=1)
t(196, 279, 'MAQUETA', fontsize=6, color='#b04a3a', ha='right', fontweight='bold')

fig.savefig(os.path.join(AQUI, 'plano_ejemplo_dipolo.pdf'))
fig.savefig(os.path.join(AQUI, 'plano_ejemplo_dipolo.png'), dpi=150)
print('ok')
