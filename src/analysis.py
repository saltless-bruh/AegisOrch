import math
import collections
from typing import Dict, Any, List

try:
    import pefile
except ImportError:
    pefile = None

def calculate_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    
    # Calculate frequency of each byte
    counts = collections.Counter(data)
    total = len(data)
    
    entropy = 0.0
    for count in counts.values():
        p_x = count / total
        entropy -= p_x * math.log2(p_x)
        
    return entropy

def analyze_file_static(path: str) -> Dict[str, Any]:
    info = {
        'path': path,
        'entropy': 0.0,
        'size': 0,
        'is_packed': False,
        'pe_details': {}
    }

    try:
        with open(path, 'rb') as f:
            data = f.read()

        info['size'] = len(data)
        if len(data) == 0:
            return info

        ent = calculate_entropy(data)
        info['entropy'] = round(ent, 4)
        
        # High entropy usually indicates packed or encrypted data
        if ent > 7.0:
            info['is_packed'] = True
        
        # Windows PE Analysis (if pefile is available)
        if pefile and data[:2] == b'MZ':
            try:
                pe = pefile.PE(data=data)
                pe_info = {
                    'machine': hex(pe.FILE_HEADER.Machine),
                    'timestamp': pe.FILE_HEADER.TimeDateStamp,
                    'sections': len(pe.sections),
                    'imports': []
                }
                
                # Extract imported DLLs (limit to 5 for brevity)
                if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                    for entry in pe.DIRECTORY_ENTRY_IMPORT:
                        pe_info['imports'].append(entry.dll.decode('utf-8', 'ignore'))
                        if len(pe_info['imports']) >= 5:
                            break
                
                info['pe_details'] = pe_info
            except Exception:
                pass

    except (OSError, IOError):
        pass

    return info
