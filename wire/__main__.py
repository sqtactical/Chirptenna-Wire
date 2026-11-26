"""Línea de comandos mínima.

    python -m wire plano jpole 145 --diametro 2 --salida jpole_145.pdf
    python -m wire plano --desde diseno.json --salida plano.svg
    python -m wire nec dipolo 145 --diametro 2 --salida dipolo_145.nec
"""

from __future__ import annotations

import argparse
import os
import sys

from . import nec
from .diseno import TIPOS, Diseno, disenar


def _diseno(args) -> Diseno:
    if args.desde:
        with open(args.desde, encoding="utf-8") as f:
            diseno = Diseno.desde_json(f.read())
        if getattr(args, "idioma", None):
            diseno.plano.idioma = args.idioma
        return diseno
    if not args.tipo or args.f_MHz is None:
        sys.exit("falta el tipo y la frecuencia (o --desde diseno.json)")
    plano = {"papel": args.papel, "unidades": args.unidades, "idioma": args.idioma or "es"}
    cable, vf = args.cable, args.vf_medido
    if args.cable_medido:
        from .cables import leer_cable_medido
        with open(args.cable_medido, encoding="utf-8") as f:
            medido = leer_cable_medido(f.read())
        vf = medido["vf"]
        cable = cable or medido.get("cable") or None      # el nombre del archivo es libre: solo vale si es uno de la tabla
    return disenar(args.tipo, args.f_MHz, args.diametro, ajustar=not args.sin_motor, cable=cable,
                   vf_medido=vf, conector=args.conector, elementos=args.elementos, eje=args.eje, eje_mm=args.eje_mm,
                   relacion=args.relacion, altura_m=args.altura, suelo=args.suelo, potencia_w=args.potencia, largo_max_m=args.largo_max,
                   bandas=[b.strip() for b in args.bandas.split(",")] if args.bandas else None, f_alta_MHz=args.f_alta, **plano)


class _Ayuda(argparse.HelpFormatter):
    """argparse trae «usage:» en inglés; aquí va en castellano."""

    def _format_usage(self, usage, actions, groups, prefix):
        return super()._format_usage(usage, actions, groups, "uso: " if prefix is None else prefix)


