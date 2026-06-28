#A05_Datatables.py
"""
This module defines static analysis table metadata. 
It keeps shared labels and configuration values separate from calculation and UI code.
"""
"""________________________________________________________________________________________________""" 
TAG_OPTIONS = {
    "vola_state": ["Mixed", "Up", "Down"],
    "term_structure_state": ["Backwardation", "Contango", "flat"],
    "gear_state": ["Gear 1", "Gear 2", "Gear 3", "Gear 4", "Gear 5"],
    "strategy": ["Vola-Momentum", "Vola-Reversion"],
    "conviction_state": ["High Conviction", "Moderate Conviction", "Low Conviction"],
    "trend_strength_state": [
        "Positive Short Trendstrength",
        "Positive Long Trendstrength",
        "Low Trendstrength",
    ],
    "vola_strength_state": ["High Vola-Strength", "Moderate Vola-Strength", "Low Vola-Strength"],
    "trend_state": ["Long", "Short", "Neutral"],
    "direction": ["Long", "Short"],
    "market": ["MES1!", "MGC1!", "MCL1!", "MNQ1!"],
}
REQUIRED_COLS = ["entry", "exits", "size", "direction", "point_value", "stop"]
"""________________________________________________________________________________________________""" 
WIN_THRESHOLD = float(50.0)
LOSS_THRESHOLD = float(50.0)
