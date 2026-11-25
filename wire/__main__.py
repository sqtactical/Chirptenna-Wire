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
    return disenar(args.tipo, args.f_MHz, args.diametro, ajustar=not args.sin_motor, cable=args.cable,
                   vf_medido=args.vf_medido, **plano)


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
    sub = p.add_subparsers(dest="orden", required=True, title="órdenes", metavar="{plano,nec}")
    for nombre, ayuda in (("plano", "plano en PDF o SVG"), ("nec", "modelo .nec para 4nec2, xnec2c o nec2c")):
        s = sub.add_parser(nombre, help=ayuda, description=ayuda, add_help=False, formatter_class=_Ayuda)
        _en_castellano(s)
        s.add_argument("-h", "--help", action="help", help="muestra esta ayuda y sale")
        s.add_argument("tipo", nargs="?", choices=sorted(TIPOS), help="tipo de antena: " + ", ".join(sorted(TIPOS)))
        s.add_argument("f_MHz", nargs="?", type=float, help="frecuencia en MHz")
        s.add_argument("--diametro", type=float, default=2.0, help="diámetro del alambre en mm (2)")
        s.add_argument("--cable", help="cable coaxial de las antenas de coaxial (RG-58 por defecto)")
        s.add_argument("--vf-medido", type=float, help="factor de velocidad medido del cable (sustituye al de catálogo)")
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
    args = p.parse_args(argv)
    diseno = _diseno(args)

    if args.orden == "nec":
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
