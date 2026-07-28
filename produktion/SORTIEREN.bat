@echo off
chcp 65001 >nul
rem ============================================================
rem  SORTIEREN.bat
rem  Erstellt NUR einen Sortier-/Kopierplan. Es wird NICHT geloescht
rem  und NICHT kopiert.
rem ============================================================
setlocal EnableDelayedExpansion

if not exist E:\ (
    echo [FEHLER] T7 nicht angeschlossen. E: fehlt.
    pause
    exit /b 1
)

set T7_ROOT=E:\PRODUKTION
set PLAN_ROOT=%T7_ROOT%\_SORTIEREN

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmmss"') do set STAMP=%%I
set PLAN_DIR=%PLAN_ROOT%\%STAMP%

mkdir "%PLAN_DIR%" 2>nul

set SRC1=C:\PRODUKTION
set SRC2=G:\PRODUKTION
set SRC3=%OneDrive%\PRODUKTION

echo.
echo ===========================================================
echo  SORTIER-PLAN WIRD ERSTELLT
echo  Ziel zentral: %T7_ROOT%
echo  Planordner : %PLAN_DIR%
echo ===========================================================
echo.

echo [1/4] Quellen pruefen und grob zusammenfassen ...
(
    echo Quelle;Pfad;Dateien;Groesse_Bytes;Groesse_GB
) > "%PLAN_DIR%\quellen_uebersicht.csv"

for %%N in (1 2 3) do call :summarize %%N

echo [2/4] Duplikat-Analyse (nach relativen Pfaden) ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$sources=@();" ^
  "if(Test-Path $env:SRC1){$sources += @{Name='SRC1_C';Path=$env:SRC1}};" ^
  "if(Test-Path $env:SRC2){$sources += @{Name='SRC2_G';Path=$env:SRC2}};" ^
  "if(Test-Path $env:SRC3){$sources += @{Name='SRC3_OneDrive';Path=$env:SRC3}};" ^
  "if(Test-Path $env:T7_ROOT){$sources += @{Name='T7';Path=$env:T7_ROOT}};" ^
  "$all=@();" ^
  "foreach($s in $sources){" ^
  "  Get-ChildItem -LiteralPath $s.Path -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {" ^
  "    $rel=$_.FullName.Substring($s.Path.Length).TrimStart('\\');" ^
  "    $all += [pscustomobject]@{Source=$s.Name;RelativePath=$rel;Length=$_.Length;LastWriteTimeUtc=$_.LastWriteTimeUtc;FullName=$_.FullName}" ^
  "  }" ^
  "};" ^
  "$dupByPath=$all | Group-Object RelativePath | Where-Object {$_.Count -gt 1};" ^
  "$rows=@();" ^
  "foreach($g in $dupByPath){ foreach($i in $g.Group){ $rows += [pscustomobject]@{RelativePath=$i.RelativePath;Source=$i.Source;Length=$i.Length;LastWriteTimeUtc=$i.LastWriteTimeUtc;FullName=$i.FullName} } }" ^
  "$rows | Sort-Object RelativePath,Source | Export-Csv -Path (Join-Path $env:PLAN_DIR 'duplikate_nach_pfad.csv') -NoTypeInformation -Encoding UTF8;" ^
  "$dupsByNameSize = $all | Group-Object @{Expression={$_.Length}}, @{Expression={[System.IO.Path]::GetFileName($_.RelativePath)}} | Where-Object {$_.Count -gt 1};" ^
  "$rows2=@();" ^
  "foreach($g in $dupsByNameSize){ foreach($i in $g.Group){ $rows2 += [pscustomobject]@{FileName=[System.IO.Path]::GetFileName($i.RelativePath);Length=$i.Length;Source=$i.Source;RelativePath=$i.RelativePath;FullName=$i.FullName} } }" ^
  "$rows2 | Sort-Object FileName,Length,Source | Export-Csv -Path (Join-Path $env:PLAN_DIR 'duplikate_name_groesse.csv') -NoTypeInformation -Encoding UTF8;" ^
  "'Duplikat-Dateien nach relativem Pfad: ' + ($dupByPath | Measure-Object).Count | Out-File -FilePath (Join-Path $env:PLAN_DIR 'summary.txt') -Encoding UTF8;" ^
  "'Duplikat-Gruppen nach Name+Groesse: ' + ($dupsByNameSize | Measure-Object).Count | Add-Content -Path (Join-Path $env:PLAN_DIR 'summary.txt');"
if errorlevel 1 (
    echo [WARN] Duplikat-Analyse hatte Probleme. Pruefe trotzdem die erzeugten Dateien.
)

echo [3/4] Kopierplan (nur Simulation mit ROBOCOPY /L) ...
for %%N in (1 2 3) do call :plan_copy %%N

echo [4/4] Abschluss-Hinweise schreiben ...
(
  echo REIHENFOLGE (SICHER):
  echo 1. quellen_uebersicht.csv + summary.txt lesen.
  echo 2. duplikate_nach_pfad.csv und duplikate_name_groesse.csv pruefen.
  echo 3. kopierplan_quelle*.log pruefen (was wuerde kopiert).
  echo 4. Erst danach echten Kopiervorgang starten.
  echo 5. NIE blind loeschen: erst Kopie + Stichprobe + dann manuell aufraeumen.
  echo.
  echo ZIELBILD:
  echo - Duplikate nur EINMAL zentral auf T7.
  echo - 06-ROHMATERIAL, 07-AUDIO, 08-FERTIG, Archiv bleiben auf T7.
  echo - PC-uebergreifende Arbeitsordner in OneDrive mit Dateien bei Bedarf.
) > "%PLAN_DIR%\ANLEITUNG.txt"

echo.
echo ===========================================================
echo FERTIG. Plan erzeugt unter:
echo %PLAN_DIR%
echo.
echo Jetzt erst pruefen, dann kopieren. Nie blind loeschen.
echo ===========================================================
echo.
pause
exit /b 0

:summarize
setlocal
call set SRC=%%SRC%1%%
if not defined SRC (
    endlocal & goto :eof
)
if not exist "%SRC%" (
    echo [Quelle %1] fehlt: "%SRC%"
    endlocal & goto :eof
)
echo [Quelle %1] %SRC%
for /f "usebackq delims=" %%L in (`powershell -NoProfile -Command "$p='%SRC%'; $files=Get-ChildItem -LiteralPath $p -Recurse -File -ErrorAction SilentlyContinue; $count=($files|Measure-Object).Count; $bytes=($files|Measure-Object -Property Length -Sum).Sum; if($null -eq $bytes){$bytes=0}; $gb=[math]::Round($bytes/1GB,2); Write-Output ('%1;'+$p+';'+$count+';'+$bytes+';'+$gb)"`) do (
    >> "%PLAN_DIR%\quellen_uebersicht.csv" echo %%L
)
endlocal & goto :eof

:plan_copy
setlocal
call set SRC=%%SRC%1%%
if not defined SRC (
    endlocal & goto :eof
)
if not exist "%SRC%" (
    echo [Quelle %1] fehlt: "%SRC%" - uebersprungen.
    endlocal & goto :eof
)
echo [Quelle %1] Simuliere Kopie "%SRC%" -> "%T7_ROOT%"
robocopy "%SRC%" "%T7_ROOT%" /E /L /COPY:DAT /DCOPY:T /R:0 /W:0 /NP /LOG:"%PLAN_DIR%\kopierplan_quelle%1.log" >nul
endlocal & goto :eof
