"""Maqueta de plano de una J-pole de Koch de alambre (433 MHz) para Chirptenna Wire: hoja resumen + plantilla a 1:1
repartida en un mosaico de A4 con solape, marcas de registro y mapa de montaje. Cotas ORIENTATIVAS (sin simular)."""
import os
import sys
import math

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle, Arc
from matplotlib.backends.backend_pdf import PdfPages

# Hace falta una copia de Chirptenna (antenas/geometria.py): CHIRPTENNA = ruta de su carpeta.
sys.path.insert(0, os.environ.get('CHIRPTENNA', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'proyecto_generador_antenas')))
from antenas import geometria as g   # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, '..', '..', 'img')
TINTA, GRIS, COBRE, VERDE, ROJO = '#1f2a24', '#6d7680', '#c8892b', '#2f6b3a', '#b04a3a'

# ---- Geometría (mm), cotas orientativas: J-pole de 433 MHz con el radiador λ/2 hecho curva de Koch de iteración 2
F = 433.92
SEP = 20.0                    # separación entre las ramas del adaptador
STUB = 164.0                  # adaptador λ/4 (≈ 0,95·λ/4)
H_KOCH = 230.0                # altura del radiador de Koch (≈ 0,7 del λ/2 recto, sin simular)
TOMA = 28.0                   # punto de toma desde el fondo de la U
DIAM = 2.0
koch = np.array(g.koch(2, (0, STUB), (0, STUB + H_KOCH), 60.0))
if koch[:, 0].min() < -1:     # que las muescas vayan hacia fuera (+x), lejos de la rama corta
    koch[:, 0] *= -1
long_koch = float(np.sum(np.hypot(*np.diff(koch, axis=0).T)))
long_rama_larga = STUB + long_koch
long_alambre = long_rama_larga + math.pi*SEP/2 + STUB         # rama larga + U + rama corta
tramo_koch = H_KOCH/9


def fmt(v, d=0):
    return f'{v:.{d}f}'.replace('.', ',')


def dibujar_antena(ax, k=1.0, marcas=True):
    """La antena en mm reales (origen: fondo de la rama larga)."""
    lw = DIAM*72/25.4*k                                  # el trazo mide 2 mm en el papel a 1:1
    ax.plot([0, 0], [0, STUB], color=COBRE, lw=lw, solid_capstyle='butt')
    ax.plot([-SEP, -SEP], [0, STUB], color=COBRE, lw=lw, solid_capstyle='butt')
    ax.add_patch(Arc((-SEP/2, 0), SEP, SEP, theta1=180, theta2=360, color=COBRE, lw=lw))
    ax.plot(*koch.T, color=COBRE, lw=lw, solid_joinstyle='miter', solid_capstyle='round')
    if not marcas:
        return
    for p in koch[1:-1]:                                  # puntos de doblez
        ax.add_patch(Circle(tuple(p), 1.6, fill=False, ec=TINTA, lw=0.4))
    for x in (0, -SEP):                                   # toma del coaxial
        ax.plot([x - 4, x + 4], [TOMA, TOMA], color=ROJO, lw=0.8)
    ax.text(6, TOMA, f'toma · {fmt(TOMA)} mm\nvivo → rama larga\nmalla → rama corta', fontsize=6, color=ROJO, va='center')
    ax.plot([-SEP - 3, 3], [STUB - 8, STUB - 8], color=GRIS, lw=3, alpha=0.5)
    ax.text(6, STUB - 8, 'separador aislante (PVC)', fontsize=6, color=GRIS, va='center')
    ax.text(-SEP - 4, STUB/2, f'adaptador λ/4 · {fmt(STUB)} mm · separación {fmt(SEP)} mm', fontsize=6,
            rotation=90, ha='right', va='center')
    ax.text(koch[:, 0].max() + 6, STUB + H_KOCH/2, f'radiador de Koch (iteración 2)\n{fmt(H_KOCH)} mm de alto · '
            f'{fmt(long_koch)} mm de alambre\n16 tramos de {fmt(tramo_koch, 1)} mm · dobla en cada ○',
            fontsize=6, va='center')


