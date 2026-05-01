#!/usr/bin/env python3
"""
Download MITRE ATT&CK STIX bundles for offline use.
Run from COA_Project: python scripts/download_mitre_stix.py
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

# Raw paths from mitre-attack/attack-stix-data (update if MITRE changes layout)
URLS = {
    "enterprise-attack.json": (
        "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/"
        "enterprise-attack/enterprise-attack.json"
    ),
    "ics-attack.json": (
        "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/"
        "ics-attack/ics-attack.json"
    ),
}


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "mitre_data"
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, url in URLS.items():
        dest = out_dir / name
        print(f"Downloading {name} …")
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"  → {dest} ({dest.stat().st_size // 1024} KB)")
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
