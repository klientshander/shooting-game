@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Create a virtual environment and install requirements-build.txt first.
    exit /b 1
)

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "Cosmic Rift.spec"
if errorlevel 1 exit /b %errorlevel%

".venv\Scripts\python.exe" -c "import shutil; shutil.make_archive('dist/cosmic-rift-windows', 'zip', root_dir='dist', base_dir='Cosmic Rift')"
if errorlevel 1 exit /b %errorlevel%

echo.
echo Release folder created in: dist\Cosmic Rift
echo Shareable archive created at: dist\cosmic-rift-windows.zip
