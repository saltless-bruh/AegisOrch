import os
import sys
import hashlib
import platform
from pathlib import Path
from typing import Optional, Union, List

def resource_path(rel_path: Union[str, Path]) -> str:
    """
    Get absolute path to resource, whether running
    from source or from PyInstaller _MEIPASS bundle.
    """
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel_path)

def compute_sha256(path: Union[str, bytes, os.PathLike], block_size: int = 1 << 16) -> Optional[str]:
    """
    Compute SHA-256 of the file at `path`. Accepts str, bytes, or PathLike.
    """
    p = os.fspath(path)
    try:
        h = hashlib.sha256()
        with open(p, 'rb') as f:
            for chunk in iter(lambda: f.read(block_size), b''):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, IOError):
        return None

def get_system_paths() -> List[str]:
    if platform.system() == "Linux":
        return ['/bin', '/sbin', '/usr/bin', '/usr/sbin']
    else:
        windir = os.environ.get('WINDIR', r'C:\Windows')
        return [os.path.join(windir, 'System32')]
