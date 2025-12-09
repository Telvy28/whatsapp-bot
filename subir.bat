@echo off
echo ==========================================
echo    SUBIENDO CAMBIOS A GITHUB Y RAILWAY
echo ==========================================

git add .
set /p mensaje="Escribe el mensaje del cambio: "
git commit -m "%mensaje%"
git push

echo.
echo ==========================================
echo      LISTO! REVISA LOS LOGS EN RAILWAY
echo ==========================================
pause