"""
Passive OT/ICS analyzer — uses only existing host connection list (psutil-style).
No Modbus/S7 frame parsing unless PCAP pipeline is added later (optional Scapy).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple

from ics_analyzer.ot_playbooks import evaluate_ot_playbooks, load_ot_playbooks
from ics_analyzer.protocol_registry import ICS_PORT_REGISTRY, describe_port
from utils.logger import logger


def _parse_ip_port(addr: str) -> Tuple[str, int | None]:
    if not addr or addr == "N/A":
        return "", None
    if ":" not in addr:
        return addr, None
    host, _, tail = addr.rpartition(":")
    try:
        return host or addr, int(tail)
    except ValueError:
        return addr, None


def analyze_ot_ics(system_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Passive-by-default: classify connections that touch well-known ICS ports.
    Does NOT send packets to OT devices.
    """
    conns = system_data.get("network_connections") or []
    hits: List[Dict[str, Any]] = []
    ics_ports_seen: Set[int] = set()
    protocols: Set[str] = set()
    inv_map: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: {"protocols": set(), "processes": set()})

    for c in conns:
        proc = str(c.get("process_name") or "unknown")
        la, lp = _parse_ip_port(str(c.get("local_address") or ""))
        ra, rp = _parse_ip_port(str(c.get("remote_address") or ""))

        for port, direction in ((lp, "local-port"), (rp, "remote-port")):
            if port is None:
                continue
            kind, meta = describe_port(port)
            if kind != "ics":
                continue
            pname = meta.get("protocol", "ICS")
            protocols.add(pname)
            ics_ports_seen.add(port)
            hits.append(
                {
                    "process": proc,
                    "pid": c.get("pid"),
                    "local": c.get("local_address"),
                    "remote": c.get("remote_address"),
                    "direction_hint": direction,
                    "port": port,
                    "protocol": pname,
                    "ics_mitre_examples": meta.get("ics_mitre_examples", []),
                    "risk_note": meta.get("risk_note", ""),
                }
            )
            peer_ip = ra if direction == "remote-port" else la
            inv_map[peer_ip or "local-ics-endpoint"]["processes"].add(proc)
            inv_map[peer_ip or "local-ics-endpoint"]["protocols"].add(pname)

    inventory: List[Dict[str, Any]] = []
    for ip, data in sorted(inv_map.items()):
        inventory.append(
            {
                "endpoint": ip,
                "processes": sorted(data["processes"]),
                "protocols_observed": sorted(data["protocols"]),
                "note": "Inferred from connection table only — not a full OT asset scan.",
            }
        )

    distinct_proto = len(protocols)
    safety_adjacent = distinct_proto >= 2 and len(hits) >= 2

    ot_playbooks = load_ot_playbooks()
    play_triggered = evaluate_ot_playbooks(ot_playbooks, ics_ports_seen, distinct_proto, safety_adjacent)

    # Production continuity score (heuristic demo)
    if not hits:
        pcs = 100
    elif distinct_proto <= 1:
        pcs = 82
    elif not safety_adjacent:
        pcs = 68
    else:
        pcs = 52

    result = {
        "mode": "passive_host_connections",
        "passive_by_default": True,
        "disclaimer": (
            "OT analysis is passive (port/process correlation only). "
            "No ICS frames parsed — add PCAP + Scapy for deep protocol analysis."
        ),
        "ics_protocol_hits": hits,
        "inventory_sketch": inventory,
        "distinct_ics_protocols": distinct_proto,
        "ics_ports_observed": sorted(ics_ports_seen),
        "ot_playbooks_triggered": play_triggered,
        "production_continuity_score": pcs,
        "ics_mitre_matrix_url": "https://attack.mitre.org/matrices/ics/",
        "known_ports_reference": list(ICS_PORT_REGISTRY.keys()),
    }
    logger.info(
        "OT/ICS passive analysis complete",
        hits=len(hits),
        distinct_ics_protocols=distinct_proto,
    )
    return result
