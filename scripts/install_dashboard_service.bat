@echo off
REM ============================================================================
REM  Job Intelligence Dashboard - Windows Service Installer (NSSM)
REM
REM  Installs the dashboard as a Windows service using NSSM so it starts
REM  automatically on boot and is accessible on the local network.
REM
REM  Usage (run as Administrator):
REM    install_dashboard_service.bat install   - Install and start the service
REM    install_dashboard_service.bat start     - Start the service
REM    install_dashboard_service.bat stop      - Stop the service
REM    install_dashboard_service.bat restart   - Restart the service
REM    install_dashboard_service.bat remove    - Remove the service
REM    install_dashboard_service.bat status    - Check service status
REM ============================================================================

setlocal enabledelayedexpansion

REM --- Configuration ---
set SERVICE_NAME=JobIntelligenceDashboard
set SERVICE_DISPLAY=Job Intelligence Dashboard
set SERVICE_DESC=Serves the Job Intelligence Dashboard on port 8888 for intranet access
set DASHBOARD_PORT=8888
set FIREWALL_RULE=Job Intelligence Dashboard

REM --- Determine project root (parent of scripts/) ---
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
pushd "%PROJECT_ROOT%"
set PROJECT_ROOT=%CD%
popd

REM --- Detect Python ---
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%P in ('where python') do (
        set PYTHON_PATH=%%P
        goto :found_python
    )
)
REM Fallback: check common locations
if exist "C:\Python312\python.exe" (
    set PYTHON_PATH=C:\Python312\python.exe
    goto :found_python
)
if exist "C:\Python311\python.exe" (
    set PYTHON_PATH=C:\Python311\python.exe
    goto :found_python
)
echo [ERROR] Python not found. Please install Python or add it to PATH.
exit /b 1

:found_python
echo [INFO] Python found at: %PYTHON_PATH%

REM --- Check for Administrator privileges ---
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] This script must be run as Administrator.
    echo         Right-click the script and select "Run as administrator".
    exit /b 1
)

REM --- Ensure logs directory exists ---
if not exist "%PROJECT_ROOT%\logs" (
    mkdir "%PROJECT_ROOT%\logs"
    echo [INFO] Created logs directory: %PROJECT_ROOT%\logs
)

REM --- Parse command ---
set ACTION=%~1
if "%ACTION%"=="" set ACTION=install

goto :%ACTION% 2>nul || goto :usage

REM ============================================================================
:install
REM ============================================================================
echo.
echo ============================================================
echo  Installing %SERVICE_DISPLAY% as a Windows Service
echo ============================================================

REM --- Check/download NSSM ---
call :ensure_nssm
if %ERRORLEVEL% neq 0 exit /b 1

REM --- Remove existing service if present ---
"%NSSM_PATH%" status %SERVICE_NAME% >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Existing service found. Removing it first...
    "%NSSM_PATH%" stop %SERVICE_NAME% >nul 2>&1
    timeout /t 2 /nobreak >nul
    "%NSSM_PATH%" remove %SERVICE_NAME% confirm
    echo [INFO] Old service removed.
)

REM --- Install the service ---
echo [INFO] Installing service...
"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "scripts\start_dashboard.py" "--host" "0.0.0.0" "--port" "%DASHBOARD_PORT%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install service.
    exit /b 1
)

REM --- Configure service parameters ---
echo [INFO] Configuring service parameters...
"%NSSM_PATH%" set %SERVICE_NAME% DisplayName "%SERVICE_DISPLAY%"
"%NSSM_PATH%" set %SERVICE_NAME% Description "%SERVICE_DESC%"
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%PROJECT_ROOT%"
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%PROJECT_ROOT%\logs\dashboard_service.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%PROJECT_ROOT%\logs\dashboard_service.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStdoutCreationDisposition 4
"%NSSM_PATH%" set %SERVICE_NAME% AppStderrCreationDisposition 4
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateBytes 5242880

echo [INFO] Service installed successfully.

REM --- Configure firewall ---
call :setup_firewall

REM --- Start the service ---
echo [INFO] Starting the service...
"%NSSM_PATH%" start %SERVICE_NAME%
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Service may have failed to start. Check logs at:
    echo           %PROJECT_ROOT%\logs\dashboard_service.log
) else (
    echo [INFO] Service started successfully.
)

REM --- Show access info ---
call :show_access_info
goto :eof

REM ============================================================================
:start
REM ============================================================================
call :ensure_nssm
echo [INFO] Starting %SERVICE_NAME%...
"%NSSM_PATH%" start %SERVICE_NAME%
call :show_access_info
goto :eof

REM ============================================================================
:stop
REM ============================================================================
call :ensure_nssm
echo [INFO] Stopping %SERVICE_NAME%...
"%NSSM_PATH%" stop %SERVICE_NAME%
echo [INFO] Service stopped.
goto :eof

REM ============================================================================
:restart
REM ============================================================================
call :ensure_nssm
echo [INFO] Restarting %SERVICE_NAME%...
"%NSSM_PATH%" restart %SERVICE_NAME%
call :show_access_info
goto :eof

