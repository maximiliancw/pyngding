"""OUI vendor lookup from local file."""
import re
from typing import Dict, Optional


class OUILookup:
    """OUI vendor lookup from a local file."""
    
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path
        self.oui_map: Dict[str, str] = {}
        if file_path:
            self.load(file_path)
    
    def load(self, file_path: str) -> int:
        """Load OUI mappings from a file.
        
        Supports formats:
        - "AA-BB-CC   (hex)  Vendor Name"
        - "AABBCC,Vendor Name" (CSV)
        
        Returns number of entries loaded.
        """
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Try format: "AA-BB-CC   (hex)  Vendor"
                    match = re.match(r'([0-9A-Fa-f]{2}[-:]?[0-9A-Fa-f]{2}[-:]?[0-9A-Fa-f]{2})\s+.*?\s+(.+)', line)
                    if match:
                        oui = match.group(1).upper().replace('-', '').replace(':', '')
                        vendor = match.group(2).strip()
                        if len(oui) == 6:
                            self.oui_map[oui] = vendor
                            count += 1
                            continue
                    
                    # Try CSV format: "AABBCC,Vendor"
                    if ',' in line:
                        parts = line.split(',', 1)
                        if len(parts) == 2:
                            oui = parts[0].strip().upper().replace('-', '').replace(':', '')
                            vendor = parts[1].strip()
                            if len(oui) == 6:
                                self.oui_map[oui] = vendor
                                count += 1
                                continue
                    
                    # Try simple format: "AABBCC Vendor Name"
                    match = re.match(r'([0-9A-Fa-f]{6})\s+(.+)', line)
                    if match:
                        oui = match.group(1).upper()
                        vendor = match.group(2).strip()
                        self.oui_map[oui] = vendor
                        count += 1
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading OUI file: {e}", file=__import__('sys').stderr)
        
        return count
    
    def lookup(self, mac: str) -> Optional[str]:
        """Look up vendor for a MAC address.
        
        Returns vendor name or None if not found.
        """
        if not mac:
            return None
        
        # Normalize MAC address
        mac_clean = mac.upper().replace('-', '').replace(':', '').replace('.', '')
        if len(mac_clean) < 6:
            return None
        
        # Get OUI (first 6 hex characters)
        oui = mac_clean[:6]
        return self.oui_map.get(oui)


# Global instance (lazy loaded)
_oui_lookup: Optional[OUILookup] = None


def get_vendor(mac: str, db_path: str) -> Optional[str]:
    """Get vendor for a MAC address using OUI lookup if enabled."""
    from pyngding.db import get_ui_setting
    from pyngding.settings import DEFAULTS
    
    oui_enabled = get_ui_setting(db_path, 'oui_lookup_enabled', DEFAULTS['oui_lookup_enabled']).lower() == 'true'
    if not oui_enabled:
        return None
    
    oui_file = get_ui_setting(db_path, 'oui_file_path', '')
    if not oui_file:
        return None
    
    global _oui_lookup
    
    # Lazy load or reload if file changed
    if _oui_lookup is None or _oui_lookup.file_path != oui_file:
        _oui_lookup = OUILookup(oui_file)
    
    return _oui_lookup.lookup(mac)

