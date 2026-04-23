@echo off
setlocal EnableDelayedExpansion

:: Navega para a raiz do projeto (pasta pai de scripts/)
cd /d "%~dp0.."

:: ============================================================
:: Gerador de Patrimônio NTI — Build de Executável
:: Requer: Python 3.10+, PyInstaller, Flet 0.21+, Pillow
:: ============================================================

set APP_NAME=GeradorPatrimonioNTI
set ENTRY=main.py
set DIST_DIR=dist
set BUILD_DIR=build
set ICON_PNG=assets\icon.png
set ICON_ICO=icone.ico
set ASSETS_DIR=assets

echo.
echo  ============================================
echo   Gerador de Patrimônio NTI — Build EXE
echo  ============================================
echo.

:: --- 1. Verificar Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale o Python 3.10+ e tente novamente.
    pause & exit /b 1
)

:: --- 2. Verificar PyInstaller ---
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller nao encontrado. Instalando...
    python -m pip install pyinstaller --quiet
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar PyInstaller.
        pause & exit /b 1
    )
)

:: --- 3. Converter icon.png para icone.ico ---
if not exist "%ICON_PNG%" (
    echo [AVISO] %ICON_PNG% nao encontrado. O executavel usara icone padrao.
    set ICON_ICO=
    goto skip_icon
)

echo [INFO] Convertendo %ICON_PNG% para %ICON_ICO%...
python -c "from PIL import Image; img=Image.open(r'%ICON_PNG%').convert('RGBA'); img.save('%ICON_ICO%', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
if errorlevel 1 (
    echo [AVISO] Falha ao converter icone. Continuando sem icone personalizado.
    set ICON_ICO=
)

:skip_icon

:: --- 4. Limpar builds anteriores ---
echo [INFO] Limpando builds anteriores...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%"  rmdir /s /q "%DIST_DIR%"
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

:: --- 5. Gerar executável ---
echo [INFO] Iniciando build — isso pode levar alguns minutos...
echo.

if defined ICON_ICO (
    set ICON_FLAG=--icon "%ICON_ICO%"
) else (
    set ICON_FLAG=
)

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "%APP_NAME%" ^
    %ICON_FLAG% ^
    --add-data "%ASSETS_DIR%;assets" ^
    --collect-all flet ^
    --hidden-import models ^
    --hidden-import models.patrimonio_model ^
    --hidden-import controllers ^
    --hidden-import controllers.patrimonio_controller ^
    --hidden-import views ^
    --hidden-import views.main_view ^
    --hidden-import config ^
    --hidden-import threading ^
    --hidden-import socket ^
    --hidden-import logging ^
    --hidden-import logging.handlers ^
    --hidden-import supabase ^
    --hidden-import dotenv ^
    "%ENTRY%"

if errorlevel 1 (
    echo.
    echo [ERRO] Falha durante o build. Verifique as mensagens acima.
    goto cleanup
)

:: --- 6. (Removido: cópia de arquivos locais de banco de dados e settings) ---
echo [INFO] O banco de dados agora está rodando integralmente via Supabase (Nuvem).

echo.
echo  ============================================
echo   Build concluido com sucesso!
echo   Executavel: %DIST_DIR%\%APP_NAME%.exe
echo  ============================================
echo.
explorer "%DIST_DIR%"

:cleanup
:: --- 7. Limpar artefatos temporários ---
echo [INFO] Removendo artefatos temporarios...
if exist "%BUILD_DIR%"     rmdir /s /q "%BUILD_DIR%"
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"
if exist "%ICON_ICO%"      del /q "%ICON_ICO%"

pause
