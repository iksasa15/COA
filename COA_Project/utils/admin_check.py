"""
Admin Privileges Checker
========================
Ensures the tool runs with required system privileges
"""

import os
import sys
import ctypes


def is_admin() -> bool:
    """
    يتحقق إذا كان البرنامج يعمل بصلاحيات المسؤول
    Returns: True إذا كان Admin، False خلاف ذلك
    """
    try:
        if os.name == 'nt':  # Windows
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        # macOS / Linux: لا نطلب root — جمع ps/netstat وغيره يعمل للمستخدم الحالي.
        # طلب geteuid() == 0 كان يمنع التشغيل العادي على macOS.
        return True
    except Exception:
        return False


def require_admin():
    """
    يجبر البرنامج على التوقف إذا لم يكن Admin
    يعرض رسالة واضحة للمستخدم
    """
    if not is_admin():
        print("\n" + "=" * 60)
        print("  ⚠️  ADMIN PRIVILEGES REQUIRED  ⚠️")
        print("=" * 60)
        print("\n  C.O.A requires Administrator privileges to:")
        print("    • Scan network connections")
        print("    • Monitor running processes")
        print("    • Execute security commands\n")
        if os.name == 'nt':
            print("  👉 Open Command Prompt or PowerShell as Administrator and try again.\n")
        else:
            print("  👉 Run with elevated privileges if you need full system visibility, e.g.:\n")
            print("       sudo python main.py\n")
        print("=" * 60 + "\n")
        sys.exit(1)


def elevate_privileges():
    """
    يحاول إعادة تشغيل البرنامج بصلاحيات Admin (Windows فقط)
    """
    if os.name == 'nt' and not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable,
                " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        except Exception as e:
            print(f"Failed to elevate: {e}")
            sys.exit(1)
