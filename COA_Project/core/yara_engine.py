"""
YARA Rules Engine
=================
Scans files against YARA rules for malware detection
Requires: pip install yara-python

Features:
- Automatic rule compilation and caching
- File scanning
- Memory/process scanning (Windows)
- Batch scanning
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from utils.logger import logger

# Try to import yara, but fail gracefully
try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False
    yara = None


class YaraEngine:
    """محرك YARA لفحص الملفات بالقواعد"""

    def __init__(self, rules_dir: Optional[Path] = None):
        """
        Args:
            rules_dir: مسار مجلد قواعد YARA (افتراضي: ./rules)
        """
        self.available = YARA_AVAILABLE

        if not self.available:
            logger.warning(
                "YARA not installed. Install with: pip install yara-python"
            )
            return

        self.rules_dir = rules_dir or Path(__file__).parent / "rules"
        self.compiled_rules = None
        self._load_rules()

    def _load_rules(self):
        """تحميل وتجميع القواعد مرة واحدة"""
        if not self.available:
            return

        if not self.rules_dir.exists():
            logger.warning(f"YARA rules directory not found: {self.rules_dir}")
            return

        # جمع كل ملفات .yar و .yara
        rule_files = list(self.rules_dir.glob("*.yar")) + list(self.rules_dir.glob("*.yara"))

        if not rule_files:
            logger.warning("No YARA rule files found")
            return

        try:
            # بناء dict من {namespace: filepath}
            filepaths = {f.stem: str(f) for f in rule_files}
            self.compiled_rules = yara.compile(filepaths=filepaths)
            logger.info(f"YARA rules loaded: {len(rule_files)} files")
        except Exception as e:
            logger.error(f"Failed to compile YARA rules: {e}")
            self.compiled_rules = None

    def scan_file(self, file_path: str, timeout: int = 10) -> Dict:
        """
        فحص ملف ضد جميع القواعد
        Returns: {
            'matches': [...],
            'matched_count': int,
            'severity': str,
        }
        """
        if not self.available:
            return {
                'error': 'YARA not installed',
                'matches': [],
                'matched_count': 0,
            }

        if not self.compiled_rules:
            return {
                'error': 'No rules loaded',
                'matches': [],
                'matched_count': 0,
            }

        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return {
                'error': 'File not found',
                'matches': [],
                'matched_count': 0,
            }

        # تخطي الملفات الكبيرة (>100MB)
        if path.stat().st_size > 100 * 1024 * 1024:
            return {
                'error': 'File too large (>100MB)',
                'matches': [],
                'matched_count': 0,
            }

        try:
            matches = self.compiled_rules.match(str(path), timeout=timeout)

            # تحويل النتائج لصيغة مفيدة
            results = []
            max_severity = "LOW"
            severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

            for match in matches:
                meta = match.meta if hasattr(match, 'meta') else {}
                severity = meta.get('severity', 'LOW')
                description = meta.get('description', 'No description')

                results.append({
                    'rule': match.rule,
                    'description': description,
                    'severity': severity,
                    'tags': list(match.tags) if hasattr(match, 'tags') else [],
                    'matched_strings': [
                        str(s[2], 'utf-8', errors='ignore')[:80]
                        for s in (match.strings or [])[:5]
                    ],
                })

                # تتبع أعلى severity
                if severity_order.get(severity, 0) > severity_order.get(max_severity, 0):
                    max_severity = severity

            return {
                'file': str(path),
                'matches': results,
                'matched_count': len(results),
                'severity': max_severity if results else 'NONE',
                'is_malicious': len(results) > 0,
            }

        except yara.TimeoutError:
            return {
                'error': 'Scan timeout',
                'matches': [],
                'matched_count': 0,
            }
        except Exception as e:
            logger.error(f"YARA scan failed for {file_path}: {e}")
            return {
                'error': str(e),
                'matches': [],
                'matched_count': 0,
            }

    def scan_process(self, pid: int) -> Dict:
        """
        فحص ذاكرة عملية (Windows/Linux)
        يتطلب صلاحيات Admin
        """
        if not self.available or not self.compiled_rules:
            return {'error': 'YARA unavailable', 'matches': []}

        try:
            matches = self.compiled_rules.match(pid=pid)
            results = [
                {
                    'rule': m.rule,
                    'severity': m.meta.get('severity', 'LOW') if hasattr(m, 'meta') else 'LOW',
                }
                for m in matches
            ]
            return {
                'pid': pid,
                'matches': results,
                'matched_count': len(results),
                'is_malicious': len(results) > 0,
            }
        except Exception as e:
            logger.error(f"Process scan failed for PID {pid}: {e}")
            return {'error': str(e), 'matches': []}

    def batch_scan_files(self, file_paths: List[str]) -> List[Dict]:
        """فحص مجموعة ملفات"""
        results = []
        for file_path in file_paths:
            result = self.scan_file(file_path)
            if result.get('matched_count', 0) > 0:
                results.append(result)
        return results


# Singleton instance
yara_engine = YaraEngine()