def _en_castellano(parser: argparse.ArgumentParser) -> None:
    """Títulos de los grupos de argumentos (argparse no los traduce; atributos privados, por eso con cuidado)."""
    for atributo, titulo in (("_positionals", "argumentos"), ("_optionals", "opciones")):
        grupo = getattr(parser, atributo, None)
        if grupo is not None:
            grupo.title = titulo


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m wire", add_help=False, formatter_class=_Ayuda,
                                description="Chirptenna Wire: planos de antenas de alambre")
    _en_castellano(p)
    p.add_argument("-h", "--help", action="help", help="muestra esta ayuda y sale")
    sub = p.add_subparsers(dest="orden", required=True, title="órdenes", metavar="{plano,nec,plantilla3d,aisladores,s1p}")
    for nombre, ayuda in (("plano", "plano en PDF o SVG"), ("nec", "modelo .nec para 4nec2, xnec2c o nec2c"),
                          ("plantilla3d", "plantilla de doblado para imprimir en 3D (zip con los STL)"),
                          ("aisladores", "aisladores (central y de extremo) para imprimir en 3D, zip con los STL"),
                          ("s1p", "S11 simulado en Touchstone (.s1p) para compararlo con la medida en Chirptenna VNA")):
        s = sub.add_parser(nombre, help=ayuda, description=ayuda, add_help=False, formatter_class=_Ayuda)
        _en_castellano(s)
        s.add_argument("-h", "--help", action="help", help="muestra esta ayuda y sale")
        s.add_argument("tipo", nargs="?", choices=sorted(TIPOS), help="tipo de antena: " + ", ".join(sorted(TIPOS)))
        s.add_argument("f_MHz", nargs="?", type=float, help="frecuencia en MHz")
        s.add_argument("--diametro", type=float, default=2.0, help="diámetro del alambre en mm (2)")
        s.add_argument("--cable", help="cable coaxial de las antenas de coaxial (RG-58 por defecto)")
        s.add_argument("--vf-medido", type=float, help="factor de velocidad medido del cable (sustituye al de catálogo)")
        s.add_argument("--cable-medido", help="JSON del VF medido con Chirptenna VNA (sustituye a --vf-medido)")
        s.add_argument("--conector", choices=("SO-239", "N"), help="conector del ground plane (SO-239 por defecto)")
        s.add_argument("--elementos", type=int, help="número de elementos de la Yagi, de 3 a 15 (3), o de secciones de la colineal, de 2 a 6 (3)")
        s.add_argument("--eje", choices=("ninguno", "aislado", "unido"),
                       help="eje de la Yagi: no metálico (ninguno), metálico con los elementos aislados o con ellos unidos")
        s.add_argument("--eje-mm", type=float, help="diámetro del eje metálico en mm (1 %% de λ)")
        s.add_argument("--relacion", type=int, choices=(9, 49, 64), help="relación del transformador de la EFHW: 9, 49 o 64 (49)")
        s.add_argument("--altura", type=float, help="altura de la EFHW sobre el suelo en m (10)")
        s.add_argument("--suelo", choices=("pobre", "normal", "bueno", "mar"), help="tipo de suelo de la EFHW (normal)")
        s.add_argument("--bandas", help="bandas del dipolo en abanico o con trampas, separadas por comas, p. ej. \"40 m,20 m,15 m\"")
        s.add_argument("--f-alta", type=float, help="banda alta de la colineal bibanda en MHz (433)")
        s.add_argument("--potencia", type=float, help="potencia en W para elegir el núcleo del transformador (100)")
        s.add_argument("--largo-max", type=float, help="largo máximo del hilo de la EFHW en m, si falta sitio")
        s.add_argument("--desde", help="diseno.json guardado antes")
        s.add_argument("--sin-motor", action="store_true", help="cotas de partida, sin ajustar con PyNEC")
        s.add_argument("--salida", required=True, help="archivo de salida (.pdf o .svg; .nec)")
        s.add_argument("--guardar", help="guarda también el diseno.json")
        if nombre == "plano":
            s.add_argument("--papel", choices=("A4", "A3"), default="A4")
            s.add_argument("--unidades", choices=("mm", "pulgadas"), default="mm")
            s.add_argument("--idioma", choices=("es", "en", "fr", "de"), help="idioma del plano (es por defecto)")
        else:
            s.set_defaults(papel="A4", unidades="mm", idioma=None)
        if nombre == "s1p":
            s.add_argument("--f-ini", type=float, help="frecuencia inicial en MHz (el rango de la gráfica de ROE del diseño)")
            s.add_argument("--f-fin", type=float, help="frecuencia final en MHz")
            s.add_argument("--puntos", type=int, default=201, help="puntos del barrido (201)")
        if nombre == "plantilla3d":
            s.add_argument("--cama", type=float, default=200.0, help="lado de la cama de la impresora en mm, cuadrada (200)")
            s.add_argument("--holgura", type=float, default=0.3, help="holgura de los encajes en mm (0,3)")
            s.add_argument("--radio", type=float, help="radio de doblado al eje del alambre en mm (2 × el diámetro, mínimo 3)")
            s.add_argument("--largo-guia", type=float, help="largo de los brazos de la J-pole recta que cubre la plantilla, en mm (250)")
    args = p.parse_args(argv)
    diseno = _diseno(args)

    if args.orden == "plantilla3d":
        from . import impresion3d
        resultado = impresion3d.generar(diseno, cama=(args.cama, args.cama), holgura=args.holgura, largo_guia_mm=args.largo_guia,
                                         radio_mm=args.radio)
        with open(args.salida, "wb") as f:
            f.write(impresion3d.a_zip(resultado))
        for aviso in resultado.avisos:
            print("AVISO:", aviso)
        print(f"{len(resultado.piezas)} STL ({resultado.columnas} × {resultado.filas} baldosas)")
    elif args.orden == "aisladores":
        from . import aisladores
        with open(args.salida, "wb") as f:
            f.write(aisladores.a_zip(diseno))
    elif args.orden == "s1p":
        from . import touchstone
        with open(args.salida, "w", encoding="utf-8", newline="\n") as f:
            f.write(touchstone.s1p(diseno, args.f_ini, args.f_fin, args.puntos))
    elif args.orden == "nec":
        nec.guardar(diseno.modelo(), args.salida)
    else:
        from . import planos
        plano = planos.generar(diseno)
        extension = os.path.splitext(args.salida)[1].lower()
        if extension == ".svg":
            base = os.path.splitext(args.salida)[0]
            for n, hoja in enumerate(plano.hojas, start=1):
                ruta = args.salida if len(plano.hojas) == 1 else f"{base}_{n}.svg"
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(planos.a_svg(hoja))
        elif extension == ".pdf":
            with open(args.salida, "wb") as f:
                f.write(planos.a_pdf(plano))
        else:
            sys.exit("la salida del plano debe ser .pdf o .svg")
    if args.guardar:
        with open(args.guardar, "w", encoding="utf-8") as f:
            f.write(diseno.a_json())
    print(f"{args.salida}: {diseno.nombre_tipo} a {diseno.f_MHz:g} MHz, estado «{diseno.estado}»")
    if args.orden == "plano":
        print("Imprime al 100 % («tamaño real») y comprueba la regla antes de usar los detalles 1:1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
