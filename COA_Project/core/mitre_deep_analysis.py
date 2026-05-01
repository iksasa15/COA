"""
MITRE ATT&CK deep analysis — kill chain ordering, D3FEND hints, Navigator layer.
================================================================================
Uses static mappings + scan-derived signals (no cloud). Optional STIX files
in mitre_data/ can be wired later via mitreattack-python.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

# Enterprise tactic order (simplified kill-chain narrative)
TACTIC_ORDER: List[Tuple[str, str]] = [
    ("TA0043", "Reconnaissance"),
    ("TA0042", "Resource Development"),
    ("TA0001", "Initial Access"),
    ("TA0002", "Execution"),
    ("TA0003", "Persistence"),
    ("TA0004", "Privilege Escalation"),
    ("TA0005", "Defense Evasion"),
    ("TA0006", "Credential Access"),
    ("TA0007", "Discovery"),
    ("TA0008", "Lateral Movement"),
    ("TA0009", "Collection"),
    ("TA0011", "Command and Control"),
    ("TA0010", "Exfiltration"),
    ("TA0040", "Impact"),
]

# signal -> primary technique row + narrative
SIGNAL_DEEP: Dict[str, Dict[str, Any]] = {
    "suspicious_port": {
        "technique": "T1071",
        "name": "Application Layer Protocol",
        "tactic": "Command and Control",
        "ta_id": "TA0011",
        "often_precedes": ["T1048 (Exfiltration)", "T1003 (Credential Access)"],
        "often_follows": ["T1071.004 DNS tunneling (hunt)", "T1573 (Encrypted channel)"],
        "detection_hint": "DNS / proxy logs; TLS inspection where policy allows; flow metadata.",
        "mitigation_mitre": ["M1031 (Network Intrusion Prevention)", "M1042 (Disable or Remove Feature)"],
        "d3fend": [
            {"id": "D3-NTF", "name": "Network Traffic Filtering"},
            {"id": "D3-PH", "name": "Protocol Analysis"},
        ],
    },
    "runs_from_temp": {
        "technique": "T1036",
        "name": "Masquerading",
        "tactic": "Defense Evasion",
        "ta_id": "TA0005",
        "often_precedes": ["T1059 Execution from script", "T1547 Persistence"],
        "often_follows": ["T1566 Phishing delivery", "T1190 Exploit facing app"],
        "detection_hint": "File-create/modify in %TEMP%; parent-child anomalies; AppLocker/WDAC.",
        "mitigation_mitre": ["M1040 (Behavior Prevention on Endpoint)", "M1026 (Privileged Account Management)"],
        "d3fend": [
            {"id": "D3-EAL", "name": "Executable Allowlisting"},
            {"id": "D3-PA", "name": "Process Analysis"},
        ],
    },
    "external_connection_from_temp": {
        "technique": "T1041",
        "name": "Exfiltration Over C2 Channel",
        "tactic": "Exfiltration",
        "ta_id": "TA0010",
        "often_precedes": ["T1021 Lateral movement", "T1486 Impact"],
        "often_follows": ["T1071 C2", "T1059.001 PowerShell"],
        "detection_hint": "Egress from unusual processes; byte ratios; beaconing stats.",
        "mitigation_mitre": ["M1037 (Filter Network Traffic)", "M1057 (Data Loss Prevention)"],
        "d3fend": [{"id": "D3-NTF", "name": "Network Traffic Filtering"}],
    },
    "masquerading_name": {
        "technique": "T1036.005",
        "name": "Match Legitimate Name or Resource",
        "tactic": "Defense Evasion",
        "ta_id": "TA0005",
        "often_precedes": ["T1055 Process Injection", "T1003 Credential dumping"],
        "often_follows": ["T1204 User execution"],
        "detection_hint": "Image path vs binary metadata; signed binary mismatches.",
        "mitigation_mitre": ["M1049 (Antivirus/Antimalware)", "M1022 (Restrict Admin)"],
        "d3fend": [{"id": "D3-PA", "name": "Process Analysis"}],
    },
    "high_cpu_low_memory": {
        "technique": "T1496",
        "name": "Resource Hijacking",
        "tactic": "Impact",
        "ta_id": "TA0040",
        "often_precedes": [],
        "often_follows": ["T1204 Execution", "Supply-chain delivered miners"],
        "detection_hint": "CPU baselines; pool reputation; unexpected miners.",
        "mitigation_mitre": ["M1048 (Application Isolation and Sandboxing)"],
        "d3fend": [{"id": "D3-OSM", "name": "Operating System Monitoring"}],
    },
    "no_digital_signature": {
        "technique": "T1553",
        "name": "Subvert Trust Controls",
        "tactic": "Defense Evasion",
        "ta_id": "TA0005",
        "often_precedes": ["T1059 Scripts", "T1548 Abuse elevation"],
        "often_follows": ["T1566 User opened payload"],
        "detection_hint": "Code signing policy; WDAC events.",
        "mitigation_mitre": ["M1042", "M1051 (Update Software)"],
        "d3fend": [{"id": "D3-EAL", "name": "Executable Allowlisting"}],
    },
    "yara_match": {
        "technique": "T1204.002",
        "name": "Malicious File",
        "tactic": "Execution",
        "ta_id": "TA0002",
        "often_precedes": ["T1059", "T1071"],
        "often_follows": ["T1566.001 Spearphishing attachment"],
        "detection_hint": "Retain samples (policy); retrohunt on YARA hits.",
        "mitigation_mitre": ["M1049"],
        "d3fend": [{"id": "D3-PA", "name": "Process Analysis"}],
    },
}


def _tactic_rank(ta_id: str) -> int:
    for i, (tid, _) in enumerate(TACTIC_ORDER):
        if tid == ta_id:
            return i
    return 99


def _threat_blob(threats: List[Dict[str, Any]]) -> str:
    return " ".join(
        f"{t.get('details','')} {t.get('source','')}".lower() for t in threats
    )


def collect_enriched_techniques(threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One row per unique technique from observed signals (+ heuristic PowerShell)."""
    rows: Dict[str, Dict[str, Any]] = {}
    blob = _threat_blob(threats)

    for t in threats:
        for sig in t.get("signals") or []:
            base = SIGNAL_DEEP.get(sig)
            if not base:
                continue
            tid = base["technique"]
            if tid not in rows:
                rows[tid] = {
                    **base,
                    "sources": [],
                    "confidence": t.get("confidence", "MEDIUM"),
                }
            rows[tid]["sources"].append(t.get("source", ""))

    if "powershell" in blob or "-enc" in blob or "encodedcommand" in blob:
        tid = "T1059.001"
        if tid not in rows:
            rows[tid] = {
                "technique": tid,
                "name": "PowerShell",
                "tactic": "Execution",
                "ta_id": "TA0002",
                "often_precedes": ["T1003 Credential Access", "T1021 Lateral Movement"],
                "often_follows": ["T1566 Phishing", "T1190 Exploit public-facing application"],
                "detection_hint": "Enable PowerShell Script Block Logging; constrain language mode; hunt -EncodedCommand.",
                "mitigation_mitre": ["M1042", "M1049"],
                "d3fend": [
                    {"id": "D3-SCA", "name": "Script Authentication"},
                    {"id": "D3-PA", "name": "Process Analysis"},
                ],
                "sources": ["heuristic:powershell-in-findings"],
                "confidence": "MEDIUM",
            }

    return sorted(rows.values(), key=lambda r: _tactic_rank(r["ta_id"]))