# ---- Mosaico: área útil de cada hoja (A4 vertical, margen 10, franja de cajetín de 22 mm abajo)
ANCHO_U, ALTO_U, SOLAPE = 190.0, 234.0, 10.0   # ventana del papel: y 32..266
x0w = -SEP - 45                                           # esquina inferior izquierda de la plantilla en el mundo
y0w = -SEP/2 - 15
alto_plantilla = (STUB + H_KOCH + 15) - y0w
n_hojas = math.ceil((alto_plantilla - SOLAPE)/(ALTO_U - SOLAPE))
ventanas = [(x0w, y0w + i*(ALTO_U - SOLAPE)) for i in range(n_hojas)]


def pagina():
    fig = plt.figure(figsize=(210/25.4, 297/25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 210); ax.set_ylim(0, 297); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((10, 10), 190, 277, fill=False, lw=0.8, ec=TINTA))
    return fig, ax


def t(ax, x, y, s, **k):
    k.setdefault('fontsize', 7); k.setdefault('color', TINTA); k.setdefault('family', 'DejaVu Sans')
    ax.text(x, y, s, **k)


def cajetin_mini(fig, ax, hoja, escala):
    """Franja de cajetín de las hojas de plantilla (10..32 mm)."""
    ax.add_patch(Rectangle((10, 10), 190, 22, fill=False, lw=0.8, ec=TINTA))
    ax.imshow(mpimg.imread(os.path.join(IMG, 'grillo-wire.png')), extent=(12, 32, 11, 31), zorder=5)
    t(ax, 36, 25, 'Chirptenna Wire · J-pole de Koch 433 MHz (j_koch_433)', fontsize=7, fontweight='bold')
    t(ax, 36, 19.5, f'Hoja {hoja} · {escala} · alambre de cobre Ø {fmt(DIAM)} mm · 25-11-2026 · CC BY-NC 4.0', fontsize=6)
    t(ax, 36, 14, 'Cotas orientativas, SIN SIMULAR (maqueta del formato)', fontsize=6, color=ROJO)
    # regla de comprobación de 50 mm en la propia franja
    ax.add_patch(Rectangle((142, 22), 50, 0.7, fc=TINTA, ec='none'))
    for mm in range(0, 51, 10):
        ax.plot([142 + mm, 142 + mm], [20.8, 22.7], color=TINTA, lw=0.4)
    t(ax, 142, 14.5, 'esta regla mide 50 mm', fontsize=5.5, color=GRIS)


def registro(ax, x, y, r=4):
    ax.plot([x - r, x + r], [y, y], color=TINTA, lw=0.4); ax.plot([x, x], [y - r, y + r], color=TINTA, lw=0.4)
    ax.add_patch(Circle((x, y), r*0.55, fill=False, lw=0.4, ec=TINTA))


