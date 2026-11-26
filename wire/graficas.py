"""Gráficas vectoriales sencillas (SVG de texto) para las interfaces: ROE frente a frecuencia. Python puro."""

from __future__ import annotations

import math

from .i18n import tr

COLORES = ("#2f6b3a", "#c8892b", "#6d7680")


def _paso(rango: float, divisiones: int = 5) -> float:
    bruto = rango / divisiones
    p = 10 ** math.floor(math.log10(bruto))
    for m in (1, 2, 2.5, 5, 10):
        if m * p >= bruto:
            return m * p
    return 10 * p


def _polar(titulo: str, curvas: list[tuple[str, list[float], list[float]]], gmax: float, lado: int, nota: str) -> str:
    """Un diagrama polar: curvas [(nombre, ángulos°, dBi)], 0° arriba y en sentido horario; anillos cada 10 dB bajo el máximo."""
    c, rad = lado / 2, lado / 2 - 34
    pie = 30.0                                              # dB bajo el máximo en el borde
    ra = lambda g: rad * max(0.0, min(1.0, 1 + (g - gmax) / pie))  # noqa: E731
    s = [f'<g><text x="{c}" y="13" text-anchor="middle" font-size="11" font-weight="bold" fill="currentColor">{titulo}</text>']
    for k in (1, 2, 3):
        s.append(f'<circle cx="{c}" cy="{c + 4}" r="{rad * k / 3:.1f}" fill="none" stroke="currentColor" stroke-opacity="0.18"/>'
                 f'<text x="{c + 3}" y="{c + 4 - rad * k / 3 + 9:.1f}" font-size="8" fill="currentColor" fill-opacity="0.7">'
                 f'{10 * k - pie:.0f}</text>')
    for a in range(0, 360, 30):
        x, y = math.sin(math.radians(a)), -math.cos(math.radians(a))
        s.append(f'<line x1="{c}" y1="{c + 4}" x2="{c + rad * x:.1f}" y2="{c + 4 + rad * y:.1f}" stroke="currentColor" stroke-opacity="0.12"/>')
        if a % 90 == 0:
            s.append(f'<text x="{c + (rad + 10) * x:.1f}" y="{c + 4 + (rad + 10) * y + 3:.1f}" text-anchor="middle" font-size="9" '
                     f'fill="currentColor">{a}°</text>')
    for i, (nombre, ang, g) in enumerate(curvas):
        pts = " ".join(f"{c + ra(v) * math.sin(math.radians(a)):.1f},{c + 4 - ra(v) * math.cos(math.radians(a)):.1f}"
                       for a, v in zip(ang, g))
        s.append(f'<polygon points="{pts}" fill="{COLORES[i % 3]}" fill-opacity="0.12" stroke="{COLORES[i % 3]}" stroke-width="2"/>')
    s.append(f'<text x="{c}" y="{lado - 3}" text-anchor="middle" font-size="9" fill="currentColor" fill-opacity="0.8">{nota}</text></g>')
    return "".join(s)


def svg_diagrama(theta, phi, g, lado: int = 280) -> str:
    """Dos cortes polares del diagrama (θ × φ, dBi) por el máximo: azimut (a la θ del máximo) y elevación (plano vertical del máximo).

    En el de elevación 0° es el cénit y los ángulos hasta 180° van del lado del máximo; el otro lado es el plano opuesto.
    """
    import numpy as np
    theta, phi, g = np.asarray(theta, float), np.asarray(phi, float), np.asarray(g, float)
    gmax = float(g.max())
    it, ip = np.unravel_index(int(np.argmax(g)), g.shape)
    azim = [("φ", list(phi) + [360.0], list(g[it, :]) + [g[it, 0]])]
    n = len(phi)
    opuesto = int(round(((phi[ip] + 180.0) % 360.0 - phi[0]) / (phi[1] - phi[0]))) % n
    lado_a = list(g[:, ip])
    lado_b = list(g[:, opuesto])
    ang = list(theta) + [360.0 - t for t in theta[::-1]]
    val = lado_a + lado_b[::-1]
    elev = [("θ", ang, val)]
    w = 2 * lado
    nota = tr("anillos: dB bajo el máximo ({0:.1f} dBi)", gmax)
    cuerpo = (_polar(tr("Azimut (θ = {0:.0f}°)", theta[it]), azim, gmax, lado, nota)
              + f'<g transform="translate({lado} 0)">'
              + _polar(tr("Elevación (φ = {0:.0f}° / {1:.0f}°)", phi[ip], (phi[ip] + 180.0) % 360.0), elev, gmax, lado,
                       nota) + "</g>")
    return (f'<svg viewBox="0 0 {w} {lado}" width="100%" style="max-width:{w}px;color:inherit" font-family="sans-serif" role="img">'
            f'{cuerpo}</svg>')


