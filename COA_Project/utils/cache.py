"""
Smart Caching System with TTL
=============================
Speeds up repeat scans by caching expensive operations
"""

import time
import hashlib
from functools import wraps
from typing import Any, Callable, Dict, Optional
from threading import Lock


class SmartCache:
    """
    Cache ذكي مع Time-To-Live لتسريع العمليات المتكررة
    يدعم thread-safe للاستخدام مع async
    """

    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: مدة بقاء الـ cache بالثواني (default: 5 دقائق)
        """
        self._cache: Dict[str, Dict] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def _make_key(self, *args, **kwargs) -> str:
        """توليد مفتاح فريد من الـ arguments"""
        key_str = f"{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """استرجاع قيمة من الـ cache"""
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            entry = self._cache[key]
            if time.time() > entry['expires_at']:
                del self._cache[key]
                self.misses += 1
                return None

            self.hits += 1
            return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """حفظ قيمة في الـ cache"""
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + (ttl or self.default_ttl),
            }

    def clear(self):
        """مسح الـ cache بالكامل"""
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict:
        """إحصائيات الأداء"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'cached_items': len(self._cache),
        }

    def cached(self, ttl: Optional[int] = None):
        """Decorator للدوال - تلقائياً يحفظ النتائج"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                key = f"{func.__name__}:{self._make_key(*args, **kwargs)}"
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value

                result = func(*args, **kwargs)
                self.set(key, result, ttl)
                return result
            return wrapper
        return decorator


# Singleton cache instance for the entire app
global_cache = SmartCache(default_ttl=300)
