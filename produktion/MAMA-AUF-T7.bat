@echo off
chcp 65001 >nul
rem ============================================================
rem  MAMAS BILDER & DATEN -> T7 (E:) — SICHERES 3-PHASEN-SKRIPT
rem  (~300 GB: je nach Platte 1–4 Stunden, laufen lassen!)
rem
rem  WICHTIG: Dieses Skript LOESCHT NICHTS. Es kopiert und prueft.
rem  Quellen loeschst DU erst am Ende von Hand, nach Kontrolle.
rem
rem  VORHER ANPASSEN: Die QUELLEN unten (Zeilen mit "set SRC")
rem  auf die echten Ordner setzen, wo Mamas Sachen liegen.
rem ============================================================
setlocal

set ZIEL=E:\MAMA-ARCHIV
set LOGDIR=E:\MAMA-ARCHIV\_logs

rem --- HIER DEINE QUELLEN EINTRAGEN (Beispiele anpassen!) ---
set SRC1=C:\Users\%USERNAME%\Pictures\Mama
set SRC2=G:\Mama
set SRC3=%OneDrive%\Bilder\Mama

if not exist E:\ (
    echo [FEHLER] T7 nicht angeschlossen? Laufwerk E: fehlt. Abbruch.
    pause & exit /b 1
)
mkdir "%ZIEL%" 2>nul
mkdir "%LOGDIR%" 2>nul

echo.
echo ================= PHASE 1: KOPIEREN =================
for %%N in (1 2 3) do call :copyone %%N
goto verify

:copyone
setlocal
call set SRC=%%SRC%1%%
if not exist "%SRC%" (
    echo [Quelle %1] "%SRC%" existiert nicht - uebersprungen.
    endlocal & goto :eof
)
echo [Quelle %1] Kopiere "%SRC%" -> "%ZIEL%\Quelle%1" ...
robocopy "%SRC%" "%ZIEL%\Quelle%1" /E /COPY:DAT /DCOPY:T /R:2 /W:2 /NP /TEE /LOG+:"%LOGDIR%\kopie_quelle%1.log"
endlocal & goto :eof

:verify
echo.
echo ================= PHASE 2: PRUEFEN ==================
echo (Listet Unterschiede. "0 Dateien" bei Copied/Extras/Mismatch = perfekt.)
for %%N in (1 2 3) do call :checkone %%N

echo.
echo ================= PHASE 3: DEINE AUFGABE =============
echo  1. Oeffne E:\MAMA-ARCHIV und STICHPROBEN pruefen:
echo     Bilder oeffnen sich? Videos spielen ab?
echo  2. Pruefe die Logs in E:\MAMA-ARCHIV\_logs auf FEHLER.
echo  3. ERST DANN die Quell-Ordner von Hand loeschen
echo     (und den Papierkorb / OneDrive-Papierkorb leeren).
echo  4. EMPFEHLUNG: Diese eine T7-Kopie ist KEIN Backup!
echo     Mindestens 1 zweite Platte an einem anderen Ort.
echo ======================================================
pause
exit /b 0

:checkone
setlocal
call set SRC=%%SRC%1%%
if not exist "%SRC%" ( endlocal & goto :eof )
echo [Pruefung %1] Vergleiche "%SRC%" mit Kopie ...
robocopy "%SRC%" "%ZIEL%\Quelle%1" /E /L /NJH /NP /LOG+:"%LOGDIR%\pruefung_quelle%1.log"
endlocal & goto :eof
