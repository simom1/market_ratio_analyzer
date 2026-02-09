from typing import Dict, Iterable, List

try:
    import MetaTrader5 as mt5
except Exception:  # pragma: no cover - allow import where MT5 is unavailable
    mt5 = None  # type: ignore


# Mapping from common timeframe strings to MT5 timeframe constants
# Accept both upper and lower case
_TIMEFRAME_MAP: Dict[str, int] = {
    "M1": getattr(mt5, "TIMEFRAME_M1", 1),
    "M2": getattr(mt5, "TIMEFRAME_M2", 2),
    "M3": getattr(mt5, "TIMEFRAME_M3", 3),
    "M4": getattr(mt5, "TIMEFRAME_M4", 4),
    "M5": getattr(mt5, "TIMEFRAME_M5", 5),
    "M6": getattr(mt5, "TIMEFRAME_M6", 6),
    "M10": getattr(mt5, "TIMEFRAME_M10", 10),
    "M12": getattr(mt5, "TIMEFRAME_M12", 12),
    "M15": getattr(mt5, "TIMEFRAME_M15", 15),
    "M20": getattr(mt5, "TIMEFRAME_M20", 20),
    "M30": getattr(mt5, "TIMEFRAME_M30", 30),
    "H1": getattr(mt5, "TIMEFRAME_H1", 60),
    "H2": getattr(mt5, "TIMEFRAME_H2", 120),
    "H3": getattr(mt5, "TIMEFRAME_H3", 180),
    "H4": getattr(mt5, "TIMEFRAME_H4", 240),
    "H6": getattr(mt5, "TIMEFRAME_H6", 360),
    "H8": getattr(mt5, "TIMEFRAME_H8", 480),
    "H12": getattr(mt5, "TIMEFRAME_H12", 720),
    "D1": getattr(mt5, "TIMEFRAME_D1", 1440),
    "W1": getattr(mt5, "TIMEFRAME_W1", 10080),
    "MN1": getattr(mt5, "TIMEFRAME_MN1", 43200),
}

# Export a sorted list of available timeframe keys for help messages
AVAILABLE_TIMEFRAMES: List[str] = sorted(_TIMEFRAME_MAP.keys(), key=lambda x: (
    0 if x.startswith("M") else 1 if x.startswith("H") else 2 if x.startswith("D") else 3 if x.startswith("W") else 4,
    int(x[1:].replace("N", "100")) if x[0] in ("M", "H", "D", "W") else 999,
))


def timeframe_from_str(tf: str) -> int:
    """Map timeframe string like 'M1','H1','D1','W1','MN1' to MT5 constant.

    Raises ValueError if not supported.
    """
    key = tf.strip().upper()
    if key in _TIMEFRAME_MAP:
        return _TIMEFRAME_MAP[key]
    raise ValueError(f"Unsupported timeframe: {tf}. Supported: {', '.join(AVAILABLE_TIMEFRAMES)}")


def parse_timeframes(items: Iterable[str]) -> List[int]:
    """Parse an iterable of timeframe strings to MT5 constants."""
    return [timeframe_from_str(x) for x in items]
