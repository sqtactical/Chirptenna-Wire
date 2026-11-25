"""Imagen para la vista previa en redes (GitHub «Social preview»): 1280 × 640 px, fondo oscuro, logo y lema.

    python img/generar_social.py      →  img/social-preview.png (Pillow, que ya trae fpdf2)

GitHub recomienda 1280 × 640 y menos de 1 MB; deja ~40 px de margen porque algunas redes recortan los bordes.
"""
import os

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(AQUI, "..", "wire", "planos", "recursos")
FONDO, TINTA, SUAVE, COBRE = (20, 24, 26), (233, 238, 233), (154, 167, 160), (200, 137, 43)


def main() -> None:
    lienzo = Image.new("RGB", (1280, 640), FONDO)
    logo = Image.open(os.path.join(AQUI, "logo-wire-oscuro.png")).convert("RGBA")
    ancho = 1040
    logo = logo.resize((ancho, round(logo.height * ancho / logo.width)), Image.LANCZOS)
    x = (1280 - ancho) // 2
    lienzo.paste(logo, (x, 120), logo)
    d = ImageDraw.Draw(lienzo)
    negrita = ImageFont.truetype(os.path.join(FUENTES, "DejaVuSans-Bold.ttf"), 38)
    normal = ImageFont.truetype(os.path.join(FUENTES, "DejaVuSans.ttf"), 28)
    d.text((640, 410), "Planos de antenas de alambre, varilla y coaxial", font=negrita, fill=TINTA, anchor="mm")
    d.text((640, 470), "Dipolo · J-pole · discone · colineal CoCo  ·  simulación NEC2  ·  A4 a tamaño real",
           font=normal, fill=SUAVE, anchor="mm")
    d.rectangle((x, 540, x + ancho, 543), fill=COBRE)
    d.text((640, 585), "github.com/sqtactical/Chirptenna-Wire", font=normal, fill=SUAVE, anchor="mm")
    destino = os.path.join(AQUI, "social-preview.png")
    lienzo.save(destino, optimize=True)
    print(destino, os.path.getsize(destino) // 1024, "KB")


if __name__ == "__main__":
    main()
