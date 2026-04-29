"""
VirusTotal API Integration
==========================
Checks files and IPs against VirusTotal's global malware database
Requires free API key from: https://www.virustotal.com/gui/join-us

Features:
- File hash checking (SHA256)
- IP reputation check
- Domain reputation check
- Local caching to respect rate limits (4 req/min for free tier)
"""

import hashlib
import os
import requests
from pathlib import Path
from typing import Dict, Optional
from utils.cache import global_cache
from utils.logger import logger


class VirusTotalClient:
    """
    VirusTotal API v3 client
    Free tier: 4 requests/minute, 500 requests/day
    """

    BASE_URL = "https://www.virustotal.com/api/v3"
    RATE_LIMIT_CACHE_TTL = 3600  # ساعة - لتجنب استهلاك الحصة

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: مفتاح VirusTotal (أو يُقرأ من متغير VT_API_KEY)
        """
        self.api_key = api_key or os.getenv("VT_API_KEY", "")
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning("VirusTotal disabled - no API key provided")

        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "x-apikey": self.api_key,
                "Accept": "application/json",
            })

    @staticmethod
    def compute_file_hash(file_path: str) -> Optional[str]:
        """حساب SHA256 لملف"""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return None

        try:
            sha256 = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            return None

    def check_file(self, file_path: str) -> Dict:
        """
        فحص ملف بصيغة hash ضد VirusTotal
        Returns: {
            'found': bool,
            'malicious': int,
            'suspicious': int,
            'harmless': int,
            'detection_ratio': str,
            'threat_names': list,
        }
        """
        if not self.enabled:
            return {'error': 'VirusTotal not configured', 'found': False}

        file_hash = self.compute_file_hash(file_path)
        if not file_hash:
            return {'error': 'Could not compute hash', 'found': False}

        return self._check_hash(file_hash)

    @global_cache.cached(ttl=3600)
    def _check_hash(self, file_hash: str) -> Dict:
        """فحص hash مع caching"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/files/{file_hash}",
                timeout=10,
            )

            if response.status_code == 404:
                return {'found': False, 'message': 'File not in VT database'}

            if response.status_code == 401:
                logger.error("VirusTotal: Invalid API key")
                return {'error': 'Invalid API key', 'found': False}

            if response.status_code == 429:
                logger.warning("VirusTotal: Rate limit exceeded")
                return {'error': 'Rate limit exceeded', 'found': False}

            response.raise_for_status()
            data = response.json()

            stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
            results = data.get('data', {}).get('attributes', {}).get('last_analysis_results', {})

            # استخراج أسماء التهديدات المكتشفة
            threat_names = []
            for engine, result in results.items():
                if result.get('category') == 'malicious':
                    threat_names.append(f"{engine}: {result.get('result', 'Unknown')}")

            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            harmless = stats.get('harmless', 0)
            undetected = stats.get('undetected', 0)
            total = malicious + suspicious + harmless + undetected

            return {
                'found': True,
                'malicious': malicious,
                'suspicious': suspicious,
                'harmless': harmless,
                'detection_ratio': f"{malicious}/{total}" if total > 0 else "0/0",
                'threat_names': threat_names[:5],  # أول 5 تهديدات
                'is_malicious': malicious >= 3,  # 3+ engines = confirmed malicious
                'confidence': self._calculate_vt_confidence(malicious, total),
            }

        except requests.exceptions.Timeout:
            return {'error': 'VirusTotal timeout', 'found': False}
        except Exception as e:
            logger.error(f"VirusTotal error: {e}")
            return {'error': str(e), 'found': False}

    def check_ip(self, ip: str) -> Dict:
        """فحص سمعة IP"""
        if not self.enabled:
            return {'error': 'VirusTotal not configured', 'found': False}

        return self._check_ip_cached(ip)

    @global_cache.cached(ttl=3600)
    def _check_ip_cached(self, ip: str) -> Dict:
        """فحص IP مع caching"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/ip_addresses/{ip}",
                timeout=10,
            )

            if response.status_code == 404:
                return {'found': False}

            if response.status_code != 200:
                return {'error': f'HTTP {response.status_code}', 'found': False}

            data = response.json()
            stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
            country = data.get('data', {}).get('attributes', {}).get('country', 'Unknown')
            asn_owner = data.get('data', {}).get('attributes', {}).get('as_owner', 'Unknown')

            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)

            return {
                'found': True,
                'ip': ip,
                'country': country,
                'as_owner': asn_owner,
                'malicious': malicious,
                'suspicious': suspicious,
                'is_malicious': malicious >= 2,
                'confidence': self._calculate_vt_confidence(malicious, 90),
            }

        except Exception as e:
            logger.error(f"VirusTotal IP check error: {e}")
            return {'error': str(e), 'found': False}

    @staticmethod
    def _calculate_vt_confidence(malicious: int, total: int) -> str:
        """حساب مستوى الثقة بناءً على عدد engines المكتشفة"""
        if total == 0:
            return 'UNKNOWN'
        ratio = malicious / total
        if ratio >= 0.3 or malicious >= 10:
            return 'VERY_HIGH'
        elif ratio >= 0.15 or malicious >= 5:
            return 'HIGH'
        elif ratio >= 0.05 or malicious >= 2:
            return 'MEDIUM'
        return 'LOW'


# Singleton instance
vt_client = VirusTotalClient()
