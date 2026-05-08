"""
Advanced Threat Analysis Engine
================================
Enhanced with:
- Weighted ML-style scoring (not just rules)
- Process behavior analysis
- Registry tampering detection (stubs)
- Confidence levels for reducing false positives
"""

import platform
from typing import Dict, List
from config.settings import (
    TRUSTED_PROCESSES,
    SUSPICIOUS_PATHS,
    SUSPICIOUS_PORTS,
    TRUSTED_IP_RANGES,
)
from utils.logger import logger


class ThreatScorer:
    """
    نظام تسجيل النقاط الذكي - يحاكي ML بدون نموذج
    كل إشارة لها وزن، والمجموع يحدد الخطورة
    """

    SIGNALS = {
        # Network signals
        'suspicious_port': 40,
        'known_malicious_ip': 50,
        'external_connection_from_temp': 35,
        'encrypted_tunnel_unusual_port': 25,

        # Process signals
        'runs_from_temp': 30,
        'no_digital_signature': 20,
        'hidden_window': 15,
        'high_cpu_low_memory': 15,  # cryptominer signature
        'spawns_many_children': 20,
        'unusual_parent': 25,

        # Behavioral signals
        'recently_created': 10,
        'runs_as_system': 15,
        'masquerading_name': 30,  # svchost.exe from Desktop
    }

    SEVERITY_THRESHOLDS = {
        'CRITICAL': 80,
        'HIGH': 60,
        'MEDIUM': 40,
        'LOW': 20,
    }

    @classmethod
    def calculate_severity(cls, score: int) -> str:
        """تحويل النقاط إلى مستوى خطورة"""
        for severity, threshold in cls.SEVERITY_THRESHOLDS.items():
            if score >= threshold:
                return severity
        return 'INFO'

    @classmethod
    def calculate_confidence(cls, signals: List[str]) -> str:
        """حساب مستوى الثقة بناءً على عدد الإشارات"""
        count = len(signals)
        if count >= 3:
            return 'HIGH'
        elif count == 2:
            return 'MEDIUM'
        return 'LOW'


