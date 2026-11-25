"""Logo de Chirptenna Wire: el grillo de Chirptenna (visto desde arriba) con las antenas de cable coaxial pelado
(cubierta negra, malla trenzada de cobre, dieléctrico blanco y vivo de cobre en la punta), y el nombre con «Wire» en
aluminio. El cuerpo del grillo es el de `docs/logo/generar_logo.py` de Chirptenna; aquí no se depende de ese repositorio.

Uso (desde la raíz del repositorio):  python img/generar_logo_wire.py
-> img/logo-wire.svg/.png y img/logo-wire-oscuro.svg/.png (icono + nombre), img/grillo-wire.svg/.png (icono),
   img/icono-192.png, img/icono-512.png y img/favicon-32.png / favicon-16.png
Requiere numpy y matplotlib.
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle, PathPatch
from matplotlib.path import Path

AQUI = os.path.dirname(os.path.abspath(__file__))

# Colores de la familia Chirptenna
COBRE = '#c8892b'            # «tenna» y el cobre de la malla y el vivo
COBRE_OSCURO = '#8a5a17'     # trenzado de la malla
VERDE = '#2f6b3a'
VERDE_CLARO = '#4f9a5c'
VERDE_OSCURO = '#1f4a28'
TEXTO = '#1f2a24'            # «Chirp» sobre claro
TEXTO_OSC = '#e9eee9'        # «Chirp» sobre oscuro
# Propios de Wire
CUBIERTA = '#26292c'         # cubierta negra del coaxial
BORDE_CUBIERTA = '#6b737c'   # borde de la cubierta sobre fondo oscuro
DIELECTRICO = '#f1efe6'      # dieléctrico de PE
ALUMINIO = {'claro': '#7f8c98', 'oscuro': '#b9c3cc'}   # «Wire»: contraste 3,4:1 sobre blanco y 9,8:1 sobre #14182a
FONDO_OSC = '#14182a'


def arco(s, n=200):
    """Curva de cada antena: la misma por la que van las de Koch en el logo de Chirptenna, suavizada (Bézier cúbica)."""
    p = np.array([(s*0.12, 1.25), (s*0.75, 2.35), (s*1.55, 3.05), (s*2.55, 3.45)])
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t)**3*p[0] + 3*(1 - t)**2*t*p[1] + 3*(1 - t)*t**2*p[2] + t**3*p[3]


def trozo(curva, a, b):
    """Parte de la curva entre las fracciones a y b de su longitud."""
    d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(curva, axis=0).T))])
    d /= d[-1]
    return curva[(d >= a) & (d <= b)]


def tira(ax, pts, ancho, color, z, cap='butt'):
    ax.plot(*pts.T, color=color, lw=ancho, solid_capstyle=cap, solid_joinstyle='round', zorder=z)


def antena_coaxial(ax, s, k, oscuro, simple):
    """Coaxial pelado. `simple` (iconos pequeños): sin trenzado ni dieléctrico, solo cubierta, malla y vivo."""
    c = arco(s)
    if oscuro:
        tira(ax, trozo(c, 0.0, 0.585), 10.5*k, BORDE_CUBIERTA, 1.5)
    tira(ax, trozo(c, 0.0, 0.58), 8.5*k, CUBIERTA, 2)
    malla = trozo(c, 0.58, 0.82 if simple else 0.80)
    tira(ax, malla, 8.5*k, COBRE, 2)
    if not simple:
        d = np.diff(malla, axis=0)
        for i in range(2, len(malla) - 2, 3):
            tx, ty = d[min(i, len(d) - 1)]/np.hypot(*d[min(i, len(d) - 1)])
            n, t = np.array([-ty, tx]), np.array([tx, ty])
            for sg in (1, -1):
                p0, p1 = malla[i] + n*0.085 + t*0.077*sg, malla[i] - n*0.085 - t*0.077*sg
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=COBRE_OSCURO, lw=0.9*k, zorder=3)
        tira(ax, trozo(c, 0.80, 0.89), 4.6*k, DIELECTRICO, 2)
        tira(ax, trozo(c, 0.89, 1.0), 2.4*k, COBRE, 2, cap='round')
    else:
        tira(ax, trozo(c, 0.82, 1.0), 3.2*k, COBRE, 2, cap='round')


def pata(ax, puntos, ancho):
    ax.plot(*np.array(puntos).T, color=VERDE_OSCURO, lw=ancho, solid_capstyle='round', solid_joinstyle='round', zorder=1)


def grillo(ax, k=1.0, oscuro=False, simple=False):
    for s in (1, -1):
        antena_coaxial(ax, s, k, oscuro, simple)
    for s in (1, -1):
        pata(ax, [(s*0.42, 0.45), (s*1.05, 0.95), (s*1.25, 1.45)], 6*k)
        pata(ax, [(s*0.5, 0.0), (s*1.25, -0.15), (s*1.6, 0.25)], 6*k)
        pata(ax, [(s*0.55, -0.55), (s*1.35, -1.25), (s*1.2, -2.55)], 12*k)
        pata(ax, [(s*1.2, -2.55), (s*1.55, -3.35)], 5*k)
        pata(ax, [(s*0.18, -2.95), (s*0.42, -3.6)], 3.5*k)
    ax.add_patch(Ellipse((0, -1.45), 1.35, 2.75, color=VERDE, zorder=3))
    alas = Path([(0, -0.35), (0.62, -1.2), (0.38, -2.75), (0, -2.85), (-0.38, -2.75), (-0.62, -1.2), (0, -0.35)],
                [Path.MOVETO] + [Path.LINETO]*5 + [Path.CLOSEPOLY])
    ax.add_patch(PathPatch(alas, color=VERDE_CLARO, zorder=4))
    for y in (-1.05, -1.6, -2.15):
        ax.plot([-0.42, 0.42], [y, y], color=VERDE, lw=2.2*k, zorder=5)
    ax.plot([0, 0], [-0.4, -2.8], color=VERDE, lw=2.2*k, zorder=5)
    ax.add_patch(Ellipse((0, 0.35), 1.25, 0.95, color=VERDE_OSCURO, zorder=6))
    ax.add_patch(Circle((0, 1.05), 0.48, color=VERDE, zorder=7))
    for s in (1, -1):
        ax.add_patch(Circle((s*0.25, 1.2), 0.11, color=TEXTO, zorder=8))
        ax.add_patch(Circle((s*0.22, 1.24), 0.035, color='white', zorder=9))


def lienzo_icono():
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.set_xlim(-3.1, 3.1); ax.set_ylim(-3.9, 4.0); ax.set_aspect('equal'); ax.axis('off')
    fig.subplots_adjust(0, 0, 1, 1)
    return fig, ax


def guardar(fig, nombre, exts=('svg', 'png'), dpi=200):
    for ext in exts:
        fig.savefig(os.path.join(AQUI, f'{nombre}.{ext}'), transparent=True, dpi=dpi if ext == 'png' else None)
    plt.close(fig)


def logo_texto(nombre, oscuro):
    fig, ax = plt.subplots(figsize=(11.9, 3))
    grillo(ax, oscuro=oscuro)
    tema = 'oscuro' if oscuro else 'claro'
    ax.text(3.6, 0.35, 'Chirp', color=TEXTO_OSC if oscuro else TEXTO, fontsize=58, fontweight='bold', va='center',
            ha='left', family='DejaVu Sans')
    ax.text(9.65, 0.35, 'tenna', color=COBRE, fontsize=58, fontweight='bold', va='center', ha='left', family='DejaVu Sans')
    ax.text(17.35, 0.35, 'Wire', color=ALUMINIO[tema], fontsize=58, fontweight='bold', va='center', ha='left',
            family='DejaVu Sans')
    ax.text(3.65, -1.85, 'wire and coax antenna plans · NEC2', color=VERDE_CLARO if oscuro else VERDE, fontsize=15,
            va='center', ha='left', family='DejaVu Sans')
    ax.set_xlim(-3.1, 23.8); ax.set_ylim(-3.9, 4.0); ax.set_aspect('equal'); ax.axis('off')
    fig.subplots_adjust(0, 0, 1, 1)
    guardar(fig, nombre)


def main():
    logo_texto('logo-wire', oscuro=False)
    logo_texto('logo-wire-oscuro', oscuro=True)
    fig, ax = lienzo_icono()
    grillo(ax)
    guardar(fig, 'grillo-wire')
    for px, k in ((512, 1.0), (192, 1.3)):     # el grosor ya escala con el tamaño; a 192 px algo más grueso
        fig, ax = lienzo_icono()
        grillo(ax, k=k, oscuro=True)       # los iconos caen sobre fondos claros u oscuros: cubierta siempre con borde
        guardar(fig, f'icono-{px}', exts=('png',), dpi=px/4)
    for px in (32, 16):      # favicon: coaxial simplificado y trazos gruesos para que se lea
        fig, ax = lienzo_icono()
        grillo(ax, k=1.9 if px == 32 else 2.3, oscuro=True, simple=True)
        guardar(fig, f'favicon-{px}', exts=('png',), dpi=px/4)
    print('Logo guardado en', AQUI)


if __name__ == '__main__':
    main()
