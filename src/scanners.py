import os
import subprocess
import platform
from typing import List, Dict, Tuple, Optional
from aegisorch.utils import resource_path

# ClamAV
try:
    import pyclamd
    ClamdUnixSocket = pyclamd.ClamdUnixSocket
    ClamdNetworkSocket = pyclamd.ClamdNetworkSocket
    PyClamdConnectionError = pyclamd.ConnectionError
except ImportError:
    pyclamd = None
    ClamdUnixSocket = None
    ClamdNetworkSocket = None
    PyClamdConnectionError = Exception

# YARA
try:
    import yara
except ImportError:
    yara = None

def scan_with_clamav(paths: List[str], host: Optional[str] = None, port: Optional[int] = None, sock: Optional[str] = None) -> int:
    found = 0

    # 1) Try clamd via pyclamd
    if ClamdUnixSocket and ClamdNetworkSocket:
        try:
            if sock:
                cd = ClamdUnixSocket(sock)
            else:
                cd = ClamdNetworkSocket(host or '127.0.0.1', port or 3310)
            cd.ping()
            print("[*] ClamAV deep-scan via clamd...")

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
                            print(f"[!] ClamAV DETECTION: {p} -> {name}")
                            found += 1
            if found == 0:
                print("[*] No ClamAV detections via clamd.")
            return found
        except (OSError, PyClamdConnectionError) as e:
            print(f"[!] Could not connect to clamd: {e}")
            print("[*] Falling back to clamscan CLI...")
    else:
        print("[!] pyclamd not installed; falling back to clamscan CLI...")

    # 2) Fallback: clamscan CLI
    print("[*] ClamAV fallback via clamscan CLI...")
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
            out = proc.stdout.strip() if proc.stdout else ""
            if "FOUND" in out:
                parts = out.split()
                name = parts[-2] if len(parts) >= 2 else "UNKNOWN"
                print(f"[!] ClamAV CLI DETECTION: {fp} -> {name}")
                found += 1
        except OSError:
            print("[!] clamscan not available; skipping ClamAV checks")
            break

    if found == 0:
        print("[*] No ClamAV detections via clamscan.")
    return found

def scan_yara(paths: List[str], rules_path: str) -> int:
    if not yara:
        print("[!] yara-python not installed; skipping YARA scan.")
        return 0

    fps = []
    # If the user provided path exists (rel or abs), use it. otherwise try bundled.
    if os.path.exists(rules_path):
        rp = rules_path
    else:
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

    try:
        if len(fps) > 1:
            rules = yara.compile(filepaths={os.path.basename(f): f for f in fps})
        else:
            rules = yara.compile(filepath=fps[0])
    except yara.Error as e:
        print(f"[!] Failed to compile YARA rules: {e}")
        return 0

    print(f"[*] YARA scan: loaded {len(fps)} rule(s); scanning {len(paths)} targets...")
    found = 0
    for fp in paths:
        if not os.path.isfile(fp):
            continue
        try:
            matches = rules.match(fp)
        except yara.Error:
            continue
        for m in matches:
            print(f"[!] YARA MATCH: {fp} -> {m.rule}")
            found += 1

    if found == 0:
        print("[*] No YARA matches found.")
    return found

def scan_with_defender(paths: List[str]) -> int:
    mp = os.path.join(
        os.getenv("ProgramFiles", r"C:\Program Files"),
        "Windows Defender", "MpCmdRun.exe"
    )
    found = 0
    print("[*] Scanning with Windows Defender...")
    if not os.path.exists(mp):
        # fallback for different install locations?
        print(f"[!] Windows Defender binary not found at {mp}")
        return 0

    for fp in paths:
        if not os.path.isfile(fp):
            continue
        cp = subprocess.run(
            [mp, "-Scan", "-ScanType", "3", "-File", fp],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        out = cp.stdout or ""
        if "Threat" in out:
            # simple parse attempt
            try:
                name = out.split("Threat")[1].split()[0]
            except IndexError:
                name = "Unknown Threat"
            print(f"[!] DEFENDER DETECTION: {fp} -> {name}")
            found += 1

    if not found:
        print("[*] No Defender detections found.")
    return found