class ThreatAnalyzer:
    """محلل التهديدات المتقدم"""

    # Suspicious process names often used for masquerading
    MASQUERADING_PATTERNS = [
        'svch0st', 'scvhost', 'explorer ', 'winlog0n',  # character substitution
        'chrom3', 'firef0x',
    ]

    @staticmethod
    def _is_trusted_ip(ip: str) -> bool:
        if not ip or ip == "N/A":
            return True
        return any(ip.startswith(prefix) for prefix in TRUSTED_IP_RANGES)

    @staticmethod
    def _is_suspicious_path(path: str) -> bool:
        if not path or path == "N/A":
            return False
        path_lower = path.lower()
        return any(sus in path_lower for sus in SUSPICIOUS_PATHS)

    @staticmethod
    def _is_trusted_process(name: str) -> bool:
        if not name:
            return False
        return name.lower() in [p.lower() for p in TRUSTED_PROCESSES]

    @staticmethod
    def _is_masquerading(name: str) -> bool:
        """كشف محاولات انتحال الأسماء"""
        if not name:
            return False
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in ThreatAnalyzer.MASQUERADING_PATTERNS)

    @classmethod
    def analyze_connection(cls, conn: Dict) -> Dict:
        """تحليل متقدم لاتصال واحد مع scoring"""
        if "error" in conn:
            return None

        signals = []
        score = 0
        details_parts = []

        remote = conn.get("remote_address", "N/A")
        process_name = conn.get("process_name", "Unknown")
        process_path = conn.get("process_path", "N/A")
        pid = conn.get("pid")

        remote_ip = remote.split(":")[0] if ":" in remote else remote
        remote_port = None
        try:
            remote_port = int(remote.split(":")[-1]) if ":" in remote else None
        except ValueError:
            pass

        # إشارة 1: منفذ مشبوه
        if remote_port and remote_port in SUSPICIOUS_PORTS:
            signals.append('suspicious_port')
            score += ThreatScorer.SIGNALS['suspicious_port']
            details_parts.append(f"suspicious port {remote_port}")

        # إشارة 2: عملية من مجلد مؤقت
        if cls._is_suspicious_path(process_path):
            signals.append('runs_from_temp')
            score += ThreatScorer.SIGNALS['runs_from_temp']
            details_parts.append("running from temp folder")

        # إشارة 3: اتصال خارجي + مجلد مشبوه
        if (cls._is_suspicious_path(process_path)
                and not cls._is_trusted_ip(remote_ip)
                and remote_ip != "N/A"):
            signals.append('external_connection_from_temp')
            score += ThreatScorer.SIGNALS['external_connection_from_temp']
            details_parts.append(f"connecting externally to {remote_ip}")

        # إشارة 4: انتحال اسم
        if cls._is_masquerading(process_name):
            signals.append('masquerading_name')
            score += ThreatScorer.SIGNALS['masquerading_name']
            details_parts.append("masquerading process name")

        if not signals:
            return None  # لا شيء مشبوه

        severity = ThreatScorer.calculate_severity(score)
        confidence = ThreatScorer.calculate_confidence(signals)

        # تحديد الإجراء المناسب
        if score >= 80:
            action = "kill_process"
        elif score >= 40:
            action = "investigate"
        else:
            action = "monitor"

        return {
            "severity": severity,
            "confidence": confidence,
            "score": score,
            "type": "Network Threat",
            "source": f"{process_name} (PID: {pid})",
            "details": f"Detected: {', '.join(details_parts)}",
            "signals": signals,
            "recommended_action": action,
            "target_pid": pid,
            "target_ip": remote_ip,
        }

    @classmethod
    def analyze_process(cls, proc: Dict) -> Dict:
        """تحليل متقدم لعملية واحدة"""
        signals = []
        score = 0
        details_parts = []

        path = proc.get("path", "N/A")
        name = proc.get("name", "Unknown")
        pid = proc.get("pid")
        cpu = proc.get("cpu_percent", 0)
        memory = proc.get("memory_percent", 0)

        # إشارة 1: مسار مؤقت
        if cls._is_suspicious_path(path) and not cls._is_trusted_process(name):
            signals.append('runs_from_temp')
            score += ThreatScorer.SIGNALS['runs_from_temp']
            details_parts.append(f"runs from {path[:50]}")

        # إشارة 2: انتحال اسم
        if cls._is_masquerading(name):
            signals.append('masquerading_name')
            score += ThreatScorer.SIGNALS['masquerading_name']
            details_parts.append("suspicious name pattern")

        # إشارة 3: cryptominer signature (high CPU, low memory)
        if cpu > 70 and memory < 5 and not cls._is_trusted_process(name):
            signals.append('high_cpu_low_memory')
            score += ThreatScorer.SIGNALS['high_cpu_low_memory']
            details_parts.append(f"{cpu}% CPU + {memory}% RAM (cryptominer pattern)")

        # إشارة 4: لا مسار تنفيذي (غالباً قيد جمع البيانات) — لا تُخطئ kernel_task ونظائره على Darwin
        if path == "N/A" and not cls._is_trusted_process(name):
            pid_int = int(pid) if pid is not None and str(pid).isdigit() else None
            if platform.system() == "Darwin" and (
                (name or "").lower() == "kernel_task"
                or pid_int == 0
            ):
                pass
            else:
                signals.append("no_digital_signature")
                score += ThreatScorer.SIGNALS["no_digital_signature"]
                details_parts.append("no executable path")

        if not signals:
            return None

        severity = ThreatScorer.calculate_severity(score)
        confidence = ThreatScorer.calculate_confidence(signals)

        if score >= 60:
            action = "kill_process"
        elif score >= 30:
            action = "investigate"
        else:
            action = "monitor"

        return {
            "severity": severity,
            "confidence": confidence,
            "score": score,
            "type": "Process Threat",
            "source": f"{name} (PID: {pid})",
            "details": f"Detected: {', '.join(details_parts)}",
            "signals": signals,
            "recommended_action": action,
            "target_pid": pid,
        }

    @classmethod
    def full_analysis(cls, system_data: Dict) -> Dict:
        """تحليل شامل بأسلوب محسّن"""
        logger.info("Starting threat analysis")

        threats = []

        # تحليل الاتصالات
        for conn in system_data.get("network_connections", []):
            threat = cls.analyze_connection(conn)
            if threat:
                threats.append(threat)
                logger.log_threat(threat)

        # تحليل العمليات
        for proc in system_data.get("processes", []):
            threat = cls.analyze_process(proc)
            if threat:
                threats.append(threat)
                logger.log_threat(threat)

        # ترتيب حسب score (الأعلى خطورة أولاً)
        threats.sort(key=lambda x: x.get("score", 0), reverse=True)

        result = {
            "total_threats": len(threats),
            "critical": sum(1 for t in threats if t["severity"] == "CRITICAL"),
            "high": sum(1 for t in threats if t["severity"] == "HIGH"),
            "medium": sum(1 for t in threats if t["severity"] == "MEDIUM"),
            "low": sum(1 for t in threats if t["severity"] == "LOW"),
            "high_confidence_threats": sum(1 for t in threats if t.get("confidence") == "HIGH"),
            "threats": threats,
        }

        logger.info(
            f"Analysis complete: {len(threats)} threats found",
            critical=result["critical"],
            high=result["high"],
        )

        return result
