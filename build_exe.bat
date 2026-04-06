@echo off
REM FeedMind Windows Executable Build Script
REM This script automates the process of building FeedMind.exe

echo ========================================
echo FeedMind v3.7 - Windows Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>NUL
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed!
    echo Please install it first: pip install pyinstaller
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking PyInstaller installation...
python -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)"
echo.

REM Clean previous builds
echo [2/4] Cleaning previous builds...
if exist build (
    echo Removing build directory...
    rmdir /s /q build
)
if exist dist (
    echo Removing dist directory...
    rmdir /s /q dist
)
echo Clean complete.
echo.

REM Build with PyInstaller
echo [3/4] Building FeedMind.exe...
echo This may take 2-5 minutes...
echo.
pyinstaller feedmind.spec

REM Check if build was successful
echo.
echo [4/4] Checking build result...
if exist dist\FeedMind.exe (
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created: dist\FeedMind.exe

    REM Get file size
    for %%A in (dist\FeedMind.exe) do echo File size: %%~zA bytes

    echo.
    echo Next steps:
    echo 1. Test the executable: cd dist ^&^& FeedMind.exe
    echo 2. Check all features work correctly
    echo 3. Distribute dist\FeedMind.exe to users
    echo.
    echo Opening dist folder...
    explorer dist
) else (
    echo.
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo - Missing dependencies (install with pip)
    echo - Incorrect file paths in spec file
    echo - Corrupted PyInstaller installation
    echo.
    echo Try running: pip install --upgrade pyinstaller
    echo.
)

echo.
pause
