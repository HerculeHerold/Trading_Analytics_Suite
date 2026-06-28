from __future__ import annotations
#RO2_Math_Functions.py
"""
This file contains math helpers for market comparison and volatility measurement. 
The functions below support beta, correlation, moving averages, and ATR-style calculations.
    -Beta
    -Correlation
    -ATR
"""
"""____________________________________________________________________________________________________"""
import math
from typing import Iterable, Sequence
"""____________________________________________________________________________________________________"""
"""
Returns the latest values from a sequence and limits statistical calculations to the requested lookback. 
This keeps beta, correlation, and indicator helpers focused on recent data.
"""
def _last_n(values: Iterable[float], length: int) -> list[float]:
    data = list(values)
    if length <= 0:
        return []
    return data[-length:]                                                                              #|give me the last values until length
"""____________________________________________________________________________________________________"""
"""
Calculates the arithmetic average of the provided values. 
It is kept as a small helper so the statistical functions use the same base calculation.
"""
def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)
"""____________________________________________________________________________________________________"""
"""
Calculates sample variance for a sequence of values. 
It measures how widely returns move around their own average.
"""
def _variance(values: Sequence[float]) -> float:
    mu = _mean(values)
    return sum((v - mu) ** 2 for v in values) / len(values)
"""____________________________________________________________________________________________________"""
"""
Calculates covariance between two value sequences. 
The result shows whether two markets tend to move together or in opposite directions.
"""
def _covariance(x: Sequence[float], y: Sequence[float]) -> float:
    mu_x = _mean(x)
    mu_y = _mean(y)
    return sum((a - mu_x) * (b - mu_y) for a, b in zip(x, y)) / len(x)                                 #|split into tuples(zip) and for each a and b do that
"""____________________________________________________________________________________________________"""
"""
Calculates market beta from two aligned return series. 
It compares covariance with benchmark variance to estimate how strongly one market reacts to another.
"""
def beta(x: Sequence[float], y: Sequence[float], length: int) -> float | None:
    if length <= 0:
        return None
    if len(x) < length or len(y) < length:
        return None
    xs = _last_n(x, length)                                                                            #|List of floats
    ys = _last_n(y, length)
    var_x = _variance(xs)
    if var_x == 0:
        return None                                                                                    #|Defense
    cov_xy = _covariance(xs, ys)
    return cov_xy / var_x
"""____________________________________________________________________________________________________"""
"""
Calculates the correlation coefficient between two aligned return series. 
It returns None when there is not enough data or when one series has no useful movement.
"""
def correlation(x: Sequence[float], y: Sequence[float], length: int) -> float | None:
    if length <= 0:
        return None
    if len(x) < length or len(y) < length:
        return None                                                                                    #|Defense
    xs = _last_n(x, length)                                                 
    ys = _last_n(y, length)                                                                            #|Same structure as in beta
    var_x = _variance(xs)
    var_y = _variance(ys)
    if var_x == 0 or var_y == 0:                                                                       #|Defense
        return None
    cov_xy = _covariance(xs, ys)
    return cov_xy / math.sqrt(var_x * var_y)                                                           #|
"""____________________________________________________________________________________________________"""
"""
Builds a simple moving average list from raw values. 
Early rows stay empty until enough data exists for the selected window.
"""
def _sma(values: Sequence[float], length: int) -> list[float]: 
    out = []
    for i in range(length - 1, len(values)):                                                           #|Look for full window
        window = values[i - length + 1 : i + 1]                                                        #|List of length(size)-characters
        out.append(sum(window) / length)
    return out
"""____________________________________________________________________________________________________"""
"""
Builds a Wilder-style smoothed moving average list. 
It starts with a simple average and then updates each new value with recursive smoothing.
"""
def _rma(values: Sequence[float], length: int) -> list[float]:
    if length <= 0 or len(values) < length:
        return []                                                                                       #|Safety 
    out = []
    seed = sum(values[:length]) / length                                                                #|Mean
    out.append(seed)
    for v in values[length:]:
        seed = (seed * (length - 1) + v) / length
        out.append(seed)
    return out
"""____________________________________________________________________________________________________"""
"""
Builds an exponential moving average list from raw values. 
Newer values receive more weight after the initial window is available.
"""
def _ema(values: Sequence[float], length: int) -> list[float]:
    if length <= 0 or len(values) < length:
        return []                                                                                       #|Safety 
    alpha = 2 / (1 + length)                                                                            #|Smoothing Factor
    initial_value = sum(values[:length])/length   
    out = [initial_value]                                                                               #|Add SMA as basis point 
    current_ema = initial_value                                                                
    for v in values[length:]:
        current_ema = v * alpha + current_ema * (1 - alpha)                                             #|Formula implemented see above
        out.append(current_ema) 
    return out 
"""____________________________________________________________________________________________________"""
"""
Calculates ATR by first creating true-range values from high, low, and close data. 
It then smooths those ranges with the RMA helper to match common trading-platform ATR behavior.
"""
def atr_true_range_rma(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    shortterm_atr_l: int,
    longterm_atr_l: int,
) -> tuple[float | None, float | None]:
    if shortterm_atr_l <= 0 or longterm_atr_l <= 0:                                                    #|Defense
        return None, None
    if len(highs) < 2 or len(lows) < 2 or len(closes) < 2:
        return None, None
    if len(highs) != len(lows) or len(highs) != len(closes):
        return None, None                                                                              #|Defense
    true_ranges = []
    #Actual Calc
    for i in range(1, len(highs)):                                                                     #|len(x) as bound
        high = highs[i]
        low = lows[i]
        prev_close = closes[i - 1]                                                                     #|We always want the previous close(Gaps)
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)                                                                         #|True Range for each candle
    shortterm_atr = _rma(true_ranges, shortterm_atr_l)
    longterm_atr = _rma(true_ranges, longterm_atr_l)
    atr_shortterm_val = shortterm_atr[-1] if shortterm_atr else None                                   #|[-1] last calculated ATR
    atr_longterm_val = longterm_atr[-1] if longterm_atr else None
    return atr_shortterm_val, atr_longterm_val

