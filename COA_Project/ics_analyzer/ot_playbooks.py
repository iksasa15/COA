"""Evaluate OT-specific scenario YAML (defense_playbooks_ot/)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set

try:
    import yaml
except ImportError:
    yaml = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OT_PLAY_DIR = PROJECT_ROOT / "defense_playbooks_ot"


def _load_yaml(path: Path) -> Dict[str, Any] | None:
    if yaml is None:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def load_ot_playbooks() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not OT_PLAY_DIR.is_dir():
        return out
    for p in sorted(OT_PLAY_DIR.glob("*.yaml")):
        doc = _load_yaml(p)
        if doc and isinstance(doc, dict) and doc.get("id"):
            out.append(doc)
    return out


def evaluate_ot_playbooks(
    playbooks: List[Dict[str, Any]],
    ics_ports_seen: Set[int],
    distinct_ics_protocols: int,
    safety_adjacent: bool,
) -> List[Dict[str, Any]]:
    """Very conservative heuristics — demo / hackathon triage only."""
    triggered: List[Dict[str, Any]] = []
    for pb in playbooks:
        pid = pb.get("id")
        reason = ""
        hit = False

        ports_req: List[int] = list(pb.get("require_any_ports") or [])
        if ports_req and any(p in ics_ports_seen for p in ports_req):
            hit = True
            reason = f"matched ICS ports {ports_req}"

        if pb.get("require_min_distinct_protocols"):
            need = int(pb["require_min_distinct_protocols"])
            if distinct_ics_protocols >= need:
                hit = True
                reason = reason or f">= {need} distinct OT protocols from passive view"

        if pb.get("require_safety_adjacent") and safety_adjacent:
            hit = True
            reason = reason or "safety-adjacent heuristic (multi-ICS + engineering pattern)"

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
