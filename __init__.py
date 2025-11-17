"""
pynamuh - Python wrapper for NH Investment & Securities WMCA API
"""

__version__ = "0.1.0"
__author__ = "pynamuh contributors"
__license__ = "MIT"

# Public API
from .wmca_agent import WMCAAgent


__all__ = [
    # Main API
    "WMCAAgent"
]
