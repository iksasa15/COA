"""Static OT/ICS bundle for UI / presentation demo (not live host data)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ics_analyzer.protocol_registry import ICS_PORT_REGISTRY


def load_presentation_demo_ot_ics() -> Dict[str, Any]:
    root = Path(__file__).resolve().parent.parent
    path = root / "fixtures" / "demo_ot_ics.json"
    with open(path, encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    data["known_ports_reference"] = list(ICS_PORT_REGISTRY.keys())
    return data
