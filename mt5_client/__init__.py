"""
Reusable MetaTrader5 client utilities.

Public API (lazy-imported):
- MT5Client: a context-managed client wrapper for MT5 initialization/login and data fetching
- timeframe_from_str: map timeframe strings like 'M1','M5','H1','D1','W1','MN1' to MT5 constants
"""

from typing import Any

__all__ = ["MT5Client", "timeframe_from_str", "AVAILABLE_TIMEFRAMES"]


def __getattr__(name: str) -> Any:
    # Lazy import to avoid importing heavy dependencies at package import time (e.g., pandas/numpy)
    if name == "MT5Client":
        from .client import MT5Client  # type: ignore
        return MT5Client
    if name in ("timeframe_from_str", "AVAILABLE_TIMEFRAMES"):
        from .periods import timeframe_from_str, AVAILABLE_TIMEFRAMES  # type: ignore
        return timeframe_from_str if name == "timeframe_from_str" else AVAILABLE_TIMEFRAMES
    raise AttributeError(name)
