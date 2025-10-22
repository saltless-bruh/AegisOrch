#!/usr/bin/env python3
"""
PyMalScan v3.3.2 – daily integrity & immediate deep forensic scan (ClamAV + YARA)
See README.md for usage.
"""

import os
import sys
import json
import argparse
import hashlib
import platform
import subprocess
import psutil

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union
from os import PathLike

try:
    import pyclamd

    ClamdUnixSocket = pyclamd.ClamdUnixSocket
    ClamdNetworkSocket = pyclamd.ClamdNetworkSocket
    PyClamdConnectionError = pyclamd.ConnectionError
except ImportError:
    # If pyclamd is absent, bind stubs so static analysis won't complain
    pyclamd = None
    ClamdUnixSocket = None
    ClamdNetworkSocket = None
    PyClamdConnectionError = Exception


# -----------------------------------------------------------------------------
# Helper to locate bundled resources (works both in source & PyInstaller exe)
# -----------------------------------------------------------------------------
def resource_path(rel_path: Union[str, Path]) -> str:
    """
    Get absolute path to resource, whether running
    from source or from PyInstaller _MEIPASS bundle.
    """
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel_path)


# -----------------------------------------------------------------------------
# Core helpers
# -----------------------------------------------------------------------------
def compute_sha256(
        path: Union[str, bytes, PathLike[str], PathLike[bytes]],
        block_size: int = 1 << 16
) -> Optional[str]:
    """
    Compute SHA-256 of the file at `path`. Accepts str, bytes, or PathLike.
    """
    # Normalize path to str or bytes
    p = os.fspath(path)
    try:
        h = hashlib.sha256()
        with open(p, 'rb') as f:
            for chunk in iter(lambda: f.read(block_size), b''):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, IOError):
        return None


def get_system_paths() -> list:
    if platform.system() == "Linux":
        return ['/bin', '/sbin', '/usr/bin', '/usr/sbin']
    else:
        windir = os.environ.get('WINDIR', r'C:\Windows')
        return [os.path.join(windir, 'System32')]


# -----------------------------------------------------------------------------
# Daily mode: snapshot & compare
# -----------------------------------------------------------------------------
def take_snapshot(paths: list) -> dict:
    snap = {}
    for base in paths:
        for root, _, files in os.walk(base):
            for fn in files:
                fp = os.path.join(root, fn)
                h = compute_sha256(fp)
                if h:
                    snap[fp] = h
    return snap


def save_snapshot(snap: dict, path: str, paths: list) -> None:
    data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'paths': paths,
        'files': snap
    }
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[+] Snapshot saved ({len(snap)} files) → {path}")


def load_snapshot(path: str) -> tuple:
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('paths', []), data.get('files', {})


def compare_snapshot(old_files: dict, new_files: dict) -> None:
    added = [f for f in new_files if f not in old_files]
    removed = [f for f in old_files if f not in new_files]
    changed = [f for f in old_files
               if f in new_files and new_files[f] != old_files[f]]

    if not (added or removed or changed):
        print("[*] No changes since snapshot.")
        return

    if changed:
        print("[!] Modified files:")
        for f in changed:
            print("    -", f)
    if added:
        print("[!] New files:")
        for f in added:
            print("    -", f)
    if removed:
        print("[!] Removed files:")
        for f in removed:
            print("    -", f)


# -----------------------------------------------------------------------------
# Deep mode: forensic checks
# -----------------------------------------------------------------------------
def detect_hidden_processes() -> None:
    if platform.system() != "Linux":
        return
    print("[*] Hidden-PID check…")
    try:
        on_disk = {int(d) for d in os.listdir('/proc') if d.isdigit()}
        via_ps = set(psutil.pids())
        hidden = sorted(on_disk - via_ps)
        if hidden:
            print(f"[!] Hidden PIDs detected: {hidden}")
        else:
            print("    (none)")
    except (OSError, IOError):
        print("    [!] Unable to inspect /proc (need root)")


def list_listening_ports() -> None:
    print("[*] Listening ports:")
    for conn in psutil.net_connections():
        if conn.status == psutil.CONN_LISTEN:
            ip, port = conn.laddr.ip or '*', conn.laddr.port
            print(f"    - {ip}:{port}  (PID {conn.pid})")


