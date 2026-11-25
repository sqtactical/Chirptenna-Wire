"""Datos reales del dipolo de 145 MHz (varilla de 2 mm) con el motor de la fase 0, para la maqueta del plano."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from wire import dipolo, motor          # noqa: E402
from wire.modelo import Barrido         # noqa: E402

F, R = 145.0, 1.0
largo = 0.48 * 299792.458 / F          # mm, punto de partida
for _ in range(4):
    f, z = motor.resonancia(dipolo(F, R, longitud_mm=largo), 120, 170)
    largo *= f / F
f, z = motor.resonancia(dipolo(F, R, longitud_mm=largo), 120, 170)
f2, _ = motor.resonancia(dipolo(F, R, longitud_mm=largo - 10), 120, 170)
sens = (f2 - f) / 10                    # MHz por mm de largo total
r = motor.simular(dipolo(F, R, longitud_mm=largo), Barrido(140, 150, 41), diagrama=True)
datos = {'f_MHz': F, 'radio_mm': R, 'largo_total_mm': largo, 'f_res_MHz': f, 'R_ohm': z.real, 'X_ohm': z.imag,
         'sens_MHz_por_mm_total': sens, 'f': list(r.frecuencias), 'roe': list(r.roe),
         'ganancia_dBi': max(r.ganancia_max) if r.ganancia_max else None}
json.dump(datos, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in datos.items() if k not in ('f', 'roe')})
print('ROE en 144 y 146 MHz:', round(r.roe[16], 2), round(r.roe[24], 2))
