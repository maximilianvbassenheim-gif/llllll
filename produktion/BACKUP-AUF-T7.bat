@echo off
chcp 65001 >nul
rem ============================================================
rem  IMPERIUM-BACKUP -> T7 (E:\BACKUP)
rem  Sichert: Projekt-Code, PRODUKTION-Ordner und deine
rem  KI-/CLI-Werkzeuge ("Halleluja Core" & Co).
rem  Nur KOPIEREN - es wird nichts geloescht.
rem  Immer wieder ausfuehrbar (kopiert nur Neues/Geaendertes).
rem ============================================================
setlocal
set ZIEL=E:\BACKUP
set STAMP=%DATE:~-4%-%DATE:~-7,2%-%DATE:~-10,2%

if not exist E:\ (
    echo [FEHLER] T7 nicht angeschlossen? Laufwerk E: fehlt. Abbruch.
    pause & exit /b 1
)
mkdir "%ZIEL%" 2>nul

rem --- HIER DEINE ORDNER EINTRAGEN (Beispiele anpassen!) ---
rem Q1: Wo dein GitHub-Projekt lokal liegt (falls geklont)
set Q1=C:\Users\%USERNAME%\Projekte\llllll
rem Q2: Deine lokale PRODUKTION (falls schon angelegt)
set Q2=C:\PRODUKTION
rem Q3: Deine KI-/CLI-Tools (Halleluja Core, LLM-Setups usw.)
set Q3=C:\Users\%USERNAME%\halleluja-core

echo.
echo ============ IMPERIUM-BACKUP %STAMP% ============
for %%N in (1 2 3) do call :backupone %%N
echo.
echo  Fertig. Kontrolle: E:\BACKUP oeffnen und Stichproben machen.
echo  Tipp: Das GitHub-Repo ist zusaetzlich online gesichert unter
echo  https://github.com/maximilianvbassenheim-gif/llllll
echo  und als ZIP in deinem Google Drive (PRODUKTION-Ordner).
echo ====================================================
pause
exit /b 0

:backupone
setlocal
call set SRC=%%Q%1%%
if not exist "%SRC%" (
    echo [Q%1] "%SRC%" existiert nicht - uebersprungen. (Pfad oben anpassen!)
    endlocal & goto :eof
)
for %%I in ("%SRC%") do set NAME=%%~nxI
echo [Q%1] Sichere "%SRC%" -> "%ZIEL%\%NAME%" ...
robocopy "%SRC%" "%ZIEL%\%NAME%" /E /COPY:DAT /DCOPY:T /XD node_modules .git __pycache__ /R:2 /W:2 /NP /TEE /LOG+:"%ZIEL%\_backup_%NAME%.log"
endlocal & goto :eof
