@echo off
chcp 65001 >nul
rem ============================================================
rem  PRODUKTION-SETUP (ZENTRAL)
rem  Zielbild:
rem  1) EINE zentrale Datenbasis auf T7 (E:\PRODUKTION)
rem  2) Grosse/statische Bereiche auf T7 (06/07/08 + Archiv)
rem  3) PC-uebergreifende Arbeitsordner in OneDrive
rem     (mit "Dateien bei Bedarf" aktivieren)
rem ============================================================
setlocal EnableDelayedExpansion

set T7_ROOT=E:\PRODUKTION
set T7_FOLDERS=00-START-HIER 01-MARKE 02-CONTENT 03-VERKAUF 04-SETUP 05-ROUTINE 06-ROHMATERIAL 07-AUDIO 08-FERTIG Archiv Eingang
set ONEDRIVE_FOLDERS=00-START-HIER 01-MARKE 02-CONTENT 03-VERKAUF 04-SETUP 05-ROUTINE

echo.
echo  ============================================
echo   PRODUKTION-Setup (zentral auf T7)
echo  ============================================
echo.

if not exist E:\ (
    echo  [FEHLER] T7 nicht angeschlossen. E: fehlt.
    echo  Bitte T7 anschliessen und erneut starten.
    pause
    exit /b 1
)

echo  [T7] Lege zentrale Struktur unter %T7_ROOT% an ...
for %%F in (%T7_FOLDERS%) do (
    if not exist "%T7_ROOT%\%%F" mkdir "%T7_ROOT%\%%F"
)
echo  [T7] fertig.

if defined OneDrive (
    set OD_ROOT=%OneDrive%\PRODUKTION
    echo  [OneDrive] gefunden: %OneDrive%
    echo  [OneDrive] Lege PC-uebergreifende Arbeitsordner an ...
    for %%F in (%ONEDRIVE_FOLDERS%) do (
        if not exist "!OD_ROOT!\%%F" mkdir "!OD_ROOT!\%%F"
    )
    echo  [OneDrive] fertig.
    echo.
    echo  WICHTIG: In OneDrive "Dateien bei Bedarf" aktivieren:
    echo          OneDrive-Einstellungen ^> Synchronisierung und Sicherung
    echo          ^> Erweiterte Einstellungen ^> Dateien bei Bedarf EIN.
) else (
    echo  [OneDrive] nicht eingerichtet - uebersprungen.
)

echo.
echo  ============================================
echo   REGELN (SICHER):
echo   1) Duplikate nur EINMAL zentral auf T7 halten.
echo   2) 06-ROHMATERIAL, 07-AUDIO, 08-FERTIG, Archiv nur auf T7.
echo   3) Vor jedem Umzug IMMER zuerst SORTIEREN.bat starten.
echo   4) Nie blind loeschen - erst Plan + Kopie + Stichprobe.
echo  ============================================
echo.
pause