REM ============================================================================
:remove
REM ============================================================================
call :ensure_nssm
echo [INFO] Stopping service (if running)...
"%NSSM_PATH%" stop %SERVICE_NAME% >nul 2>&1
timeout /t 2 /nobreak >nul
echo [INFO] Removing service...
"%NSSM_PATH%" remove %SERVICE_NAME% confirm
echo [INFO] Removing firewall rule...
netsh advfirewall firewall delete rule name="%FIREWALL_RULE%" >nul 2>&1
echo [INFO] Service and firewall rule removed.
goto :eof

REM ============================================================================
:status
REM ============================================================================
call :ensure_nssm
echo.
echo --- Service Status ---
"%NSSM_PATH%" status %SERVICE_NAME%
echo.
echo --- Firewall Rule ---
netsh advfirewall firewall show rule name="%FIREWALL_RULE%" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Firewall rule "%FIREWALL_RULE%" is configured.
) else (
    echo Firewall rule "%FIREWALL_RULE%" is NOT configured.
)
call :show_access_info
goto :eof

REM ============================================================================
:usage
REM ============================================================================
echo.
echo Usage: %~nx0 {install^|start^|stop^|restart^|remove^|status}
echo.
echo   install  - Install and start the service (default)
echo   start    - Start the service
echo   stop     - Stop the service
echo   restart  - Restart the service
echo   remove   - Remove the service and firewall rule
echo   status   - Show service and firewall status
echo.
goto :eof

REM ============================================================================
:ensure_nssm
REM   Checks for NSSM in PATH or local tools folder; downloads if missing.
REM ============================================================================
REM Check if nssm is already in PATH
where nssm >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%N in ('where nssm') do (
        set NSSM_PATH=%%N
        goto :nssm_found
    )
)

REM Check local tools directory
set NSSM_LOCAL=%PROJECT_ROOT%\tools\nssm.exe
if exist "%NSSM_LOCAL%" (
    set NSSM_PATH=%NSSM_LOCAL%
    goto :nssm_found
)

REM Download NSSM
echo [INFO] NSSM not found. Downloading...
if not exist "%PROJECT_ROOT%\tools" mkdir "%PROJECT_ROOT%\tools"

set NSSM_ZIP=%PROJECT_ROOT%\tools\nssm.zip
set NSSM_URL=https://nssm.cc/release/nssm-2.24.zip

echo [INFO] Downloading NSSM from %NSSM_URL% ...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%NSSM_URL%' -OutFile '%NSSM_ZIP%'"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to download NSSM. Please download manually from https://nssm.cc
    echo         Place nssm.exe in: %PROJECT_ROOT%\tools\
    exit /b 1
)

echo [INFO] Extracting NSSM...
powershell -Command "Expand-Archive -Path '%NSSM_ZIP%' -DestinationPath '%PROJECT_ROOT%\tools\nssm_temp' -Force"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to extract NSSM.
    exit /b 1
)

REM Copy the 64-bit executable
copy "%PROJECT_ROOT%\tools\nssm_temp\nssm-2.24\win64\nssm.exe" "%NSSM_LOCAL%" >nul
if %ERRORLEVEL% neq 0 (
    REM Fallback to 32-bit
    copy "%PROJECT_ROOT%\tools\nssm_temp\nssm-2.24\win32\nssm.exe" "%NSSM_LOCAL%" >nul
)

REM Clean up
del "%NSSM_ZIP%" >nul 2>&1
rmdir /s /q "%PROJECT_ROOT%\tools\nssm_temp" >nul 2>&1

if exist "%NSSM_LOCAL%" (
    set NSSM_PATH=%NSSM_LOCAL%
    echo [INFO] NSSM installed to: %NSSM_LOCAL%
    goto :nssm_found
) else (
    echo [ERROR] Failed to install NSSM.
    exit /b 1
)

:nssm_found
echo [INFO] NSSM found at: %NSSM_PATH%
exit /b 0

REM ============================================================================
:setup_firewall
REM   Creates an inbound firewall rule for the dashboard port.
REM ============================================================================
echo [INFO] Configuring Windows Firewall...

REM Remove existing rule if present
netsh advfirewall firewall delete rule name="%FIREWALL_RULE%" >nul 2>&1

REM Create new inbound TCP rule
netsh advfirewall firewall add rule name="%FIREWALL_RULE%" dir=in action=allow protocol=TCP localport=%DASHBOARD_PORT% profile=domain,private
if %ERRORLEVEL% equ 0 (
    echo [INFO] Firewall rule created: Allow TCP port %DASHBOARD_PORT% (domain/private networks)
) else (
    echo [WARNING] Failed to create firewall rule. You may need to open port %DASHBOARD_PORT% manually.
)
exit /b 0

REM ============================================================================
:show_access_info
REM   Displays LAN IP addresses and access URL.
REM ============================================================================
echo.
echo ============================================================
echo  Dashboard Access Information
echo ============================================================
echo.
echo  Local:   http://localhost:%DASHBOARD_PORT%
echo.
echo  LAN IPs (use from other devices on your network):

REM Get IPv4 addresses that are not loopback
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%A
    REM Trim leading space
    set IP=!IP:~1!
    echo           http://!IP!:%DASHBOARD_PORT%
)

echo.
echo  Logs:    %PROJECT_ROOT%\logs\dashboard_service.log
echo ============================================================
echo.
exit /b 0
