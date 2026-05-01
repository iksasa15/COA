# MITRE STIX data (offline, optional)

Large JSON bundles are **not committed** to the repo. To enable full STIX-backed enrichment later:

1. Run from project root:

```bash
python scripts/download_mitre_stix.py
```

2. Files expected (examples):

- `enterprise-attack.json` — Enterprise ATT&CK
- `ics-attack.json` — ATT&CK for ICS (critical for OT/SCADA contexts)

Source repository: [mitre-attack/attack-stix-data](https://github.com/mitre-attack/attack-stix-data)

After download, you may integrate `mitreattack-python` (`MitreAttackData`) in custom code paths; core C.O.A deep analysis works with embedded mappings without these files.
