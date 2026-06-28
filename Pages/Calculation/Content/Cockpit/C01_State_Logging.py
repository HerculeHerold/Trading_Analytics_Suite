# state.py
"""
This module stores the current cockpit state for each market. 
Streamlit pages read and update these MarketState objects so market-specific inputs survive page reruns.
Via st.session state in the UI the Market Metrics where always met and stored here 
"""
"""________________________________________________________________________________________________"""
from dataclasses import dataclass, field
from Pages.Data.Content.Cockpit.C01_DataTables import MARKETS
"""________________________________________________________________________________________________"""
"""
This class stores the selected state for one market. 
It keeps trend, volatility, term-structure, and extra inputs together in a typed container.
"""
@dataclass
class MarketState:
    gear: int = 3
    vol_strength: float = 0.5
    trend_strength: float = 0.5
    conviction: float = 0.5
    trend_score: float = 0.5
    vola_score: float = 0.5
    term_structure_score: float = 0.5
    vol_state: str = "MIXED"
    trend_state: str = "NEUTRAL"
    conviction_state: str = "Moderate Conviction"
    trend_strength_state: str = "Moderate Trend-Strength"
    vola_strength_state: str = "Moderate Vola-Strength"
    term_structure_state: str = "Flat"
    strategy: str = "Vola-Reversion"
    gear_state: str = "Gear 3"
    inputs: dict[str, object] = field(default_factory=dict)

STATES: dict[str, MarketState] = {m: MarketState() for m in MARKETS}
"""________________________________________________________________________________________________""" 
"""
Returns the saved MarketState object for the requested market. 
If the market has not been used yet, it creates a fresh default state so the UI always has safe values to read.
"""
def get_state(market: str) -> MarketState:
    return STATES.setdefault(market, MarketState())

