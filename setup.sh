#!/usr/bin/env bash
set -e

# 1) On Debian/Ubuntu, install ClamAV if missing
if command -v apt-get &>/dev/null; then
  echo "[*] Installing ClamAV & dependencies…"
  sudo apt-get update
  sudo apt-get install -y clamav clamav-daemon
fi

# 2) Update the ClamAV database
if command -v freshclam &>/dev/null; then
  echo "[*] Updating ClamAV database…"
  sudo freshclam --quiet
fi

# 3) Launch the scanner from source
DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$DIR/AegisOrch.py"

echo "[*] Running AegisOrch (Source) -> $*"
exec python3 "$SCRIPT" "$@"
