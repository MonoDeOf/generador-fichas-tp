@echo off
cd /d "%~dp0backend"
echo Instalando dependencias (solo tarda la primera vez)...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo.
  echo No se encontro Python. Instalalo desde https://www.python.org
  echo y marca "Add Python to PATH" durante la instalacion.
  pause
  exit /b
)
python main.py
pause
