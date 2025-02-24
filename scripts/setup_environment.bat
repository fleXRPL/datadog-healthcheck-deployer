@echo off
setlocal enabledelayedexpansion

:: Colors for output (Windows 10 and above)
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "NC=[0m"

echo %YELLOW%Starting local environment setup...%NC%

:: Get script directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

:: Function to check if command exists
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo %RED%Python not found. Please install Python 3.9 or higher%NC%
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%I"
echo %GREEN%Found Python %PYTHON_VERSION%%NC%

:: Create and activate virtual environment
echo %YELLOW%Setting up virtual environment...%NC%
if exist venv (
    echo %YELLOW%Found existing virtual environment. Removing...%NC%
    rmdir /s /q venv
)

python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo %RED%Failed to create virtual environment%NC%
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo %RED%Failed to activate virtual environment%NC%
    exit /b 1
)

:: Upgrade pip and install dependencies
echo %YELLOW%Installing dependencies...%NC%
python -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo %RED%Failed to upgrade pip%NC%
    exit /b 1
)

pip install -r requirements-dev.txt
if %ERRORLEVEL% neq 0 (
    echo %RED%Failed to install development dependencies%NC%
    exit /b 1
)

pip install -e .
if %ERRORLEVEL% neq 0 (
    echo %RED%Failed to install package in editable mode%NC%
    exit /b 1
)

:: Set up pre-commit hooks
echo %YELLOW%Setting up pre-commit hooks...%NC%
pre-commit install
if %ERRORLEVEL% neq 0 (
    echo %RED%Failed to set up pre-commit hooks%NC%
    exit /b 1
)

:: Create config directory if it doesn't exist
if not exist config (
    echo %YELLOW%Creating config directory...%NC%
    mkdir config
)

:: Check for DataDog credentials
echo %YELLOW%Checking DataDog credentials...%NC%
if "%DD_API_KEY%"=="" (
    echo %YELLOW%DataDog API key not found in environment.%NC%
    echo Please set up your credentials by running:
    echo setx DD_API_KEY "your-api-key"
)
if "%DD_APP_KEY%"=="" (
    echo %YELLOW%DataDog Application key not found in environment.%NC%
    echo setx DD_APP_KEY "your-app-key"
)

:: Create example configuration if it doesn't exist
if not exist config\healthcheck.yaml (
    echo %YELLOW%Creating example health check configuration...%NC%
    (
        echo version: "1.0"
        echo healthchecks:
        echo   - name: "Example API Check"
        echo     type: "http"
        echo     url: "https://api.example.com/health"
        echo     frequency: 60
        echo     locations:
        echo       - "aws:us-east-1"
        echo     monitors:
        echo       availability:
        echo         enabled: true
        echo         threshold: 99.9
        echo       latency:
        echo         enabled: true
        echo         threshold: 500
        echo     tags:
        echo       - "env:production"
        echo       - "service:api"
    ) > config\healthcheck.yaml
    echo %GREEN%Created example configuration%NC%
)

echo %GREEN%Local environment setup complete!%NC%
echo.
echo Next steps:
echo 1. Set up your DataDog credentials if you haven't already
echo 2. Review and modify config\healthcheck.yaml
echo 3. Run 'dd-healthcheck deploy config\healthcheck.yaml' to deploy your first health check
echo.
echo For more information, visit: https://github.com/fleXRPL/datadog-healthcheck-deployer/wiki/Getting-Started

:: Deactivate virtual environment
deactivate

endlocal 