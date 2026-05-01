"""
Agent #6 — ICS Specialist (OT-aware triage)
===========================================
Rule-based assessment for hackathon / SOC narrative.
Does not replace an OT engineer or SIS validation.
"""

from __future__ import annotations

from typing import Any, Dict, List


class ICSSpecialistAgent:
    """محلل الأنظمة الصناعية — وكيل سادس (منطق حتمي محلي)."""

    ROLE = "ICS Specialist Agent"

    @staticmethod
    def assess(ot_ics: Dict[str, Any]) -> Dict[str, Any]:
        hits: List[Dict[str, Any]] = list(ot_ics.get("ics_protocol_hits") or [])
        playbooks = ot_ics.get("ot_playbooks_triggered") or []
        pcs = int(ot_ics.get("production_continuity_score") or 100)

        if not hits:
            return {
                "ascii_report": (
                    "ICS THREAT ASSESSMENT\n"
                    "─────────────────────\n"
                    "No industrial protocol ports observed on this host's connection table.\n"
                    "If OT exists elsewhere, mirror SPAN/tap traffic to a passive collector for PCAP.\n"
                ),
                "cyber_impact": "NONE",
                "operational_impact": "NONE",
                "safety_impact": "NONE",
                "production_continuity_score": pcs,
                "do_list": ["Maintain network segmentation IT/OT", "Schedule passive OT visibility pilot"],
                "dont_list": ["Run active Modbus/S7 scanners against production PLCs"],
                "mitre_ics_examples": [],
            }

        cyber = "HIGH" if len(hits) >= 3 else "MEDIUM"
        op = "HIGH" if playbooks else "MODERATE"
        safety = "MODERATE" if any("T0843" in str(h.get("ics_mitre_examples")) for h in hits) else "LOW"

        lines = [
            "ICS THREAT ASSESSMENT",
            "─────────────────────",
            f"Passive ICS protocol observations: {len(hits)}",
            f"Distinct OT-style protocols: {ot_ics.get('distinct_ics_protocols', 0)}",
            "",
            "Cyber impact (connection-level): " + cyber,
            "Operational impact (heuristic): " + op,
            "Safety impact (heuristic): " + safety,
            "",
            "Production continuity score (demo heuristic): " + str(pcs) + "/100",
            "",
            "Recommended response (production-safe):",
            "  ✓ DO: Correlate with maintenance window & change tickets",
            "  ✓ DO: Capture host-side logs + switch flow if available",
            "  ✓ DO: Notify OT shift lead before any containment",
            "  ✗ DON'T: Restart PLC or block ICS blindly from IT tools",
            "  ✗ DON'T: Run unapproved active scans on OT VLANs",
            "",
        ]
        if playbooks:
            lines.append("OT scenario playbooks flagged:")
            for p in playbooks:
                lines.append(f"  • [{p.get('id')}] {p.get('name_en', '')} — {p.get('reason', '')}")
            lines.append("")

        mitre_refs: List[str] = []
        for h in hits[:8]:
            for tid in h.get("ics_mitre_examples") or []:
                if tid not in mitre_refs:
                    mitre_refs.append(tid)
        if mitre_refs:
            lines.append("MITRE ICS mapping (examples): " + ", ".join(mitre_refs))

        return {
            "ascii_report": "\n".join(lines) + "\n",
            "cyber_impact": cyber,
            "operational_impact": op,
            "safety_impact": safety,
            "production_continuity_score": pcs,
            "do_list": [
                "Isolate engineering workstation VLAN if unauthorized programming suspected",
                "Preserve PCAP from tap if TRITON-like scenario triggered",
            ],
            "dont_list": [
                "STOP CPU / download block without OT approval",
                "Block OPC UA globally without HMI impact analysis",
            ],
            "mitre_ics_examples": mitre_refs[:12],
        }