def build_kill_chain_phases(threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = collect_enriched_techniques(threats)
    phases: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        ta = r["ta_id"]
        phases.setdefault(ta, []).append(r)
    out = []
    for ta_id, tactic_name in TACTIC_ORDER:
        if ta_id in phases:
            out.append({"ta_id": ta_id, "tactic": tactic_name, "techniques": phases[ta_id]})
    return out


def _ics_context(system_data: Dict[str, Any], playbooks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Heuristic ICS mention when SCADA-style ports or playbook fired."""
    ports = {502, 102}
    hit = any(
        p.get("id") == "critical_infrastructure" for p in (playbooks or [])
    )
    for c in system_data.get("network_connections") or []:
        ra = str(c.get("remote_address") or "")
        if ":" in ra:
            try:
                p = int(ra.rsplit(":", 1)[-1])
                if p in ports:
                    hit = True
                    break
            except ValueError:
                pass
    return {
        "ics_relevant": hit,
        "note": (
            "Review MITRE ATT&CK for ICS (e.g. T0855 Unauthorized Command Message, "
            "T0831 Manipulation of Control) if OT assets are in scope — import ics-attack.json "
            "via scripts/download_mitre_stix.py for full matrix alignment."
        )
        if hit
        else "No industrial port heuristics in this scan window.",
    }


def suggested_detection_gaps(observed_ids: Set[str]) -> List[str]:
    """Static gap hints — not an inventory of your SOC."""
    gaps = []
    if "T1071.004" not in observed_ids:
        gaps.append(
            "No DNS tunneling (T1071.004) hypothesis in this scan — if DNS is blind spot, deploy DNS logging/monitoring."
        )
    if "T1090.003" not in observed_ids:
        gaps.append(
            "Multi-hop proxy (T1090.003) not indicated — validate forward-proxy and egress visibility."
        )
    return gaps


def build_navigator_layer(
    hostname: str,
    heatmap: List[Dict[str, Any]],
    name: str = "C.O.A Threat Analysis",
) -> Dict[str, Any]:
    """ATT&CK Navigator-compatible layer (minimal fields; Navigator may extend)."""
    techniques = []
    for cell in heatmap or []:
        tid = cell.get("technique_id") or ""
        if not tid.startswith("T"):
            continue
        heat = int(cell.get("heat") or 0)
        score = min(100, max(1, heat * 28 + 15))
        if heat >= 3:
            color = "#991b1b"
        elif heat == 2:
            color = "#ea580c"
        elif heat == 1:
            color = "#ca8a04"
        else:
            color = "#64748b"
        techniques.append(
            {
                "techniqueID": tid,
                "score": score,
                "color": color,
                "comment": f"{cell.get('name', '')} — host {hostname} (C.O.A heat={heat})",
            }
        )
    return {
        "name": f"{name} — {hostname}",
        "versions": {"attack": "14", "navigator": "5.0"},
        "domain": "enterprise-attack",
        "techniques": techniques,
        "gradient": {
            "colors": ["#ffffff", "#ffcccc", "#ff6666", "#990000"],
            "minValue": 0,
            "maxValue": 100,
        },
        "legendItems": [],
    }


def format_deep_mitre_report(
    threats: List[Dict[str, Any]],
    defense_context: Optional[Dict[str, Any]],
    system_data: Dict[str, Any],
    system_info: Dict[str, Any],
) -> str:
    """ASCII block for incident report."""
    lines: List[str] = []
    lines.append("")
    lines.append("═" * 50)
    lines.append("  MITRE ATT&CK DEEP ANALYSIS (C.O.A)")
    lines.append("═" * 50)

    phases = build_kill_chain_phases(threats)
    if not phases:
        lines.append("\nNo ATT&CK-mapped techniques from this scan (clean or below mapping threshold).")
        return "\n".join(lines)

    lines.append("\n▸ Detected techniques (ordered by tactic / kill-chain view)\n")
    for ph in phases:
        lines.append(f"  ┌─ {ph['tactic']} ({ph['ta_id']})")
        for tech in ph["techniques"]:
            lines.append(f"  │  • {tech['technique']} — {tech['name']}")
            lines.append(f"  │    Confidence: {tech.get('confidence','')} | Sources: {', '.join(tech.get('sources') or [])[:120]}")
        lines.append("  └" + "─" * 46)

    obs_ids: Set[str] = set()
    for ph in phases:
        for tech in ph["techniques"]:
            obs_ids.add(tech["technique"])

    lines.append("\n▸ Attack chain completeness (heuristic)")
    lines.append(f"  Tactics with at least one mapped technique: {len(phases)} / {len(TACTIC_ORDER)}")
    lines.append("  ⚠ Interpret as triage hint — not proof of attacker progress.")

    if defense_context:
        att = defense_context.get("attribution") or {}
        lines.append("\n▸ Threat actor correlation (defense context / heuristic)")
        lines.append(f"  Best match: {att.get('likely_actor', 'N/A')} — {att.get('confidence_percent', 0)}%")
        alts = defense_context.get("profiles_ranked") or []
        if len(alts) > 1:
            lines.append(f"  Alternative: {alts[1].get('display_name', 'N/A')} — {alts[1].get('similarity', 0)} similarity")

    lines.append("\n▸ Defensive mappings (MITRE mitigations + D3FEND hints)")
    seen = set()
    for ph in phases:
        for tech in ph["techniques"]:
            tid = tech["technique"]
            if tid in seen:
                continue
            seen.add(tid)
            for m in tech.get("mitigation_mitre") or []:
                lines.append(f"  • {m} — relates to {tid}")
            for d in tech.get("d3fend") or []:
                lines.append(f"  • D3FEND {d.get('id')}: {d.get('name')} ← for {tid}")

    lines.append("\n▸ Expected next steps (generic prediction, not attribution)")
    last = phases[-1]["techniques"][-1] if phases else {}
    for hint in last.get("often_precedes") or []:
        lines.append(f"  → Often next in narratives: {hint}")

    gaps = suggested_detection_gaps(obs_ids)
    if gaps:
        lines.append("\n▸ Detection gap hints (environment-agnostic)")
        for g in gaps:
            lines.append(f"  • {g}")

    ics = _ics_context(system_data, (defense_context or {}).get("playbooks_triggered") or [])
    lines.append("\n▸ ICS / OT context")
    lines.append(f"  {ics['note']}")

    lines.append("\n▸ Shallow vs deep binding")
    lines.append("  Shallow: single technique label without tactic chain.")
    lines.append("  Deep: tactic ordering, likely before/after, mitigations, D3FEND, ICS note, Navigator export.")

    lines.append("")
    return "\n".join(lines)


def build_mitre_deep_bundle(
    analysis: Dict[str, Any],
    defense_context: Optional[Dict[str, Any]],
    system_data: Dict[str, Any],
    system_info: Dict[str, Any],
) -> Dict[str, Any]:
    threats = list(analysis.get("threats") or [])
    heat = (defense_context or {}).get("mitre_heatmap") or []
    hostname = str(system_info.get("hostname") or "host")
    phases = build_kill_chain_phases(threats)
    navigator = build_navigator_layer(hostname, heat, "C.O.A Threat Analysis")
    report = format_deep_mitre_report(threats, defense_context, system_data, system_info)
    return {
        "kill_chain_phases": phases,
        "navigator_layer": navigator,
        "ascii_report": report,
        "ics_context": _ics_context(system_data, (defense_context or {}).get("playbooks_triggered") or []),
        "detection_gap_hints": suggested_detection_gaps(
            {t["technique"] for ph in phases for t in ph["techniques"]}
        ),
    }
