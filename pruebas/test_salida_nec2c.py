"""Lector de la salida de texto de nec2c (no necesita nec2c)."""

from wire.motor import leer_salida_nec2c

# Bloque con la disposición estándar de la salida NEC-2 (la que imprime nec2c).
SALIDA = """
                        --------- ANTENNA INPUT PARAMETERS ---------
  TAG   SEG       VOLTAGE (VOLTS)         CURRENT (AMPS)         IMPEDANCE (OHMS)        ADMITTANCE (MHOS)     POWER
  NO.   NO.     REAL      IMAGINARY     REAL      IMAGINARY     REAL      IMAGINARY    REAL       IMAGINARY   (WATTS)
    1    13  1.0000E+00  0.0000E+00  1.3858E-02 -1.0168E-03  7.1771E+01  5.2659E+00  1.3858E-02 -1.0168E-03  6.9291E-03

                        --------- ANTENNA INPUT PARAMETERS ---------
  TAG   SEG       VOLTAGE (VOLTS)         CURRENT (AMPS)         IMPEDANCE (OHMS)        ADMITTANCE (MHOS)     POWER
  NO.   NO.     REAL      IMAGINARY     REAL      IMAGINARY     REAL      IMAGINARY    REAL       IMAGINARY   (WATTS)
    1    13  1.0000E+00  0.0000E+00  1.2000E-02  2.0000E-03  8.0000E+01 -1.3333E+01  1.2000E-02  2.0000E-03  6.0000E-03
"""


def test_lee_una_impedancia_por_frecuencia():
    z = leer_salida_nec2c(SALIDA)
    assert z == [complex(71.771, 5.2659), complex(80.0, -13.333)]


def test_salida_vacia():
    assert leer_salida_nec2c("nada") == []
