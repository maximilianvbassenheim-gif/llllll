@echo off
chcp 65001 >nul
rem ============================================================
rem  SHAKKER KIDS / PRODUKTION — Ordnerstruktur-Setup
rem  Doppelklick genügt. Legt die PRODUKTION-Struktur an auf:
rem  E:\ (Hauptplatte), C:\, G:\ (falls vorhanden) und OneDrive.
rem ============================================================
setlocal EnableDelayedExpansion

set FOLDERS=00-START-HIER 01-MARKE 02-CONTENT 03-VERKAUF 04-SETUP 05-ROUTINE 06-ROHMATERIAL 07-AUDIO 08-FERTIG

echo.
echo  ============================================
echo   PRODUKTION-Struktur wird angelegt ...
echo  ============================================
echo.

for %%D in (E C G) do (
    if exist %%D:\ (
        echo  [%%D:] Laufwerk gefunden - lege %%D:\PRODUKTION an ...
        for %%F in (%FOLDERS%) do (
            if not exist "%%D:\PRODUKTION\%%F" mkdir "%%D:\PRODUKTION\%%F"
        )
        echo  [%%D:] fertig.
    ) else (
        echo  [%%D:] nicht vorhanden - uebersprungen.
    )
)

rem --- OneDrive Personal (Windows setzt die Variable automatisch) ---
if defined OneDrive (
    echo  [OneDrive] gefunden: %OneDrive%
    for %%F in (%FOLDERS%) do (
        if not exist "%OneDrive%\PRODUKTION\%%F" mkdir "%OneDrive%\PRODUKTION\%%F"
    )
    echo  [OneDrive] fertig - synchronisiert automatisch in die Cloud.
) else (
    echo  [OneDrive] nicht eingerichtet - uebersprungen.
)

echo.
echo  ============================================
echo   FERTIG! Struktur angelegt.
echo   Tipp: Grosse Dateien (Video/Audio) nach
echo   06-ROHMATERIAL, 07-AUDIO, 08-FERTIG.
echo   Die Anleitungen (Markdown-Dateien) aus dem
echo   GitHub-Ordner "produktion" hineinkopieren.
echo  ============================================
echo.
pause
