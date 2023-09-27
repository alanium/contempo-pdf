@echo off
setlocal enabledelayedexpansion

echo Seleccione el tipo de commit:
echo 1. fix: Falla corregida.
echo 2. feat: Nueva funcion.
echo 3. docs: Actualizada la documentacion.
echo 4. style: Formateo del codigo.
echo 5. chore: Actualizadas las dependencias.

set /p commit_type=Ingrese el numero correspondiente al tipo de commit: 

if "%commit_type%"=="1" (
    set type=fix
) else if "%commit_type%"=="2" (
    set type=feat
) else if "%commit_type%"=="3" (
    set type=docs
) else if "%commit_type%"=="4" (
    set type=style
) else if "%commit_type%"=="5" (
    set type=chore
) else (
    echo Tipo de commit no válido.
    exit /b 1
)

set /p commit_description=Ingrese la descripcion del commit: 

echo Realizando commit: %type%: %commit_description%

git add .
git commit -m "%type%: %commit_description%"
git pull origin main
git push origin main

endlocal
 