"""
Well-known industrial protocol ports → labels and MITRE for ICS technique hints.
References: public MITRE ATT&CK for ICS matrix (technique IDs may vary by revision).
"""

from typing import Any, Dict, List, Tuple

# port -> metadata (passive inference from TCP/UDP port only)
ICS_PORT_REGISTRY: Dict[int, Dict[str, Any]] = {
    502: {
        "protocol": "Modbus TCP",
        "category": "SCADA/PLC",
        "ics_mitre_examples": ["T0852", "T0869"],
        "risk_note": "Write operations (FC06/16) are high-risk if unexpected — verify with operations.",
    },
    102: {
        "protocol": "S7comm (Siemens typical)",
        "category": "PLC/HMI",
        "ics_mitre_examples": ["T0843", "T0866"],
        "risk_note": "Programming or STOP-style sessions require OT approval — never block blindly.",
    },
    20000: {
        "protocol": "DNP3 (common)",
        "category": "Energy/Utilities",
        "ics_mitre_examples": ["T0855", "T0806"],
        "risk_note": "Operate / cold-restart class functions are safety-critical.",
    },
    4840: {
        "protocol": "OPC UA",
        "category": "Integration",
        "ics_mitre_examples": ["T0884", "T0861"],
        "risk_note": "IT/OT bridge via OPC UA is a common lateral path — review segmentation.",
    },
    44818: {
        "protocol": "EtherNet/IP (Rockwell ecosystem)",
        "category": "PLC",
        "ics_mitre_examples": ["T0858", "T0869"],
        "risk_note": "",
    },
    47808: {
        "protocol": "BACnet/IP",
        "category": "Building/Process",
        "ics_mitre_examples": ["T0855"],
        "risk_note": "",
    },
    2404: {
        "protocol": "IEC 60870-5-104 (common in power)",
        "category": "Energy",
        "ics_mitre_examples": ["T0806", "T0805"],
        "risk_note": "",
    },
}


def describe_port(port: int) -> Tuple[str, Dict[str, Any]]:
    if port in ICS_PORT_REGISTRY:
        return "ics", ICS_PORT_REGISTRY[port]
    return "other", {}
