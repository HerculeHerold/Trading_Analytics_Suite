#RO2_Calc.py
"""
This module performs risk-management calculations and trade insertion preparation. 
It computes ATR inputs, return alignment, stop values, and payloads for open trades.
"""
"""____________________________________________________________________________________________________"""
import pandas as pd
import time
from Pages.Calculation.Content.Riskmanagement.R02_Math_Functions import atr_true_range_rma
from Pages.Calculation.Content.Cockpit.C01_State_Logging import get_state
"""____________________________________________________________________________________________________"""
"""
Rounds a price or distance to the nearest valid market step. 
This keeps stop, target, and price calculations aligned with contract tick sizes.
"""
def round_to_step(x: float, step: float) -> float:
    if step == 0:                                                                                       #|No decimal steps
        return x
    return round(x / step) * step
"""____________________________________________________________________________________________________"""
"""
Converts the market label used in the UI into the symbol used by market-data queries. 
Unknown labels fall back to the original value so custom symbols can still pass through.
"""
def market_to_symbol(market: str) -> str:
    base = market.replace("1!", "").replace("!", "")
    return f"{base}-USD"
"""____________________________________________________________________________________________________"""
"""
Calculates short-term and long-term ATR values from high, low, and close rows. 
The function builds true ranges and smooths them so the risk page can estimate current volatility.
"""
def compute_atr(  
    rows: list[float],                                                                                  
    shortterm_atr_l: int,
    longterm_atr_l: int,
    include_latest: bool = True,
) -> tuple[float | None, float | None]:
    if not rows:                                                                                        #|Again defense if Rows are empty
        return None, None
    if not include_latest and len(rows) > 1:
        rows = rows[1:]                                                                                 #|Only fetching latest bar(On close)
    ordered = list(reversed(rows))
    highs = [float(r[0]) for r in ordered]                                                              #|Fetched: High Low Close Index per row
    lows = [float(r[1]) for r in ordered]
    closes = [float(r[2]) for r in ordered]
    return atr_true_range_rma(highs, lows, closes, shortterm_atr_l, longterm_atr_l)

"""____________________________________________________________________________________________________"""
"""
Turns close-price rows into percentage return values for correlation and beta calculations. 
It sorts the market data by time and keeps only the requested lookback window.
"""
def returns_series(lookback: int, rows: pd.Series, corr_bar_size: str) -> pd.Series:
    df = pd.DataFrame(rows, columns=["bar_time", "close", "bar_size"])
    df["bar_time"] = pd.to_datetime(df["bar_time"], errors="coerce")                                    #|Write errors as None
    df = df.dropna(subset=["bar_time"])                                                                 #|Drop NaN or N/A rows 
    if df.empty:
        return pd.Series(dtype=float)
    if (df["bar_size"] == corr_bar_size).any():                                                         #|Controlling if Bar_size is correct
        df = df[df["bar_size"] == corr_bar_size].copy()                                                 #|bar_time as index
        return df.set_index("bar_time")["close"].sort_index()
    series = df.set_index("bar_time")["close"].sort_index()                                             #|Indexing to bar_time to resample
    series = series.resample("60min").last().dropna()                                                   #|Group 60min buckets (last close)
    if series.empty:
        return pd.Series(dtype=float)
    rets = series.pct_change().dropna()                                                                 #|Percentage changes from series
    if lookback > 0:
        return rets.tail(lookback)                                                                      #|lookback for series
    return rets
"""____________________________________________________________________________________________________"""
"""
Aligns two return series on matching timestamps before statistical comparison. 
This avoids comparing returns from different bars or missing time periods.
"""
def align_returns(a: pd.Series, b: pd.Series, lookback: int) -> tuple[list[float], list[float]]:
    if a.empty or b.empty:
        return [], []                                                                                   #|Defense
    joined = pd.concat([a, b], axis=1, join="inner").dropna()                                           #|concat sets lists side by side, axis=1 means stacked on colummns, 
    if joined.empty:                                                                                    #|innerjoin means here only keep values that exist in both a and b
        return [], []                                                                                   #|Defense
    if lookback > 0:
        joined = joined.tail(lookback)
    return joined.iloc[:, 0].tolist(), joined.iloc[:, 1].tolist()                                       #|Returns to list index 0 and 1 and makes a list of them
"""____________________________________________________________________________________________________"""
"""
Combines loser MAE, ATR ratio, and short-term ATR into a suggested stop distance. 
The result gives the risk page a market-aware stop-loss estimate.
"""
def stop_loss_calc(mae_l: float, atr_ratio: float, atr_shortterm: float) -> float:
    return max(mae_l * atr_ratio, atr_shortterm)                                                      #|Stop Loss Calc
"""____________________________________________________________________________________________________"""
"""
Converts a planned price level into monetary trade value. 
It accounts for long or short direction, entry price, 
and tick value so the trading plan can show risk and reward in account terms.
"""
def tradingplan_value(x: float, entry: float, tick_value:float, direction:str) -> float:
    if direction.lower().startswith("short"):                                                           #|Tradingplan lagic per Direction
        return round_to_step(entry - x, tick_value)
    return round_to_step(entry + x, tick_value)
"""____________________________________________________________________________________________________"""
"""
Builds the complete payload for a currently open trade and stores it through the database layer. 
It combines manual trade inputs, cockpit state values, and calculated scores for later tracking.
"""
def insert_trade(
    trade_Id:str,
    entry: float,
    stop_loss: float,
    breakeven: float,
    trailing_start: float,
    take_profit: float,
    st_atr: float,
    lt_atr: float,
    strategy: str,
    market: str,
    size: int,
    direction: str,
    min_risk: float,
    max_risk: float,
    real_risk_ticks: int,
    real_risk_usd: float,
    create_time: str
) -> dict[str, float | int | str]:                                                                       #|Parameters
    return {
        #Trade specific variables
        "trade_id":f"{market}_{int(time.time())}",
        "market": market,
        "size": size,
        "direction": direction,
        "strategy" : strategy,
        "entry": entry,
        "stop": tradingplan_value(-stop_loss),
        "breakeven": tradingplan_value(breakeven),
        "trailingstart": tradingplan_value(trailing_start),
        "profit": tradingplan_value(take_profit),
        "real_risk_ticks":real_risk_ticks,
        "real_risk_usd":real_risk_usd,
        "created_at":create_time,
        #Other veriables 
        "min_risk": min_risk,
        "max_risk": max_risk,
        "st_atr": st_atr,
        "lt_atr": lt_atr,
        #States
        "gear": get_state(market).gear,
        "Conviction_state": get_state(market).conviction_state,
        "Trend_strength_state": get_state(market).trend_strength_state,
        "Vola_strength_state": get_state(market).vola_strength_state,
        "trend_state": get_state(market).trend_state,
        "Vola_state": get_state(market).vol_state,
        "termstructure_state": get_state(market).term_structure_state,
        #Scores
        "Trend_Score": get_state(market).Trend_score,
        "Vola_Score": get_state(market).Vola_Score,
        "Conviction_Score": get_state(market).conviction,
        "Trend_strength_score":get_state(market).trend_strength,
        "Vola_strength_score": get_state(market).vol_strength,
        "term_structure_score": get_state(market).term_structure_score  
    }                                                                                                  #|Dictionary for all inputs
"""____________________________________________________________________________________________________"""

