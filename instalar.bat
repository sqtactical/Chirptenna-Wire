@echo off
rem Instala Chirptenna Wire (ver instalar\instalar.ps1). Con -Comprobar solo informa.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar\instalar.ps1" %*
pause
