@echo off
REM ============================================================================
REM  Job Intelligence Dashboard - Task Scheduler Installer (No NSSM needed)
REM
REM  A simpler alternative that uses Windows Task Scheduler to run the
REM  dashboard at system startup. No third-party tools required.
REM
REM  Usage (run as Administrator):
REM    install_dashboard_task.bat install   - Create the scheduled task
REM    install_dashboard_task.bat remove    - Remove the scheduled task
REM    install_dashboard_task.bat start     - Run the task now
REM    install_dashboard_task.bat stop      - Stop the running dashboard
REM    install_dashboard_task.bat status    - Check task status
REM ============================================================================

setlocal enabledelayedexpansion

REM --- Configuration ---
set TASK_NAME=JobIntelligenceDashboard
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
echo  Installing %TASK_NAME% as a Scheduled Task
echo ============================================================

REM --- Remove existing task if present ---
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Existing task found. Removing it first...
    REM Stop any running instance
    taskkill /f /fi "WINDOWTITLE eq %TASK_NAME%" >nul 2>&1
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
    echo [INFO] Old task removed.
)

REM --- Create a launcher script that the task will execute ---
REM   This wrapper ensures proper working directory and log redirection.
set LAUNCHER=%PROJECT_ROOT%\scripts\run_dashboard_task.bat
echo @echo off > "%LAUNCHER%"
echo cd /d "%PROJECT_ROOT%" >> "%LAUNCHER%"
echo "%PYTHON_PATH%" scripts\start_dashboard.py --host 0.0.0.0 --port %DASHBOARD_PORT% ^>^> "%PROJECT_ROOT%\logs\dashboard_service.log" 2^>^&1 >> "%LAUNCHER%"
echo [INFO] Created launcher script: %LAUNCHER%

REM --- Create the scheduled task ---
REM   /sc onstart  - trigger at system startup
REM   /ru SYSTEM   - run as SYSTEM account (runs without user login)
REM   /rl HIGHEST  - run with highest privileges
echo [INFO] Creating scheduled task...
schtasks /create /tn "%TASK_NAME%" /tr "\"%LAUNCHER%\"" /sc onstart /ru SYSTEM /rl HIGHEST /f
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to create scheduled task.
    echo [INFO]  Trying alternative: run as current user...
    REM Fallback: run as the current user (requires user to be logged in)
    schtasks /create /tn "%TASK_NAME%" /tr "\"%LAUNCHER%\"" /sc onlogon /rl HIGHEST /f
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create scheduled task with both methods.
        exit /b 1
    )
    echo [INFO] Task created with ONLOGON trigger (requires user login).
)

echo [INFO] Scheduled task created successfully.

REM --- Configure firewall ---
call :setup_firewall

REM --- Start the task now ---
echo [INFO] Starting the dashboard now...
schtasks /run /tn "%TASK_NAME%"
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Could not start task automatically.
    echo           You can start it manually: schtasks /run /tn "%TASK_NAME%"
) else (
    echo [INFO] Dashboard started.
)

REM --- Show access info ---
call :show_access_info
goto :eof

REM ============================================================================
:start
REM ============================================================================
echo [INFO] Starting %TASK_NAME%...
schtasks /run /tn "%TASK_NAME%"
if %ERRORLEVEL% equ 0 (
    call :show_access_info
) else (
    echo [ERROR] Failed to start task. Is it installed?
)
goto :eof

REM ============================================================================
:stop
REM ============================================================================
echo [INFO] Stopping %TASK_NAME%...

REM Find and kill the Python process running start_dashboard.py
for /f "tokens=2" %%P in ('wmic process where "CommandLine like '%%start_dashboard%%'" get ProcessId /format:list 2^>nul ^| findstr ProcessId') do (
    set PID=%%P
    REM Trim carriage return
    set PID=!PID: =!
    if defined PID (
        echo [INFO] Killing process PID: !PID!
        taskkill /f /pid !PID! >nul 2>&1
    )
)

REM Also try ending the task via schtasks
schtasks /end /tn "%TASK_NAME%" >nul 2>&1

echo [INFO] Dashboard stopped.
goto :eof

REM ============================================================================
:remove
REM ============================================================================
echo [INFO] Stopping dashboard (if running)...
call :stop

echo [INFO] Removing scheduled task...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Scheduled task removed.
) else (
    echo [INFO] No scheduled task found to remove.
)

echo [INFO] Removing firewall rule...
netsh advfirewall firewall delete rule name="%FIREWALL_RULE%" >nul 2>&1

REM Clean up launcher script
if exist "%PROJECT_ROOT%\scripts\run_dashboard_task.bat" (
    del "%PROJECT_ROOT%\scripts\run_dashboard_task.bat"
    echo [INFO] Launcher script removed.
)

echo [INFO] Cleanup complete.
goto :eof

REM ============================================================================
:status
REM ============================================================================
echo.
echo --- Scheduled Task Status ---
schtasks /query /tn "%TASK_NAME%" /v /fo list 2>nul
if %ERRORLEVEL% neq 0 (
    echo Task "%TASK_NAME%" is NOT installed.
)

echo.
echo --- Dashboard Process ---
wmic process where "CommandLine like '%%start_dashboard%%'" get ProcessId,CommandLine /format:list 2>nul | findstr /v "^$"
if %ERRORLEVEL% neq 0 (
    echo No running dashboard process found.
)

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
echo Usage: %~nx0 {install^|start^|stop^|remove^|status}
echo.
echo   install  - Create the scheduled task and start dashboard (default)
echo   start    - Run the dashboard task now
echo   stop     - Stop the running dashboard
echo   remove   - Remove the task, firewall rule, and launcher
echo   status   - Show task and process status
echo.
goto :eof

REM ============================================================================
:setup_firewall
REM   Creates an inbound firewall rule for the dashboard port.
REM ============================================================================
echo [INFO] Configuring Windows Firewall...

REM Remove existing rule if present
netsh advfirewall firewall delete rule name="%FIREWALL_RULE%" >nul 2>&1

REM Create new inbound TCP rule for domain and private networks
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
