# Instala Chirptenna Wire para un usuario de Windows: entorno de Python fuera de OneDrive (las rutas largas fallan),
# paquetes y un acceso para arrancar la interfaz. Idempotente. `-Comprobar` solo informa, sin cambiar nada.
param([switch]$Comprobar, [string]$Python = "")
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$entorno = Join-Path $env:LOCALAPPDATA "chirptenna-wire\venv"
$paquetes = @("nicegui", "PyNEC", "numpy", "fpdf2")

function Buscar-Python {
    if ($Python) { return $Python }
    foreach ($c in @("py -3.14", "py -3.13", "py -3.12", "py -3.11", "python")) {
        try {
            $partes = $c.Split(" ")
            $v = & $partes[0] $partes[1..($partes.Length - 1)] -c "import sys; print(sys.version_info[:2] >= (3, 11))" 2>$null
            if ($v -eq "True") { return $c }
        } catch { }
    }
    return $null
}

$py = Buscar-Python
if (-not $py) { Write-Host "No encuentro Python 3.11 o posterior. Instalalo desde https://www.python.org y vuelve a ejecutar."; exit 1 }
Write-Host "Python: $py"
Write-Host "Entorno: $entorno"
if ($Comprobar) {
    Write-Host ("Entorno creado: " + (Test-Path (Join-Path $entorno "Scripts\python.exe")))
    exit 0
}
if (-not (Test-Path (Join-Path $entorno "Scripts\python.exe"))) {
    New-Item -ItemType Directory -Force (Split-Path $entorno) | Out-Null
    $partes = $py.Split(" ")
    & $partes[0] $partes[1..($partes.Length - 1)] -m venv $entorno
}
$pe = Join-Path $entorno "Scripts\python.exe"
& $pe -m pip install --upgrade pip
& $pe -m pip install @paquetes
$arranque = Join-Path $raiz "iniciar.bat"
@(
    "@echo off",
    "cd /d `"%~dp0`"",
    "start `"`" http://127.0.0.1:8090/",
    "`"$pe`" gui\app.py --puerto 8090"
) | Set-Content -Path $arranque -Encoding ascii
Write-Host "Listo. Para arrancar la interfaz: iniciar.bat (se abre http://127.0.0.1:8090/)."
