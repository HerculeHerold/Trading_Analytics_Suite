#C01_Set_States.py
"""
This module converts numeric cockpit scores into readable state labels. 
It uses simple thresholds so the UI can display consistent market, trend, and volatility states.
"""
"""________________________________________________________________________________________________________________"""
import pandas as pd
"""________________________________________________________________________________________________________________"""
"""
Maps a numeric term-structure risk score into a readable market state. Negative, neutral, and positive ranges become Contango, Flat, or Backwardation labels for the cockpit.
"""
def termstructure_state(tsrisk : float):
    if tsrisk <= -1/3:
        term_state = "Backwardation"
    if tsrisk >= 1/3:
        term_state = "Contango"
    if tsrisk < 1/3 and tsrisk > -1/3:
        term_state = "flat"
    return term_state
"""________________________________________________________________________________________________________________"""
"""
Maps the volatility strength score into a display label. 
The thresholds separate weak, moderate, and strong volatility pressure for the UI.
"""
def volstrength_state(vol_strength:float): 
    if vol_strength <= -1/3:
        vol_strength_state = "Low Vola-Strength"
    if vol_strength >= 1/3:
        vol_strength_state = "High Vola-Strength"
    if vol_strength < 1/3 and vol_strength > -1/3:
        vol_strength_state = "Moderate Vola-Strength"
    return vol_strength_state
"""________________________________________________________________________________________________________________"""
"""
Maps the trend strength score into a readable label. 
This turns the numeric trend-strength calculation into a state that can be shown in the cockpit.
"""
def Trendstrength_state(trend_strength: float):
    if trend_strength <= -1/3:
        trend_strength_state = "Positive Short Trend-Strength"
    if trend_strength >= 1/3:
        trend_strength_state = "Positive Long Trend-Strength"
    if trend_strength < 1/3 and trend_strength > -1/3:
        trend_strength_state = "Moderate Trend-Strength"
    return trend_strength_state
"""________________________________________________________________________________________________________________"""
"""
Maps the conviction score into a qualitative confidence label. 
It helps users understand whether the different market inputs are aligned or conflicting.
"""
def conviction_state(conviction_score:float):
    if conviction_score >= 2/3:
        conviction_state = "High Conviction"
    if conviction_score <= 1/3:
        conviction_state = "Low Conviction"
    if conviction_score <= 2/3 and conviction_score >= 1/3:
        conviction_state = "Moderate Conviction"
    return conviction_state
"""________________________________________________________________________________________________________________"""
"""
Maps the normalized volatility score into a cockpit state. 
Lower scores show calm volatility, middle scores show mixed conditions, and higher scores show elevated volatility.
"""
def Vol_state(vola_score:float):       
    if vola_score >= 2/3:
        vola_state = "Up"
    if vola_score <= 1/3:
        vola_state = "Down"
    if vola_score < 2/3 and vola_score > 1/3:
        vola_state = "Neutral"
    return vola_state
"""________________________________________________________________________________________________________________"""
"""
Maps the normalized trend score into a directional state. 
Scores below neutral are bearish, neutral values are balanced, and scores above neutral are bullish.
"""
def trend_state(Trend_score:float):
    if Trend_score <= -1/3:
        trend_state = "Short"
    if Trend_score >= 1/3:
        trend_state = "Long"
    else:
        trend_state = "Neutral"
    return trend_state
"""________________________________________________________________________________________________________________"""
"""
Returns the UI color connected to a state label. 
This keeps bullish, bearish, neutral, and risk-related badges visually consistent across pages.
"""
def state_color(state: str) -> str:
    if state == "Volatility Up":
        return "#2ecc71"
    if state == "Volatility Down":
        return "#e74c3c"
    return "#95a5a6"
"""________________________________________________________________________________________________________________"""
"""
Translates API-derived trend labels into the internal component labels used by the scoring tables. 
This lets automatic market-data states reuse the same database scores as manual selections.
"""
def api_state_to_component_state(state: str) -> str:
    if state == "Up":
        return "Up"
    if state == "Down":
        return "Down"
    return "Neutral"
"""________________________________________________________________________________________________""" 
"""
Classifies price position relative to three moving averages. 
The result describes whether the latest close is aligned bullish, bearish, or mixed against the average stack.
"""
def alignment_state(close: float, s1: float, s2: float, s3: float) -> str:
    if pd.isna(close) or pd.isna(s1) or pd.isna(s2) or pd.isna(s3):                                  #|.isna detects: None;NaN;NaT
        return "n/a"
    if close >= s1 and close >= s2 and close >= s3:
        return "Up"
    if close <= s1 and close <= s2 and close <= s3:
        return "Down"
    return "Neutral"