def hoja_resumen(pdf):
    fig, ax = pagina()
    t(ax, 14, 279, 'J-pole de Koch · 433 MHz (alambre)', fontsize=12, fontweight='bold')
    t(ax, 14, 273.5, f'Alambre de cobre Ø {fmt(DIAM)} mm · alimentación con coaxial de 50 Ω en la toma · {n_hojas + 1} hojas A4',
      fontsize=7.5, color=GRIS)
    ax.plot([10, 200], [270, 270], color=TINTA, lw=0.5)
    t(ax, 196, 279, 'MAQUETA · SIN SIMULAR', fontsize=6, color=ROJO, ha='right', fontweight='bold')
    # Vista general reducida (sin escala), con cotas
    t(ax, 14, 264, 'VISTA GENERAL', fontsize=7.5, fontweight='bold')
    t(ax, 14, 259.5, 'Sin escala · la plantilla a 1:1 está en las hojas A1 y A2', fontsize=6.3, color=GRIS, style='italic')
    axv = fig.add_axes([18/210, 95/297, 70/210, 155/297])
    dibujar_antena(axv, k=0.35, marcas=False)
    axv.set_aspect('equal'); axv.axis('off'); axv.set_xlim(-SEP - 30, koch[:, 0].max() + 20); axv.set_ylim(-SEP, STUB + H_KOCH + 10)
    for y0, y1, txt in ((0, STUB, f'{fmt(STUB)}'), (STUB, STUB + H_KOCH, f'{fmt(H_KOCH)}')):
        axv.add_patch(FancyArrowPatch((-SEP - 18, y0), (-SEP - 18, y1), arrowstyle='<|-|>', mutation_scale=5, lw=0.5))
        axv.text(-SEP - 22, (y0 + y1)/2, txt, rotation=90, ha='right', va='center', fontsize=6)
    axv.plot([-6, 6], [TOMA, TOMA], color=ROJO, lw=0.8); axv.text(8, TOMA, 'toma', fontsize=5.5, color=ROJO, va='center')
    # Lista de corte
    x0 = 100
    t(ax, x0, 264, 'LISTA DE CORTE', fontsize=7.5, fontweight='bold')
    t(ax, x0, 259.5, 'Un solo alambre: rama corta + U + rama larga + Koch', fontsize=6.3, color=VERDE, style='italic')
    filas = [('Rama corta (adaptador)', f'{fmt(STUB)} mm'), ('U del fondo (π·S/2)', f'{fmt(math.pi*SEP/2)} mm'),
             ('Rama larga recta', f'{fmt(STUB)} mm'), (f'Curva de Koch (16 tramos de {fmt(tramo_koch, 1)})', f'{fmt(long_koch)} mm'),
             ('Total de alambre', f'{fmt(long_alambre)} mm'), ('Cortar a (con 30 mm de sobrante)', f'{fmt(long_alambre + 30)} mm')]
    for i, (a, b) in enumerate(filas):
        y = 250 - i*5.2
        t(ax, x0, y, a, fontsize=6.4, fontweight='bold' if i >= 4 else 'normal'); t(ax, 196, y, b, fontsize=6.4, ha='right',
                                                                                   fontweight='bold' if i >= 4 else 'normal')
    ax.plot([x0, 196], [227.5, 227.5], color=TINTA, lw=0.4)
    t(ax, x0, 212, 'Materiales: alambre de cobre rígido Ø 2 mm, separador de PVC\n(2 taladros a 20 mm), coaxial RG-58 o RG-316, '
      'termorretráctil.', fontsize=6.2)
    t(ax, x0, 196, 'Montaje:\n1. Une las hojas A1 y A2 (mapa de abajo) y comprueba las reglas.\n'
      '2. Endereza el alambre y dóblalo sobre la plantilla, tramo a tramo:\n    cada ○ es un doblez de 60° o 120°.\n'
      '3. Haz la U con un tubo de Ø 20 mm como molde.\n4. Pon el separador y suelda el coaxial en la toma.\n'
      '5. Mide con el NanoVNA: mueve la toma para la adaptación y recorta\n    la punta de la Koch para subir la frecuencia.', fontsize=6.2,
      va='top')
    # Mapa de montaje
    t(ax, x0, 150, 'MAPA DE MONTAJE DEL MOSAICO', fontsize=7.5, fontweight='bold')
    s = 0.16                                               # escala del mapa
    mx, my = x0 + 10, 64
    for i, (xw, yw) in enumerate(ventanas):
        yy = my + i*(ALTO_U - SOLAPE)*s
        ax.add_patch(Rectangle((mx, yy), ANCHO_U*s, ALTO_U*s, fill=False, lw=0.7, ec=TINTA))
        t(ax, mx + ANCHO_U*s + 2, yy + ALTO_U*s/2, f'hoja A{i + 1}', fontsize=6.5, va='center')
        if i:
            ax.add_patch(Rectangle((mx, yy), ANCHO_U*s, SOLAPE*s, fc=COBRE, alpha=0.3, lw=0))
    p = koch.copy()
    ax.plot(mx + (p[:, 0] - x0w)*s, my + (p[:, 1] - y0w)*s, color=COBRE, lw=0.8)
    ax.plot([mx + (0 - x0w)*s]*2, [my + (0 - y0w)*s, my + (STUB - y0w)*s], color=COBRE, lw=0.8)
    ax.plot([mx + (-SEP - x0w)*s]*2, [my + (0 - y0w)*s, my + (STUB - y0w)*s], color=COBRE, lw=0.8)
    t(ax, x0, 54, f'Solape de {fmt(SOLAPE)} mm (en cobre): recorta el borde superior de A1 por la línea\n'
      'de corte y pega A2 encima haciendo coincidir las marcas ⊕.', fontsize=6)
    cajetin_mini(fig, ax, f'1 de {n_hojas + 1} (resumen)', 'vista sin escala')
    pdf.savefig(fig); fig.savefig(os.path.join(AQUI, 'plano_jpole_koch_p1.png'), dpi=150); plt.close(fig)


