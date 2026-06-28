#C01_DataTables.py
"""
This file stores static cockpit configuration used by trend and volatility calculations. 
The values define market lists, score bounds, volatility mappings, and amplifier tables used by the calculation layer.
These tables are later unpacked and used in the 'amp' calculation, which gives each state its dependent weight.
"""
"""________________________________________________________________________________________________________________"""
from dataclasses import dataclass
"""________________________________________________________________________________________________________________"""
"""
This dataclass stores lower, neutral, and upper bounds for one score component. 
It gives normalization functions a clear typed input.
"""
@dataclass  
class ComponentBounds:
    min: float
    max: float
"""________________________________________________________________________________________________________________"""
"""
This dataclass stores cockpit scoring weights. 
It keeps risk, direction, volatility, term, and gear settings in one structured object.
"""
@dataclass
class Weights:
    sentiment: float
    elliott: float
    vola: float
    market_profile: float
    trend: float
    equity: float
    term_structure: float   
"""________________________________________________________________________________________________________________"""
"""
This dataclass stores gear scaling thresholds and multipliers. 
It supports translating market conditions into sizing context.
"""
@dataclass
class GearScale:
    first: float
    second: float
    third: float
    fourth: float
    fifth: float
"""________________________________________________________________________________________________________________"""
"""
These are amplifiers for trend and volatility-strength calculations. 
"""
SENTIMENT_TREND_AMPLIFIER = [
    {"trend": "Long",  "support": "Positive", "amp":  1},
    {"trend": "Short", "support": "Negative", "amp":  -1},
    {"trend": "Long",  "support": "Negative", "amp":  0},
    {"trend": "Short", "support": "Positive", "amp":  0},
    {"trend": "Neutral", "support": "Neutral", "amp":  0},
]

VOL_SENTIMENT_TREND_AMPLIFIER = [
    {"vola": "Up",  "support": "Positive", "amp":  1},
    {"vola": "Down", "support": "Negative", "amp":  -1},
    {"vola": "Mixed",  "support": "Neutral", "amp":  0},

    {"vola": "Up",  "support": "Neutral", "amp":  0},
    {"vola": "Down", "support": "Neutral", "amp":  0},
    {"vola": "Mixed",  "support": "Negative", "amp":  0},

    {"vola": "Up",  "support": "Negative", "amp":  0},
    {"vola": "Down", "support": "Positive", "amp":  0},
    {"vola": "Mixed",  "support": "Positive", "amp":  0},   
]

OPENING_DRIVE_AMPLIFIER = [
    {"opening_drive_state": "Up",   "trend": "Long",  "amp":  1},
    {"opening_drive_state": "Down", "trend": "Short", "amp":  -1},
    {"opening_drive_state": "Up",   "trend": "Short", "amp": 0},
    {"opening_drive_state": "Down", "trend": "Long",  "amp": 0},
]

ELLIOTT_AMPLIFIER = [
    {"wave": "Impulswelle",    "trend": "Long",  "amp":  1},
    {"wave": "Impulswelle",    "trend": "Short", "amp": -1},
    {"wave": "Korrekturwelle", "trend": "Long",  "amp":  0},
    {"wave": "Korrekturwelle", "trend": "Short", "amp":  0},
]

"""________________________________________________________________________________________________________________"""

DEFAULT_VOLA_INSTR_WEIGHTS = {"vix": 1.0, "vvix": 1.0, "cor1m": 1.0}                                                #|Instrument weights for each Vol indece (Only for S&P)

"""________________________________________________________________________________________________________________"""
"""
Searches an amplifier table for the row matching the provided conditions. 
The returned amp value adjusts a score when sentiment, volatility, or profile context supports the selected direction.
"""
def lookup_amplifier(table, **conditions) -> float:
    for row in table:
        if all(row.get(k) == v for k, v in conditions.items()):
            return float(row["amp"])
    return 0.0
"""________________________________________________________________________________________________________________"""
"""
Volatility State API Helpers
Timeframeweights and Market Vol indices are stored here
"""
TF_WEIGHTS = {"1H": 0.15, "4H": 0.20, "D": 0.30, "W": 0.35}
MARKET_VOL_INDEX = {
    "MES1!": {"VIX": "VIX-USD", "VVIX": "VVIX-USD", "COR1M": "COR1M-USD"},
    "MNQ1!": {"VIX": "VXN-USD"},
    "MGC1!": {"VIX": "GVZ-USD"},
}
TF_PER_INDICE = {
 "VIX-USD": ["1H","4H","D", "W"],
 "VVIX-USD": ["1H","4H","D", "W"],
 "COR1M-USD": ["1H","4H","D", "W"],
 "VXN-USD": ["1H","4H","D", "W"],
 "GVZ-USD": ["1H","4H","D", "W"],
 }
"""________________________________________________________________________________________________________________"""
"""
Market-Selections generally(e.g. Cockpit.py, State.py)
"""
MARKETS = ["MES1!", "MGC1!", "MNQ1!"]
"""________________________________________________________________________________________________________________"""
"""
This is the Log-tolerance on which Changes in the Scores are detected
When there are notable changes above this tolerance, a log is written.
"""
LOG_TOL = 1e-6
"""________________________________________________________________________________________________________________"""
"""
Sentiment_weights
"""
SENT_WEIGHTS = {
    "aaii": 0.25,
    "fng": 0.25,
    "under": 0.25,
    "vola": 0.25,
}
"""________________________________________________________________________________________________________________"""
SMA_LENGTHS = {"sma1" : 20, "sma2": 30, "sma3": 50} 