def scan_with_clamav(paths, host=None, port=None, sock=None):
    found = 0

    # 1) Try clamd via pyclamd
    if ClamdUnixSocket and ClamdNetworkSocket:
        try:
            if sock:
                cd = ClamdUnixSocket(sock)
            else:
                cd = ClamdNetworkSocket(host or '127.0.0.1',
                                        port or 3310)
            cd.ping()
            print("[*] ClamAV deep-scan via clamd…")

            for fp in paths:
                if not os.path.isfile(fp):
                    continue
                try:
                    result = cd.scan_file(fp)
                except OSError:
                    continue
                if result:
                    for p, (status, name) in result.items():
                        if status.upper() == 'FOUND':
                            print(f"[!] ClamAV DETECTION: {p} → {name}")
                            found += 1

            if found == 0:
                print("[*] No ClamAV detections via clamd.")
            return found

        except (OSError, PyClamdConnectionError) as e:
            print(f"[!] Could not connect to clamd: {e}")
            print("[*] Falling back to clamscan CLI…")

    else:
        print("[!] pyclamd not installed; falling back to clamscan CLI…")

    # 2) Fallback: clamscan CLI
    print("[*] ClamAV fallback via clamscan CLI…")
    for fp in paths:
        if not os.path.isfile(fp):
            continue
        try:
            proc = subprocess.run(
                ['clamscan', '--no-summary', fp],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
        except OSError:
            print("[!] clamscan not available; skipping ClamAV checks")
            break

        out = proc.stdout.strip()
        if out.endswith("FOUND"):
            parts = out.split()
            name = parts[-2] if len(parts) >= 2 else "UNKNOWN"
            print(f"[!] ClamAV CLI DETECTION: {fp} → {name}")
            found += 1

    if found == 0:
        print("[*] No ClamAV detections via clamscan.")
    return found


def scan_yara(paths: list, rules_path: str) -> int:
    try:
        import yara
    except ImportError:
        print("[!] yara-python not installed; skipping YARA scan.")
        return 0

    # gather rule files
    fps = []
    rp = resource_path(rules_path)
    if os.path.isdir(rp):
        for fn in os.listdir(rp):
            if fn.lower().endswith(('.yar', '.yara')):
                fps.append(os.path.join(rp, fn))
    elif os.path.isfile(rp):
        fps.append(rp)

    if not fps:
        print(f"[!] No YARA rules found in {rules_path}")
        return 0

    # compile
    try:
        if len(fps) > 1:
            rules = yara.compile(filepaths={os.path.basename(f): f for f in fps})
        else:
            rules = yara.compile(filepath=fps[0])
    except yara.Error as e:
        print(f"[!] Failed to compile YARA rules: {e}")
        return 0

    print(f"[*] YARA scan: loaded {len(fps)} rule(s); scanning {len(paths)} targets…")
    found = 0
    for fp in paths:
        if not os.path.isfile(fp):
            continue
        try:
            matches = rules.match(fp)
        except yara.Error:
            continue
        for m in matches:
            print(f"[!] YARA MATCH: {fp} → {m.rule}")
            found += 1

    if found == 0:
        print("[*] No YARA matches found.")
    return found


def gather_all_targets() -> list:
    tg = set()

    # system binaries
    for base in get_system_paths():
        for root, _, files in os.walk(base):
            for fn in files:
                tg.add(os.path.join(root, fn))

    # running executables
    for proc in psutil.process_iter():
        try:
            exe = proc.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if exe and os.path.isfile(exe):
            tg.add(exe)

    # kernel modules (Linux)
    if platform.system() == "Linux":
        try:
            with open('/proc/modules') as modf:
                for line in modf:
                    mod = line.split()[0]
                    out, _ = subprocess.Popen(
                        ['modinfo', '-n', mod],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True
                    ).communicate()
                    path = out.strip()
                    if os.path.isfile(path):
                        tg.add(path)
        except (OSError, subprocess.SubprocessError):
            pass

    # startup entries
    if platform.system() == "Windows":
        try:
            import winreg
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                key = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(hive, key) as rk:
                    for i in range(winreg.QueryInfoKey(rk)[1]):
                        _, val, _ = winreg.EnumValue(rk, i)
                        exe = val.strip('" ').split()[0]
                        if os.path.isfile(exe):
                            tg.add(exe)
        except OSError:
            pass
    else:
        try:
            out, _ = subprocess.Popen(
                ['systemctl', 'list-unit-files', '--type=service', '--state=enabled'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            ).communicate()
            for line in out.splitlines():
                parts = line.split()
                if not parts or not parts[0].endswith('.service'):
                    continue
                svc = parts[0]
                for d in ('/etc/systemd/system', '/lib/systemd/system'):
                    pth = os.path.join(d, svc)
                    if os.path.isfile(pth):
                        tg.add(pth)
        except (OSError, subprocess.SubprocessError):
            # fallback SysV
            for fn in os.listdir('/etc/init.d'):
                pth = os.path.join('/etc/init.d', fn)
                if os.path.isfile(pth):
                    tg.add(pth)

    return list(tg)


def scan_with_defender(paths):
    # Path to Defender CLI (adjust if yours is elsewhere)
    mp = os.path.join(
        os.getenv("ProgramFiles", r"C:\Program Files"),
        "Windows Defender", "MpCmdRun.exe"
    )
    found = 0
    print("[*] Scanning with Windows Defender…")
    for fp in paths:
        if not os.path.isfile(fp):
            continue
        # Scan only this file: ScanType 3
        cp = subprocess.run(
            [mp, "-Scan", "-ScanType", "3", "-File", fp],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        out = cp.stdout or ""
        # Look for “Threat” in the output
        if "Threat" in out:
            # crude parse: grab the last quoted item
            name = out.split("Threat")[1].split()[0]
            print(f"[!] DEFENDER DETECTION: {fp} → {name}")
            found += 1

    if not found:
        print("[*] No Defender detections found.")
    return found


def immediate_deep_scan(use_clamav: bool,
                        use_yara: bool,
                        clam_host: str,
                        clam_port: int,
                        clam_socket: str,
                        yara_rules: str) -> int:
    print("[*] Starting immediate deep scan…")
    detect_hidden_processes()
    list_listening_ports()

    targets = gather_all_targets() if (use_clamav or use_yara) else []
    total = 0

    if use_clamav:
        print(f"[*] Will scan {len(targets)} files with ClamAV…")
        if platform.system() == "Windows":
            total += scan_with_defender(targets)
        else:
            total += scan_with_clamav(
                targets,
                host=clam_host,
                port=clam_port,
                sock=clam_socket
            )
    if use_yara:
        total += scan_yara(targets, yara_rules)

    if total == 0:
        print("[*] No detections found. System appears clean.")

    print("[*] Immediate deep scan complete.")
    return total


# -----------------------------------------------------------------------------
# CLI entrypoint
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(prog="PyMalScan")
    subs = parser.add_subparsers(dest='mode', required=True)

    # daily subcommand
    d = subs.add_parser('daily', help='snapshot & integrity check')
    d.add_argument('--init', action='store_true',
                   help="build a clean snapshot of system binaries")
    d.add_argument('--snapshot-file', default='snapshot.json',
                   help="path to read/write the JSON snapshot")

    # deep subcommand
    q = subs.add_parser('deep', help='immediate forensic scan (ClamAV + YARA)')
    q.add_argument('--clamav', action='store_true', help="enable ClamAV scan")
    q.add_argument('--clam-host', help="ClamAV TCP host (default 127.0.0.1)")
    q.add_argument('--clam-port', type=int, help="ClamAV TCP port (default 3310)")
    q.add_argument('--clam-socket', help="ClamAV UNIX socket path")
    q.add_argument('--yara', action='store_true', help="enable YARA scan")
    q.add_argument('--yara-rules', default='yara_rules',
                   help="bundled YARA rule file or directory")

    args = parser.parse_args()

    if args.mode == 'daily':
        paths = get_system_paths()
        if args.init:
            snap = take_snapshot(paths)
            save_snapshot(snap, args.snapshot_file, paths)
        else:
            if not os.path.exists(args.snapshot_file):
                print(f"[!] Snapshot not found: {args.snapshot_file}", file=sys.stderr)
                sys.exit(1)
            old_paths, old_files = load_snapshot(args.snapshot_file)
            if set(old_paths) != set(paths):
                print("[!] Warning: monitored paths changed since snapshot.")
            new_files = take_snapshot(paths)
            compare_snapshot(old_files, new_files)
        sys.exit(0)

    # deep mode
    # resolve rules path through resource_path()
    args.yara_rules = resource_path(args.yara_rules)
    immediate_deep_scan(
        use_clamav=args.clamav,
        use_yara=args.yara,
        clam_host=args.clam_host,
        clam_port=args.clam_port,
        clam_socket=args.clam_socket,
        yara_rules=args.yara_rules
    )
    sys.exit(0)


if __name__ == '__main__':
    main()