def hoja_plantilla(pdf, i):
    fig, ax = pagina()
    xw, yw = ventanas[i]
    # ventana de la plantilla en el papel: x 10..200, y 32..266 (234 mm), a escala 1:1; encabezado por encima
    axp = fig.add_axes([10/210, 32/297, ANCHO_U/210, ALTO_U/297])
    axp.set_xlim(xw, xw + ANCHO_U); axp.set_ylim(yw, yw + ALTO_U); axp.axis('off')
    dibujar_antena(axp)
    t(ax, 14, 278, f'HOJA A{i + 1} · PLANTILLA A ESCALA 1:1', fontsize=9, fontweight='bold')
    t(ax, 14, 273, 'Pon el alambre encima y dóblalo siguiendo la línea. Mide la regla antes de empezar.', fontsize=6.5, color=VERDE)
    ax.plot([10, 200], [266, 266], color=TINTA, lw=0.5)
    for (x, y) in ((16, 38), (194, 38), (16, 260), (194, 260)):
        registro(ax, x, y)
    if i < n_hojas - 1:                                      # zona de solape arriba: se tapa con la hoja siguiente
        ax.add_patch(Rectangle((10, 266 - SOLAPE), 190, SOLAPE, fc=COBRE, alpha=0.12, lw=0))
        ax.plot([10, 200], [266 - SOLAPE, 266 - SOLAPE], color=ROJO, lw=0.6, ls=(0, (4, 2)))
        t(ax, 150, 266 - SOLAPE + 3, f'✂ corta por la línea roja · encima va la hoja A{i + 2}', fontsize=6, color=ROJO, ha='center')
    if i > 0:
        ax.add_patch(Rectangle((10, 32), 190, SOLAPE, fc=COBRE, alpha=0.12, lw=0))
        t(ax, 150, 35, f'franja de solape: va sobre la hoja A{i} ({fmt(SOLAPE)} mm)', fontsize=6, color=ROJO, ha='center')
    cajetin_mini(fig, ax, f'{i + 2} de {n_hojas + 1} (A{i + 1})', 'escala 1:1')
    pdf.savefig(fig); fig.savefig(os.path.join(AQUI, f'plano_jpole_koch_p{i + 2}.png'), dpi=150); plt.close(fig)


with PdfPages(os.path.join(AQUI, 'plano_ejemplo_jpole_koch.pdf')) as pdf:
    hoja_resumen(pdf)
    for i in range(n_hojas):
        hoja_plantilla(pdf, i)
print('hojas de plantilla:', n_hojas, '· alambre total', round(long_alambre), 'mm · Koch', round(long_koch), 'mm',
      '· ancho', round(koch[:, 0].max() - (-SEP)), 'mm')
