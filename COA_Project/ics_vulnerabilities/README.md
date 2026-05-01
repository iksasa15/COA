# ICS vulnerabilities (local enrichment — no fabricated CVEs)

Use authoritative feeds only:

- **CISA ICS Advisories:** https://www.cisa.gov/news-events/cybersecurity-advisories
- **Vendor CERT:** Siemens ProductCERT, Rockwell Security, Schneider Electric, ABB, etc.

## Suggested workflow

1. Export advisory JSON or CSV from CISA (per your clearance / policy).
2. Store under `ics_vulnerabilities/` (gitignored if sensitive).
3. Map **asset fingerprints** from passive inventory (vendor string from future enrichment) to advisory records.

C.O.A currently does **not** ship CVE rows: wrong data would harm trust in hackathon judging.

Optional: add `vendor_hints.yaml` with *search URLs* only (no CVSS claims).
