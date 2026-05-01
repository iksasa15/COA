"""
Defense Context Engine — deterministic matching for Agent #5
==============================================================
Correlates Threat Hunter output with open-source-style APT profiles and playbooks.
Not intelligence-grade attribution; scores are heuristics for SOC triage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.logger import logger

try:
    import yaml
except ImportError:
    yaml = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APT_DIR = PROJECT_ROOT / "apt_profiles"
PLAYBOOKS_DIR = PROJECT_ROOT / "defense_playbooks"

# Subset of signal → MITRE (aligned with IncidentReporter.mitre_mapping)
SIGNAL_TO_TTP: Dict[str, Tuple[str, str, str]] = {
    "suspicious_port": ("T1071", "Application Layer Protocol", "Command and Control"),
    "runs_from_temp": ("T1036", "Masquerading", "Defense Evasion"),
    "external_connection_from_temp": ("T1041", "Exfiltration Over C2 Channel", "Exfiltration"),
    "masquerading_name": ("T1036.005", "Match Legitimate Name or Resource", "Defense Evasion"),
    "high_cpu_low_memory": ("T1496", "Resource Hijacking", "Impact"),
    "no_digital_signature": ("T1553", "Subvert Trust Controls", "Defense Evasion"),
    "yara_match": ("T1204.002", "Malicious File", "Execution"),
}


def _load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    if yaml is None:
        logger.warning("PyYAML not installed — install pyyaml to load APT profiles / playbooks")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load YAML {path}: {e}")
        return None


def _load_all_profiles() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not APT_DIR.is_dir():
        return out
    for p in sorted(APT_DIR.glob("*.yaml")):
        if p.name == "README.yaml":
            continue
        doc = _load_yaml(p)
        if doc and isinstance(doc, dict) and doc.get("id"):
            out.append(doc)
    return out


def _load_all_playbooks() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not PLAYBOOKS_DIR.is_dir():
        return out
    for p in sorted(PLAYBOOKS_DIR.glob("*.yaml")):
        doc = _load_yaml(p)
        if doc and isinstance(doc, dict) and doc.get("id"):
            out.append(doc)
    return out


def _threat_corpus(threats: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for t in threats:
        parts.append(str(t.get("details", "")))
        parts.append(str(t.get("source", "")))
        parts.append(" ".join(str(s) for s in t.get("signals", [])))
    return " ".join(parts).lower()


def _observed_ttp_ids(threats: List[Dict[str, Any]]) -> Set[str]:
    ids: Set[str] = set()
    for t in threats:
        for sig in t.get("signals", []):
            row = SIGNAL_TO_TTP.get(sig)
            if row:
                ids.add(row[0])
    return ids


def _score_profile(profile: Dict[str, Any], blob: str, observed_ttps: Set[str]) -> Tuple[float, List[str]]:
    reasons: List[str] = []
    score = 0.0
    prof_ttps = set(profile.get("ttps") or [])
    overlap = prof_ttps & observed_ttps
    if overlap:
        score += len(overlap) * 16.0
        reasons.append(f"TTP overlap: {', '.join(sorted(overlap))}")

    for kw in profile.get("tool_keywords") or []:
        k = str(kw).lower()
        if k and k in blob:
            score += 10.0
            reasons.append(f"keyword:{kw}")

    pat_hits = 0
    for pat in profile.get("ioc_text_patterns") or []:
        p = str(pat).lower()
        if p and p in blob:
            pat_hits += 1
    if pat_hits:
        score += min(24.0, pat_hits * 8.0)
        reasons.append(f"pattern_hits:{pat_hits}")

    return min(100.0, score), reasons


def _strategic_intent(all_signals: Set[str]) -> Dict[str, str]:
    if "high_cpu_low_memory" in all_signals and len(all_signals) <= 2:
        return {
            "primary": "Opportunistic / Financial (e.g. cryptojacking-style)",
            "secondary": "Low strategic targeting confidence",
        }
    if "external_connection_from_temp" in all_signals or "suspicious_port" in all_signals:
        return {
            "primary": "Credential access / C2 or staging (investigate)",
            "secondary": "Possible targeted network activity",
        }
    if "masquerading_name" in all_signals or "runs_from_temp" in all_signals:
        return {
            "primary": "Defense evasion / persistence staging",
            "secondary": "May support broader intrusion objectives",
        }
    return {
        "primary": "General malicious or suspicious activity",
        "secondary": "Insufficient indicators for strategic subclass",
    }


def _sophistication(threats: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not threats:
        return {"level": 1, "label": "LOW", "notes": "No threats scored"}
    mx = max(int(t.get("score", 0) or 0) for t in threats)
    level = max(1, min(10, round(mx / 10)))
    label = "HIGH" if level >= 7 else "MEDIUM" if level >= 4 else "LOW"
    notes: List[str] = []
    if any("masquerading" in str(t.get("signals", [])) for t in threats):
        notes.append("Masquerading increases assessed operator care")
    if len(threats) >= 3:
        notes.append("Multiple concurrent findings")
    return {"level": level, "label": label, "notes": "; ".join(notes) or "Based on threat scorer only"}


def _campaign_note(threats: List[Dict[str, Any]]) -> str:
    if len(threats) >= 3:
        return "Several related findings in one scan — hunt for related IOCs across hosts (campaign-style review)."
    if len(threats) == 2:
        return "Two findings — correlate timelines and parent/child processes for coordinated activity."
    return "Isolated or single-vector indicators in this scan window."


def _build_mitre_heatmap(
    threats: List[Dict[str, Any]],
    top_profile: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """heat: 1=profile-only emphasis, 2=observed this scan, 3=observed + profile TTP."""
    cells: Dict[str, Dict[str, Any]] = {}

    def add_cell(tid: str, name: str, tactic: str, heat: int):
        cur = cells.get(tid, {"technique_id": tid, "name": name, "tactic": tactic, "heat": 0})
        cur["heat"] = max(cur["heat"], heat)
        cells[tid] = cur

    for t in threats:
        for sig in t.get("signals", []):
            row = SIGNAL_TO_TTP.get(sig)
            if row:
                tid, name, tactic = row
                add_cell(tid, name, tactic, 2)

    if top_profile:
        prof_ttps = {str(x).strip() for x in (top_profile.get("ttps") or [])}
        for tid in prof_ttps:
            if tid in cells:
                add_cell(tid, cells[tid]["name"], cells[tid]["tactic"], 3)
            else:
                tactic_guess = "Unknown"
                name_guess = f"Profile TTP {tid}"
                for _sig, row in SIGNAL_TO_TTP.items():
                    if row[0] == tid:
                        name_guess = row[1]
                        tactic_guess = row[2]
                        break
                add_cell(tid, name_guess, tactic_guess, 1)

    return sorted(cells.values(), key=lambda x: (-x["heat"], x["technique_id"]))


def _eval_playbooks(
    playbooks: List[Dict[str, Any]],
    system_data: Dict[str, Any],
    threats: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    triggered: List[Dict[str, Any]] = []
    all_signals: Set[str] = set()
    for t in threats:
        all_signals.update(t.get("signals") or [])

    def remote_port(conn: Dict[str, Any]) -> Optional[int]:
        r = str(conn.get("remote_address") or "")
        if ":" not in r:
            return None
        tail = r.rsplit(":", 1)[-1]
        try:
            return int(tail)
        except ValueError:
            return None

    for pb in playbooks:
        pid = pb.get("id")
        hit = False
        reason = ""

        ports = pb.get("any_remote_ports") or []
        if ports:
            n = 0
            for c in system_data.get("network_connections") or []:
                rp = remote_port(c)
                if rp is not None and rp in ports:
                    n += 1
            need = int(pb.get("min_connection_matches") or 1)
            if n >= need:
                hit = True
                reason = f"matched sensitive ports {ports} ({n} connection(s))"

        sig_any: List[str] = list(pb.get("signals_any") or [])
        if sig_any and not hit:
            if any(s in all_signals for s in sig_any):
                if len(threats) >= int(pb.get("min_threats") or 1):
                    hit = True
                    reason = f"signals_any {sig_any}"

        sig_all: List[str] = list(pb.get("signals_all") or [])
        if sig_all and not hit:
            if all(any(s in (t.get("signals") or []) for t in threats) for s in sig_all):
                if len(threats) >= int(pb.get("min_threats") or 1):
                    hit = True
                    reason = f"signals_all {sig_all}"

        min_only = pb.get("min_threats_only")
        if min_only is not None and not hit:
            if len(threats) >= int(min_only):
                hit = True
                reason = f"min_threats_only>={min_only}"

        if hit:
            triggered.append(
                {
                    "id": pid,
                    "name_ar": pb.get("name_ar", ""),
                    "name_en": pb.get("name_en", ""),
                    "reason": reason,
                }
            )
    return triggered


def run_defense_context_analysis(system_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    threats: List[Dict[str, Any]] = list(analysis.get("threats") or [])
    blob = _threat_corpus(threats)
    observed = _observed_ttp_ids(threats)
    profiles = _load_all_profiles()
    playbooks = _load_all_playbooks()

    best: Optional[Dict[str, Any]] = None
    best_score = 0.0
    best_reasons: List[str] = []
    rankings: List[Dict[str, Any]] = []

    for prof in profiles:
        sc, rsn = _score_profile(prof, blob, observed)
        rankings.append(
            {
                "profile_id": prof.get("id"),
                "display_name": prof.get("display_name"),
                "similarity": round(sc, 1),
                "reasons": rsn,
            }
        )
        if sc > best_score:
            best_score = sc
            best = prof
            best_reasons = rsn

    rankings.sort(key=lambda x: -x["similarity"])

    all_signals: Set[str] = set()
    for t in threats:
        all_signals.update(t.get("signals") or [])

    confidence = int(min(95, max(0, best_score))) if best_score >= 22 else int(min(40, best_score))
    attribution = {
        "likely_actor": best.get("display_name") if best and best_score >= 22 else "No strong regional APT correlation",
        "profile_id": best.get("id") if best and best_score >= 22 else None,
        "mitre_group_id": best.get("mitre_group_id") if best and best_score >= 22 else None,
        "confidence_percent": confidence,
        "reasoning": "; ".join(best_reasons) if best_reasons else "Insufficient overlap with loaded regional profiles",
        "source_note": (best or {}).get("source_note", "Public MITRE / open sources only"),
    }

    posture: List[str] = [
        "Immediate: validate findings on-host and isolate if business rules allow",
        "Short-term: hunt for shared IOCs across subnet from same timeframe",
        "Strategic: tune profiles/YARA to your sector — these templates are non-authoritative",
    ]
    if analysis.get("critical", 0) > 0:
        posture.insert(0, "Immediate: treat as high priority — critical severity in scan")

    result = {
        "agent": "Defense Context Analyzer",
        "agent_version": "1.0",
        "profiles_ranked": rankings[:8],
        "attribution": attribution,
        "strategic_intent": _strategic_intent(all_signals),
        "sophistication": _sophistication(threats),
        "campaign": {"summary": _campaign_note(threats)},
        "playbooks_triggered": _eval_playbooks(playbooks, system_data, threats),
        "mitre_heatmap": _build_mitre_heatmap(threats, best if best_score >= 18 else None),
        "recommended_defense_posture": posture,
        "disclaimer": (
            "Heuristic demo correlation from open-source-style YAML profiles — "
            "not attribution from classified intelligence."
        ),
    }
    logger.info(
        "Defense context analysis complete",
        top_profile=attribution.get("profile_id"),
        confidence=confidence,
    )
    return result


def format_defense_context_report(d: Dict[str, Any]) -> str:
    """ASCII report block for CLI / incident appendix."""
    lines = [
        "",
        "═" * 42,
        "  DEFENSE CONTEXT ANALYSIS (Agent #5)",
        "═" * 42,
        "",
        "▸ Threat Attribution (heuristic)",
        f"  Likely actor: {d['attribution']['likely_actor']}",
        f"  Confidence: {d['attribution']['confidence_percent']}%",
        f"  Reasoning: {d['attribution']['reasoning']}",
        f"  Source note: {d['attribution']['source_note']}",
        "",
        "▸ Strategic intent",
        f"  Primary: {d['strategic_intent']['primary']}",
        f"  Secondary: {d['strategic_intent']['secondary']}",
        "",
        "▸ Sophistication",
        f"  Level: {d['sophistication']['label']} ({d['sophistication']['level']}/10)",
        f"  Notes: {d['sophistication']['notes']}",
        "",
        "▸ Campaign",
        f"  {d['campaign']['summary']}",
        "",
    ]
    pb = d.get("playbooks_triggered") or []
    if pb:
        lines.append("▸ Playbooks triggered")
        for p in pb:
            lines.append(f"  • [{p.get('id')}] {p.get('name_en','')} — {p.get('reason','')}")
        lines.append("")
    lines.append("▸ Recommended defense posture")
    for item in d.get("recommended_defense_posture") or []:
        lines.append(f"  • {item}")
    lines.append("")
    lines.append(f"Disclaimer: {d.get('disclaimer','')}")
    lines.append("")
    return "\n".join(lines)
