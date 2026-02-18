@echo off
REM 1) (Optional) Update portable ClamAV DB if you bundled a clamav\ folder
IF EXIST "%~dp0clamav\freshclam.exe" (
  echo [*] Updating bundled ClamAV database...
  "%~dp0clamav\freshclam.exe" --quiet
) ELSE (
  echo [*] No portable ClamAV found. Windows Defender will be used for AV.
)

REM 2) Launch the scanner with user args
echo [*] Running PyMalScan.exe (Windows) %*
"%~dp0PyMalScan.exe" %*
