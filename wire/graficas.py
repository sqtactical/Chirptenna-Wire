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
