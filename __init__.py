"""
pynamuh - Python wrapper for NH Investment & Securities WMCA API
"""

__version__ = "0.1.0"
__author__ = "pynamuh contributors"
__license__ = "MIT"


import sys
# Windows 환경 확인
if sys.platform != "win32":
    raise ImportError("이 모듈은 Windows 환경에서만 실행 가능합니다.")
    sys.exit(1)

# 32비트 Python 확인
import platform
if platform.architecture()[0] != "32bit":
    print(f"현재 Python: {platform.architecture()[0]}")
    print(f"wmca.dll 요구사항: 32bit")
    print("\n32비트 Python을 설치하고 다음과 같이 실행하세요:")
    print("  py -3.11-32 wmca_login_with_msg.py")
    print("=" * 70)
    raise ImportError("이 모듈은 32비트 Python에서만 실행 가능합니다.")

# Public API
from .wmca_agent import WMCAAgent


__all__ = [
    # Main API
    "WMCAAgent"
]
