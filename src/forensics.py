import os
import psutil
import platform
import subprocess
from typing import List, Set
from aegisorch.utils import get_system_paths

def gather_all_targets() -> List[str]:
    tg: Set[str] = set()

    # System binaries
    for base in get_system_paths():
        if os.path.isdir(base):
            for root, _, files in os.walk(base):
                for fn in files:
                    tg.add(os.path.join(root, fn))

    # Running executables
    for proc in psutil.process_iter(['exe']):
        try:
            exe = proc.info.get('exe')
            if exe and os.path.isfile(exe):
                tg.add(exe)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Kernel modules (Linux)
    if platform.system() == "Linux":
        try:
            if os.path.exists('/proc/modules'):
                with open('/proc/modules') as modf:
                    for line in modf:
                        mod = line.split()[0]
                        try:
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
        except OSError:
            pass

    # Startup entries
    # (Simplified for brevity, can expand later)
    # Check systemd services
    if platform.system() == "Linux":
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
                # Check common locations
                for d in ('/etc/systemd/system', '/lib/systemd/system', '/usr/lib/systemd/system'):
                    pth = os.path.join(d, svc)
                    if os.path.isfile(pth):
                        tg.add(pth)
        except (OSError, subprocess.SubprocessError):
            pass

    return list(tg)

def detect_hidden_processes() -> None:
    if platform.system() != "Linux":
        return
    print("[*] Checking for hidden processes (PID mismatch)...")
    try:
        if not os.path.exists('/proc'):
            return
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
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == psutil.CONN_LISTEN:
            ip, port = conn.laddr.ip or '*', conn.laddr.port
            print(f"    - {ip}:{port}  (PID {conn.pid})")