def _color_ganancia(t: float) -> tuple[float, float, float]:
    """Escala azul → verde → amarillo → rojo para t de 0 a 1 (RGB de 0 a 1)."""
    t = max(0.0, min(1.0, t))
    paradas = ((0.0, (0.15, 0.25, 0.85)), (0.35, (0.1, 0.75, 0.55)), (0.7, (0.95, 0.85, 0.2)), (1.0, (0.9, 0.15, 0.1)))
    for (t0, c0), (t1, c1) in zip(paradas, paradas[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return tuple(a + (b - a) * u for a, b in zip(c0, c1))
    return paradas[-1][1]


def puntos_diagrama(theta, phi, g, piso: float = 25.0):
    """Nube de puntos del diagrama en 3D: (puntos [x, y, z], colores [r, g, b], máximo dBi).

    El radio es proporcional a los dB por encima de `piso` dB bajo el máximo (1 en el máximo) y el color sigue la
    misma escala. Ejes de NEC: θ desde +z, φ desde +x.
    """
    import numpy as np
    g = np.asarray(g, float)
    gmax = float(g.max())
    t = np.clip((g - (gmax - piso)) / piso, 0.0, 1.0)
    th, ph = np.meshgrid(np.radians(theta), np.radians(phi), indexing="ij")
    r = t
    xyz = np.stack([r * np.sin(th) * np.cos(ph), r * np.sin(th) * np.sin(ph), r * np.cos(th)], axis=-1).reshape(-1, 3)
    colores = [_color_ganancia(v) for v in t.reshape(-1)]
    return xyz.tolist(), colores, gmax


def svg_roe(curvas: list[tuple[str, list[float], list[float]]], banda: tuple[float, float] | None = None,
            ancho: int = 560, alto: int = 240, techo: float = 3.0) -> str:
    """ROE frente a frecuencia de una o varias curvas [(nombre, f_MHz, roe)], con la banda sombreada y la leyenda."""
    f0 = min(min(c[1]) for c in curvas)
    f1 = max(max(c[1]) for c in curvas)
    ml, mr, mt, mb = 44, 12, 14, 34
    w, h = ancho - ml - mr, alto - mt - mb
    sx = lambda v: ml + (v - f0) / (f1 - f0) * w  # noqa: E731
    sy = lambda v: mt + h - (min(v, techo) - 1) / (techo - 1) * h  # noqa: E731
    s = [f'<svg viewBox="0 0 {ancho} {alto}" width="100%" style="max-width:{ancho}px;color:inherit" font-family="sans-serif" '
         f'font-size="10" role="img">']
    if banda and min(banda[1], f1) > max(banda[0], f0):
        s.append(f'<rect x="{sx(max(banda[0], f0)):.1f}" y="{mt}" width="{sx(min(banda[1], f1)) - sx(max(banda[0], f0)):.1f}" '
                 f'height="{h}" fill="#c8892b" fill-opacity="0.18"/>')
    paso = _paso(f1 - f0)
    k = math.ceil(f0 / paso - 1e-9)
    while k * paso <= f1 + 1e-9:
        v = k * paso
        s.append(f'<line x1="{sx(v):.1f}" y1="{mt}" x2="{sx(v):.1f}" y2="{mt + h}" stroke="currentColor" stroke-opacity="0.15"/>'
                 f'<text x="{sx(v):.1f}" y="{mt + h + 13}" text-anchor="middle" fill="currentColor">{v:g}</text>')
        k += 1
    v = 1.0
    while v <= techo + 1e-9:
        s.append(f'<line x1="{ml}" y1="{sy(v):.1f}" x2="{ml + w}" y2="{sy(v):.1f}" stroke="currentColor" stroke-opacity="0.15"/>'
                 f'<text x="{ml - 5}" y="{sy(v) + 3.5:.1f}" text-anchor="end" fill="currentColor">{v:g}</text>')
        v += 0.5
    for i, (nombre, f, roe) in enumerate(curvas):
        pts = " ".join(f"{sx(a):.1f},{sy(b):.1f}" for a, b in zip(f, roe))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{COLORES[i % 3]}" stroke-width="2"/>')
        s.append(f'<line x1="{ml + 8 + i * 130}" y1="{mt + 8}" x2="{ml + 26 + i * 130}" y2="{mt + 8}" stroke="{COLORES[i % 3]}" '
                 f'stroke-width="2"/><text x="{ml + 30 + i * 130}" y="{mt + 11.5}" fill="currentColor">{nombre}</text>')
    s.append(f'<rect x="{ml}" y="{mt}" width="{w}" height="{h}" fill="none" stroke="currentColor" stroke-opacity="0.6"/>'
             f'<text x="{ml + w / 2}" y="{alto - 4}" text-anchor="middle" fill="currentColor">MHz</text>'
             f'<text x="12" y="{mt + h / 2}" text-anchor="middle" fill="currentColor" transform="rotate(-90 12 {mt + h / 2})">'
             f'{tr("ROE")}</text></svg>')
    return "".join(s)
