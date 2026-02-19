import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from aegisorch.utils import compute_sha256

def take_snapshot(paths: List[str]) -> Dict[str, str]:
    snap = {}
    for base in paths:
        if not os.path.exists(base):
            continue
        for root, _, files in os.walk(base):
            for fn in files:
                fp = os.path.join(root, fn)
                h = compute_sha256(fp)
                if h:
                    snap[fp] = h
    return snap

def save_snapshot(snap: Dict[str, str], path: str, paths: List[str]) -> None:
    data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'paths': paths,
        'files': snap
    }
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[+] Snapshot saved ({len(snap)} files) -> {path}")

def load_snapshot(path: str) -> Tuple[List[str], Dict[str, str]]:
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('paths', []), data.get('files', {})

def compare_snapshot(old_files: Dict[str, str], new_files: Dict[str, str]) -> Dict[str, List[str]]:
    added = [f for f in new_files if f not in old_files]
    removed = [f for f in old_files if f not in new_files]
    changed = [f for f in old_files
               if f in new_files and new_files[f] != old_files[f]]

    return {
        'added': added,
        'removed': removed,
        'changed': changed
    }
