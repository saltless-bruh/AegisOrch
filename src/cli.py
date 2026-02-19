import argparse
import sys
import os
import platform
from typing import List

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
except ImportError:
    console = None
    Table = None

from aegisorch.utils import get_system_paths, resource_path
from aegisorch.snapshot import take_snapshot, save_snapshot, load_snapshot, compare_snapshot
from aegisorch.scanners import scan_with_clamav, scan_yara, scan_with_defender
from aegisorch.forensics import gather_all_targets, detect_hidden_processes, list_listening_ports
from aegisorch.analysis import analyze_file_static

def print_rich(msg, style="bold white"):
    if console:
        console.print(msg, style=style)
    else:
        print(msg)

def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def main():
    parser = argparse.ArgumentParser(prog="AegisOrch")
    subs = parser.add_subparsers(dest='mode', required=True)

    # daily subcommand
    d = subs.add_parser('daily', help='snapshot & integrity check')
    d.add_argument('--init', action='store_true', help="build a clean snapshot of system binaries")
    d.add_argument('--snapshot-file', default='snapshot.json', help="path to read/write the JSON snapshot")

    # deep subcommand
    q = subs.add_parser('deep', help='immediate forensic scan (ClamAV + YARA)')
    q.add_argument('--clamav', action='store_true', help="enable ClamAV scan")
    q.add_argument('--clam-host', help="ClamAV TCP host (default 127.0.0.1)")
    q.add_argument('--clam-port', type=int, help="ClamAV TCP port (default 3310)")
    q.add_argument('--clam-socket', help="ClamAV UNIX socket path")
    q.add_argument('--yara', action='store_true', help="enable YARA scan")
    q.add_argument('--yara-rules', default='rules', help="bundled YARA rule file or directory")
    q.add_argument('--analyze', action='store_true', help="[New] Perform static analysis on suspicious files (high entropy/PE)")

    args = parser.parse_args()

    if args.mode == 'daily':
        print_rich("[*] Daily Integrity Check Mode", style="bold cyan")
        paths = get_system_paths()
        if args.init:
            print_rich("[*] Initializing snapshot...", style="yellow")
            snap = take_snapshot(paths)
            save_snapshot(snap, args.snapshot_file, paths)
            print_rich(f"[+] Snapshot saved to {args.snapshot_file}", style="green")
        else:
            if not os.path.exists(args.snapshot_file):
                print_rich(f"[!] Snapshot not found: {args.snapshot_file}", style="bold red")
                sys.exit(1)
            
            print_rich("[*] Loading snapshot...", style="blue")
            old_paths, old_files = load_snapshot(args.snapshot_file)
            if set(old_paths) != set(paths):
                print_rich("[!] Warning: monitored paths changed since snapshot.", style="bold orange1")
            
            print_rich("[*] Comparing current state...", style="blue")
            new_files = take_snapshot(paths)
            diff = compare_snapshot(old_files, new_files)
            
            if not (diff['added'] or diff['removed'] or diff['changed']):
                print_rich("[+] System Integrity Verified: No changes detected.", style="bold green")
            else:
                if diff['changed']:
                    print_rich("[!] Modified Files:", style="bold red")
                    for f in diff['changed']:
                        print_rich(f"    - {f}", style="red")
                if diff['added']:
                    print_rich("[!] New Files:", style="bold yellow")
                    for f in diff['added']:
                        print_rich(f"    - {f}", style="yellow")
                if diff['removed']:
                    print_rich("[!] Removed Files:", style="bold white")
                    for f in diff['removed']:
                        print_rich(f"    - {f}", style="white")

        sys.exit(0)

    # deep mode
    if args.mode == 'deep':
        print_rich("[*] Starting Deep Forensic Scan...", style="bold magenta")
        detect_hidden_processes()
        list_listening_ports()

        use_engines = args.clamav or args.yara or args.analyze
        targets = gather_all_targets() if use_engines else []
        total_detections = 0

        if args.clamav:
            print_rich(f"[*] Scanning {len(targets)} targets with ClamAV...", style="cyan")
            if platform.system() == "Windows":
                 total_detections += scan_with_defender(targets)
            else:
                 total_detections += scan_with_clamav(targets, host=args.clam_host, port=args.clam_port, sock=args.clam_socket)

        if args.yara:
            print_rich(f"[*] Scanning {len(targets)} targets with YARA...", style="cyan")
            total_detections += scan_yara(targets, args.yara_rules)
            
        if args.analyze:
            print_rich(f"[*] performing Static Analysis on targets...", style="cyan")
            
            targets_to_analyze = [t for t in targets if os.path.isfile(t)]
            suspicious_files = []

            for t in targets_to_analyze:
                res = analyze_file_static(t)
                if res['entropy'] > 7.0:
                    suspicious_files.append((t, res))

            if suspicious_files:
                if console and Table:
                    table = Table(title="Static Analysis Report (High Entropy / Suspicious)")
                    table.add_column("File", style="cyan", no_wrap=True)
                    table.add_column("Size", style="magenta")
                    table.add_column("Entropy", style="red")
                    table.add_column("Packed?", style="bold red")
                    
                    for t, res in suspicious_files:
                        table.add_row(
                             os.path.basename(t),
                             format_bytes(res['size']),
                             f"{res['entropy']:.2f}",
                             "YES" if res['is_packed'] else "No"
                         )
                    console.print(table)
                else:
                    print("[!] Suspicious Files Detected (High Entropy):")
                    for t, res in suspicious_files:
                        print(f"    - {t} (Entropy: {res['entropy']:.2f}, Packed: {'YES' if res['is_packed'] else 'No'})")
            else:
                print_rich("[*] No high-entropy files detected.", style="green")

        if total_detections == 0 and not args.analyze:
            print_rich("[+] No threats detected by signature engines.", style="bold green")

        print_rich("[*] Scan Complete.", style="bold white")
        sys.exit(0)

if __name__ == "__main__":
    main()
