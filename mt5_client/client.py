from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

import pandas as pd

try:
    import MetaTrader5 as mt5
except Exception as e:  # pragma: no cover
    mt5 = None  # type: ignore


@dataclass
class MT5Credentials:
    login: Optional[int] = None
    password: Optional[str] = None
    server: Optional[str] = None
    path: Optional[str] = None  # path to terminal, optional


class MT5Client:
    """
    Reusable MT5 client wrapper.

    Usage:
        with MT5Client(MT5Credentials(login=..., password=..., server=...)) as cli:
            df = cli.get_rates("XAUUSD.c", timeframe=mt5.TIMEFRAME_M5, count=500)
    """

    def __init__(self, creds: Optional[MT5Credentials] = None, *, ensure_initialized: bool = True):
        if mt5 is None:
            raise RuntimeError("MetaTrader5 package not available. Please install MetaTrader5 and run inside Windows with MT5 terminal.")
        self.creds = creds or MT5Credentials()
        self._initialized = False
        if ensure_initialized:
            self.initialize()

    def initialize(self) -> None:
        if self._initialized:
            return
        # Initialize terminal
        kwargs = {}
        if self.creds.path:
            kwargs["path"] = self.creds.path
        ok = mt5.initialize(**kwargs) if kwargs else mt5.initialize()
        if not ok:
            raise RuntimeError(f"MT5 initialize() failed: {mt5.last_error()}")
        # Optional login
        if self.creds.login and self.creds.password and self.creds.server:
            if not mt5.login(self.creds.login, password=self.creds.password, server=self.creds.server):
                raise RuntimeError(
                    f"MT5 login() failed: {mt5.last_error()}. "
                    "Ensure your login/server/password are correct and the account is available in the terminal."
                )
        self._initialized = True

    def shutdown(self) -> None:
        if self._initialized:
            mt5.shutdown()
            self._initialized = False

    def __enter__(self) -> "MT5Client":
        self.initialize()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        with contextlib.suppress(Exception):
            self.shutdown()

    # --- Data operations ---
    def ensure_symbol(self, symbol: str) -> None:
        info = mt5.symbol_info(symbol)
        if info is None:
            raise ValueError(f"Symbol not found: {symbol}")
        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                raise RuntimeError(f"Failed to select symbol: {symbol}")

    def get_rates(
        self,
        symbol: str,
        timeframe: int,
        *,
        count: Optional[int] = 1000,
        from_time_utc: Optional[datetime] = None,
        to_time_utc: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Fetch rates as a pandas DataFrame with a UTC datetime index named 'time'.

        If from_time_utc and to_time_utc are provided, uses copy_rates_range.
        Otherwise, uses copy_rates_from_pos with the specified count (default 1000).
        """
        self.ensure_symbol(symbol)
        if from_time_utc and to_time_utc:
            rates = mt5.copy_rates_range(symbol, timeframe, from_time_utc, to_time_utc)
        else:
            if count is None:
                raise ValueError("count must be provided when from/to range is not specified")
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            raise RuntimeError(f"Failed to fetch rates for {symbol}, timeframe {timeframe}: {mt5.last_error()}")
        if len(rates) == 0:
            return pd.DataFrame(columns=["time","open","high","low","close","tick_volume","spread","real_volume"]).set_index(pd.DatetimeIndex([], name="time"))
        df = pd.DataFrame(rates)
        # Convert 'time' (unix seconds) to UTC datetime
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df.set_index("time", inplace=True)
        return df[["open","high","low","close","tick_volume","spread","real_volume"]].sort_index()

    def get_multi_timeframes(
        self,
        symbol: str,
        timeframes: Iterable[int],
        *,
        count: Optional[int] = 1000,
        from_time_utc: Optional[datetime] = None,
        to_time_utc: Optional[datetime] = None,
    ) -> List[pd.DataFrame]:
        return [self.get_rates(symbol, tf, count=count, from_time_utc=from_time_utc, to_time_utc=to_time_utc) for tf in timeframes]

    # --- Convenience price getters ---
    def get_tick(self, symbol: str) -> pd.Series:
        """Get the latest tick for a symbol (bid/ask/last and time in UTC).

        Returns a pandas Series with index ['time','bid','ask','last','volume'].
        """
        self.ensure_symbol(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"Failed to fetch tick for {symbol}: {mt5.last_error()}")
        # tick.time is seconds since epoch; tick.time_msc may exist as ms
        ts = getattr(tick, "time_msc", None)
        if ts is not None and ts > 0:
            time_utc = pd.to_datetime(ts, unit="ms", utc=True)
        else:
            time_utc = pd.to_datetime(tick.time, unit="s", utc=True)
        data = {
            "time": time_utc,
            "bid": getattr(tick, "bid", float("nan")),
            "ask": getattr(tick, "ask", float("nan")),
            "last": getattr(tick, "last", float("nan")),
            "volume": getattr(tick, "volume", float("nan")),
        }
        return pd.Series(data)

    def get_last_price(self, symbol: str, price_type: str = "bid") -> float:
        """Get a single float price from the latest tick.

        price_type: one of 'bid', 'ask', 'last'. Default 'bid'.
        """
        s = self.get_tick(symbol)
        key = price_type.lower()
        if key not in ("bid", "ask", "last"):
            raise ValueError("price_type must be one of 'bid', 'ask', 'last'")
        val = float(s[key])
        return val

    def get_latest_close(self, symbol: str, timeframe: int) -> pd.Series:
        """Get the latest completed bar's close and OHLCV for a given timeframe.

        Returns a pandas Series with the OHLCV fields indexed by their names and with
        an attribute 'time' for the bar time in UTC.
        """
        self.ensure_symbol(symbol)
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"Failed to fetch latest bar for {symbol}, timeframe {timeframe}: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        row = df.iloc[0]
        # Return a Series with time and OHLCV fields
        return pd.Series({
            "time": row["time"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "tick_volume": float(row.get("tick_volume", float("nan"))),
            "spread": float(row.get("spread", float("nan"))),
            "real_volume": float(row.get("real_volume", float("nan"))),
        })

    # --- Account and trading operations ---
    def get_account_info(self) -> dict:
        """Return current account information as a dictionary."""
        info = mt5.account_info()
        if info is None:
            raise RuntimeError(f"Failed to fetch account info: {mt5.last_error()}")
        d = info._asdict() if hasattr(info, "_asdict") else dict(info.__dict__)
        # Normalize time to pandas UTC if present
        if "server" in d:
            d["server"] = str(d["server"])  # ensure str
        return d

    def get_positions(self, symbol: Optional[str] = None, magic: Optional[int] = None) -> List[dict]:
        """Get open positions; optionally filter by symbol and/or magic number."""
        self.ensure_symbol(symbol) if symbol else None
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions is None:
            # If no positions, MetaTrader5 returns () not None; None indicates error
            err = mt5.last_error()
            # Sometimes returns (1, 'No error') with None; treat as empty
            if err and err[0] != 0:
                raise RuntimeError(f"Failed to fetch positions: {err}")
            return []
        result: List[dict] = []
        for p in positions:
            p_dict = p._asdict() if hasattr(p, "_asdict") else dict(p.__dict__)
            # Filter by magic number if specified
            if magic is not None and p_dict.get("magic") != magic:
                continue
            result.append(p_dict)
        return result

    def send_market_order(
        self,
        symbol: str,
        volume: float,
        order_type: str,
        *,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        deviation: int = 20,
        comment: str = "",
        magic: int = 0,
    ) -> dict:
        """Place a market order (BUY or SELL).

        order_type: 'buy' or 'sell'
        magic: Magic number to identify the order (default 0)
        Returns the raw result dict from order_send.
        """
        self.ensure_symbol(symbol)
        t = order_type.strip().lower()
        if t not in ("buy", "sell"):
            raise ValueError("order_type must be 'buy' or 'sell'")
        
        # 获取品种信息，确定支持的filling mode
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise RuntimeError(f"Cannot get symbol info for {symbol}")
        
        # 根据品种支持的filling_mode选择合适的模式
        filling_mode = symbol_info.filling_mode
        
        # 优先级: IOC > FOK > Return
        if filling_mode & 2:  # 支持IOC
            type_filling = getattr(mt5, "ORDER_FILLING_IOC", 2)
        elif filling_mode & 1:  # 支持FOK
            type_filling = getattr(mt5, "ORDER_FILLING_FOK", 1)
        elif filling_mode & 4:  # 支持Return
            type_filling = getattr(mt5, "ORDER_FILLING_RETURN", 4)
        else:
            # 默认尝试FOK
            type_filling = getattr(mt5, "ORDER_FILLING_FOK", 0)
        
        action_type = getattr(mt5, "TRADE_ACTION_DEAL", 1)
        order_type_const = getattr(mt5, "ORDER_TYPE_BUY", 0) if t == "buy" else getattr(mt5, "ORDER_TYPE_SELL", 1)
        request = {
            "action": action_type,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type_const,
            "deviation": int(deviation),
            "comment": comment,
            "magic": int(magic),
            "type_filling": type_filling,
            "type_time": getattr(mt5, "ORDER_TIME_GTC", 0),
        }
        if sl is not None:
            request["sl"] = float(sl)
        if tp is not None:
            request["tp"] = float(tp)
        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
        res = result._asdict() if hasattr(result, "_asdict") else dict(result.__dict__)
        # status 10009/10008 are accepted; check retcode
        retcode = res.get("retcode")
        if retcode not in (
            getattr(mt5, "TRADE_RETCODE_DONE", 10009),
            getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", 10008),
            getattr(mt5, "TRADE_RETCODE_PLACED", 10016),
        ):
            raise RuntimeError(f"Order failed: retcode={retcode}, details={res}")
        return res

    def close_position(self, ticket: int, *, deviation: int = 20, comment: str = "") -> dict:
        """Close a position by ticket using a market deal in the opposite direction."""
        pos_list = mt5.positions_get(ticket=ticket)
        if pos_list is None or len(pos_list) == 0:
            raise RuntimeError(f"Position not found for ticket {ticket}: {mt5.last_error()}")
        p = pos_list[0]
        p_dict = p._asdict() if hasattr(p, "_asdict") else dict(p.__dict__)
        symbol = p_dict.get("symbol")
        volume = float(p_dict.get("volume", 0.0))
        order_type = p_dict.get("type")
        if order_type is None:
            raise RuntimeError("Position type not available")
        # Determine opposite order type
        type_buy = getattr(mt5, "POSITION_TYPE_BUY", 0)
        opposite_const = getattr(mt5, "ORDER_TYPE_SELL", 1) if order_type == type_buy else getattr(mt5, "ORDER_TYPE_BUY", 0)
        
        # 获取品种信息，确定支持的filling mode
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise RuntimeError(f"Cannot get symbol info for {symbol}")
        
        # 根据品种支持的filling_mode选择合适的模式
        filling_mode = symbol_info.filling_mode
        
        # 优先级: IOC > FOK > Return
        if filling_mode & 2:  # 支持IOC
            type_filling = getattr(mt5, "ORDER_FILLING_IOC", 2)
        elif filling_mode & 1:  # 支持FOK
            type_filling = getattr(mt5, "ORDER_FILLING_FOK", 1)
        elif filling_mode & 4:  # 支持Return
            type_filling = getattr(mt5, "ORDER_FILLING_RETURN", 4)
        else:
            # 默认尝试FOK
            type_filling = getattr(mt5, "ORDER_FILLING_FOK", 0)
        
        request = {
            "action": getattr(mt5, "TRADE_ACTION_DEAL", 1),
            "symbol": symbol,
            "volume": volume,
            "type": opposite_const,
            "position": int(ticket),
            "deviation": int(deviation),
            "comment": comment or "close_position",
            "type_filling": type_filling,
            "type_time": getattr(mt5, "ORDER_TIME_GTC", 0),
        }
        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
        res = result._asdict() if hasattr(result, "_asdict") else dict(result.__dict__)
        retcode = res.get("retcode")
        if retcode not in (
            getattr(mt5, "TRADE_RETCODE_DONE", 10009),
            getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", 10008),
            getattr(mt5, "TRADE_RETCODE_PLACED", 10016),
        ):
            raise RuntimeError(f"Close failed: retcode={retcode}, details={res}")
        return res

    def close_all_positions(self, symbol: Optional[str] = None, *, deviation: int = 20, magic: Optional[int] = None) -> List[dict]:
        """Close all open positions, optionally filtered by symbol and/or magic number. Returns list of results."""
        results: List[dict] = []
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        for p in positions or []:
            try:
                # Filter by magic number if specified
                if magic is not None:
                    p_dict = p._asdict() if hasattr(p, "_asdict") else dict(p.__dict__)
                    if p_dict.get("magic") != magic:
                        continue
                res = self.close_position(p.ticket, deviation=deviation)
                results.append(res)
            except Exception as e:
                results.append({"ticket": getattr(p, "ticket", None), "error": str(e)})
        return results

    def modify_position_sltp(
        self,
        ticket: int,
        *,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "",
    ) -> dict:
        """Modify stop loss and take profit for an open position.

        ticket: Position ticket to modify
        sl: New stop loss price (optional)
        tp: New take profit price (optional)
        comment: Optional comment for the modification
        Returns the raw result dict from order_send.
        """
        request = {
            "action": getattr(mt5, "TRADE_ACTION_SLTP", 6),
            "position": int(ticket),
            "comment": comment,
        }
        if sl is not None:
            request["sl"] = float(sl)
        if tp is not None:
            request["tp"] = float(tp)
        
        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
        res = result._asdict() if hasattr(result, "_asdict") else dict(result.__dict__)
        # Check retcode for success
        retcode = res.get("retcode")
        if retcode not in (
            getattr(mt5, "TRADE_RETCODE_DONE", 10009),
            getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", 10008),
            getattr(mt5, "TRADE_RETCODE_PLACED", 10016),
        ):
            raise RuntimeError(f"Modify SLTP failed: retcode={retcode}, details={res}")
        return res

    def partial_close(
        self,
        ticket: int,
        symbol: str,
        volume: float,
        *,
        deviation: int = 20,
        comment: str = "",
    ) -> dict:
        """Partially close a position by ticket.

        ticket: Position ticket to partially close
        symbol: Symbol of the position
        volume: Volume to close (in lots)
        deviation: Max price deviation in points
        comment: Optional comment
        Returns the raw result dict from order_send.
        """
        pos_list = mt5.positions_get(ticket=ticket)
        if pos_list is None or len(pos_list) == 0:
            raise RuntimeError(f"Position not found for ticket {ticket}: {mt5.last_error()}")
        p = pos_list[0]
        p_dict = p._asdict() if hasattr(p, "_asdict") else dict(p.__dict__)
        order_type = p_dict.get("type")
        if order_type is None:
            raise RuntimeError("Position type not available")
        
        # Determine opposite order type
        type_buy = getattr(mt5, "POSITION_TYPE_BUY", 0)
        opposite_const = getattr(mt5, "ORDER_TYPE_SELL", 1) if order_type == type_buy else getattr(mt5, "ORDER_TYPE_BUY", 0)
        
        # 获取品种信息，确定支持的filling mode
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise RuntimeError(f"Cannot get symbol info for {symbol}")
        
        # 根据品种支持的filling_mode选择合适的模式
        filling_mode = symbol_info.filling_mode
        
        # 优先级: IOC > FOK > Return
        if filling_mode & 2:  # 支持IOC
            type_filling = getattr(mt5, "ORDER_FILLING_IOC", 2)
        elif filling_mode & 1:  # 支持FOK
            type_filling = getattr(mt5, "ORDER_FILLING_FOK", 1)
        elif filling_mode & 4:  # 支持Return
            type_filling = getattr(mt5, "ORDER_FILLING_RETURN", 4)
        else:
            # 默认尝试FOK
            type_filling = getattr(mt5, "ORDER_FILLING_FOK", 0)
        
        request = {
            "action": getattr(mt5, "TRADE_ACTION_DEAL", 1),
            "symbol": symbol,
            "volume": float(volume),
            "type": opposite_const,
            "position": int(ticket),
            "deviation": int(deviation),
            "comment": comment or "partial_close",
            "type_filling": type_filling,
            "type_time": getattr(mt5, "ORDER_TIME_GTC", 0),
        }
        
        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
        res = result._asdict() if hasattr(result, "_asdict") else dict(result.__dict__)
        retcode = res.get("retcode")
        if retcode not in (
            getattr(mt5, "TRADE_RETCODE_DONE", 10009),
            getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", 10008),
            getattr(mt5, "TRADE_RETCODE_PLACED", 10016),
        ):
            raise RuntimeError(f"Partial close failed: retcode={retcode}, details={res}")
        return res

    def normalize_volume(self, symbol: str, volume: float) -> float:
        """Normalize volume to broker's volume step.

        symbol: Symbol to normalize for
        volume: Volume to normalize
        Returns normalized volume
        """
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return max(0.01, round(volume, 2))
            
            volume_min = float(getattr(info, "volume_min", 0.01))
            volume_max = float(getattr(info, "volume_max", 100.0))
            volume_step = float(getattr(info, "volume_step", 0.01))
            
            # Round to nearest step
            normalized = round(volume / volume_step) * volume_step
            # Clamp to min/max
            normalized = max(volume_min, min(volume_max, normalized))
            
            return normalized
        except Exception:
            return max(0.01, round(volume, 2))
