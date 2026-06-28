#C01_Calc.py
"""
This module calculates cockpit market scores from selected states and market data. It combines trend, volatility, term-structure, and extra inputs into normalized risk metrics.
"""
from __future__ import annotations
import math
import statistics
import time
from typing import Any
import streamlit as st
import pandas as pd
"""_______________________________________________________________________________________________________________________"""
from Pages.Calculation.Content.Cockpit.C01_State_Logging import MarketState, get_state
from Pages.Data.Content.Cockpit.C01_DataTables import (
    ELLIOTT_AMPLIFIER,
    OPENING_DRIVE_AMPLIFIER,
    SENTIMENT_TREND_AMPLIFIER,
    VOL_SENTIMENT_TREND_AMPLIFIER,
    lookup_amplifier,
    MARKET_VOL_INDEX,
    SMA_LENGTHS,
    TF_WEIGHTS,
    GearScale,
    ComponentBounds,
    Weights
)
from Pages.Data.Content.Cockpit.C01_Set_States import (Vol_state, 
                                                        trend_state,
                                                        alignment_state, 
                                                        api_state_to_component_state,
                                                        conviction_state,
                                                        Trendstrength_state,
                                                        volstrength_state,
                                                        termstructure_state)
"""_______________________________________________________________________________________________________________________"""
"""
Reads the active cockpit market from Streamlit session state. 
This keeps every market-specific calculation tied to the same market the user selected in the UI.
"""
def _selected_market() -> str:
    return str(st.session_state.get("cockpit_market", "MES1!"))
"""________________________________________________________________________________________________"""
"""
Converts database state rows into selectbox options and a score lookup table. 
The UI receives readable labels while the calculation layer can quickly access direction and risk values.
"""
def calculate_state_options(rows: list[Any]) -> tuple[list[Any], dict[Any, dict[str, Any]]]:                                                                                                                                          
    opts = [r[0] for r in rows]                                                                         
    score_map = {                                                                                       #|selects the state_names [0]index for rows        
        r[0]: {"dir": (r[1] if r[1] is not None else 0.0), "risk": float(r[2])}                         #|scores: Dict{state_name:Dict{dir:float,risk:float}}
        for r in rows                                                                                   #|->For all states
    }                                                                                                   
    return opts, score_map    
"""________________________________________________________________________________________________"""
"""
Reads the risk score for a selected component state. 
Missing states are treated as neutral zero-risk inputs 
so optional selections do not break the cockpit calculation.
"""
def risk_of(score_map: dict, key: str) -> float:
    return float(score_map.get(key, {}).get("risk", 0.0))                                               #|component->get.risk
"""________________________________________________________________________________________________"""
"""
Reads the directional score for a selected component state. 
Missing states return zero so the final trend score stays stable when data is incomplete.
"""
def dir_of(score_map: dict, key: str) -> float:
    return float(score_map.get(key, {}).get("dir", 0.0))                                               #|component->get.risk
"""________________________________________________________________________________________________"""
"""
Builds a unique Streamlit key for the currently selected market. 
This prevents inputs from one market from overwriting the saved inputs of another market.
"""
def market_key(name: str) -> str:
    return f"{_selected_market()}__{name}"                                                              #|Creates unique keys for component variables
"""________________________________________________________________________________________________"""
"""
Measures how strongly the component scores agree with each other. 
A low variance between inputs produces higher conviction, while conflicting inputs reduce the score.
"""
def compute_conviction_score(values: list[float]) -> float:
    try:
        var = statistics.pvariance(values)                                                              #|Variance of input values scores(Risk-Scores later)
        std = math.sqrt(var)                                                                            #|Get away from squared returns
        raw = 1 - (std / 0.5)                                                                           #|largest standard deviation between values [0;1]=0.5
        return max(0.0, min(1.0, raw))                                                                  #|---->low standard dev -> 0/0.5->High Conviction
    except Exception:
        return 1.0                                                                                      #|Defensive
"""________________________________________________________________________________________________"""
"""
Calculates weighted scores for discretionary context inputs such as sentiment, 
Elliott waves, opening drive, and market profile. 
It loads the selected state from each component 
and combines direction and risk into normalized values.
"""
def extra_input_scores(
    rows_by_component: dict[str, list[Any]],                                                            #|fetch_scores_by_state()
    selected_values: dict[str, str],                                                                    #|Get from the Frontend
    weights: dict[str, float] | None = None
) -> dict[str, float]:
    values = {}
    for name, rows in rows_by_component.items():                                                        #|name and fetched rows of the component
        _opts, score_map = calculate_state_options(rows)                                                #|iterates over two objects we want the score_map
        selected_value = selected_values[name]                                                          #|UI Input
        weight = 1.0 if weights is None else weights.get(name, 1.0)                                     #|weights either via datatable or db
        values[name] = risk_of(score_map, selected_value) * weight                                      #|risk calc
    sentiment_val = sum((values[name] for name in weights)) if weights is not None else 0.0             #|Sum sentiment vals
    market_profile_val = values["market_profile"]                                                       #|Cast each value
    elliott_val = values["elliott"]
    extra_market_inputs = {"sentiment": sentiment_val,
                            "elliott": elliott_val,
                            "market_profile": market_profile_val
                            }
    return extra_market_inputs
    
"""________________________________________________________________________________________________"""
"""
Calculates the core cockpit component scores for trend, volatility, and term structure. 
It applies component-specific timeframe weights 
so each timeframe contributes with the intended importance.
"""
def main_input_scores(
    states_map: dict[str, dict[str, dict[str, float]]],
    selected_values: dict[str, dict[str, str]],
    weights: dict[str, dict[str, float]],
) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}

    for component, score_map in states_map.items():                                                         #|Maps each component to its map
        tf_scores: dict[str, dict[str, float]] = {}
        dir_total = 0.0
        risk_total = 0.0

        for timeframe, selected_state in selected_values.get(component, {}).items():                        #|For each timeframe with its selected state
            weight = weights.get(component, {}).get(timeframe, 0.0)

            dir_score = dir_of(score_map, selected_state) * weight                                          #|Maps the ("...")score from score_map to the selected_state
            risk_score = risk_of(score_map, selected_state) * weight                                        #|("...")

            tf_scores[timeframe] = {                                                                        #|Maps the state,weight,dir,risk for each timeframe in tf_scores
                "state": selected_state,
                "weight": weight,
                "dir": dir_score,
                "risk": risk_score,
            }

            dir_total += dir_score                                                                          #|Aggregation of dir sum
            risk_total += risk_score                                                                        #|("...")

        summary[component] = {                                                                              #|Aggregation of each component
            "dir_score": dir_total,
            "risk_score": risk_total,
            "breakdown": tf_scores,
        }
    return summary
"""________________________________________________________________________________________________"""
"""
Combines sentiment, Elliott-wave, opening-drive, and market-profile inputs into one trend-strength value. 
The function uses amplifier tables so context only adds strength when it supports the selected trend.
"""
def trend_strength_calc(sent_under, elliott_choice, op_choice: Any,             
                        trend_dir_score: float,
                        term_dir_score: float, 
                        selected_market: str,
                        trend_state: str):
    sentiment_support = lookup_amplifier(
        SENTIMENT_TREND_AMPLIFIER,
        trend=trend_state,
        support=sent_under,
    )
    elliott_support = lookup_amplifier(
        ELLIOTT_AMPLIFIER,
        wave=elliott_choice,
        trend=trend_state,
    )
    opening_drive_support = lookup_amplifier(
        OPENING_DRIVE_AMPLIFIER,
        opening_drive_state=op_choice,
        trend=trend_state,
    )

    term_strength = term_dir_score if selected_market == "MGC1!" else -term_dir_score                       #|Inventory Risk handled differently in Commodities
    

    trend_strength = (
        trend_dir_score
        + term_strength
        ) / 2.0
    trend_strength = -max(-1.0, min(1.0, trend_strength))  
    return trend_strength
"""________________________________________________________________________________________________"""
"""
Builds one volatility-strength value from volatility score, term-structure risk, and selected risk settings. 
The result is normalized so it can be compared with other cockpit scores.
"""
def volatility_strength_calc(vola: float,
                             term_structure_score: float, 
                             sent_vola: Any,
                             vola_state: str
                             ):
    
    vol_sentiment_strength = lookup_amplifier(                                                          
        VOL_SENTIMENT_TREND_AMPLIFIER,
        vola=vola_state,       
        support=sent_vola,
    )
    vol_strength = (vola + (-term_structure_score) + vol_sentiment_strength) / 3  
    return vol_strength
"""________________________________________________________________________________________________"""
"""
Writes the latest calculated cockpit metrics back into Streamlit session state. 
This lets the visible UI and the stored market state stay synchronized after each calculation.
"""
def refresh_session_state(gear, rs_norm, conviction_score, trend_strength, vol_strength: float, 
                          bars:dict[str, Any], 
                          breakdown: dict[str, Any]):
    st.session_state["gear"] = gear                                                         
    st.session_state["rs_norm"] = rs_norm
    st.session_state["barometers"] = bars
    st.session_state["breakdown"] = breakdown
    st.session_state["risk_metrics"] = {
        "gear": gear,
        "conviction": conviction_score,
        "trend_strength": trend_strength,
        "vol_strength": vol_strength,
        "timestamp": time.time(),
    }
"""________________________________________________________________________________________________"""
"""
Returns the volatility-index weights used for the selected market. 
If no custom market setup exists, the function falls back to equal weighting so calculations can continue.
"""
def return_vol_indice_weights(selected_market: str):
    vola_instr_weights = {"vix": 1.0, "vvix": 1.0, "cor1m": 1.0}                                              #|Weights on different market dependencies
    if selected_market in ("MNQ1!", "MGC1!"):
        vola_instr_weights = {"vix": 3.0, "vvix": 0.0, "cor1m": 0.0} 
    return vola_instr_weights
"""________________________________________________________________________________________________"""    
"""
Main packaged cockpit calculation.
Called from the UI only after all current selections have been collected
compute_cockpit_metrics = prepare inputs -> apply fallbacks/API -> calculate metrics -> sync runtime state
"""
"""________________________________________________________________________________________________"""
def compute_cockpit_metrics(
    selected_market: str,
    vola_score: float,
    states_map: dict[str, dict[str, dict[str, float]]],
    main_input_vals: dict[str, dict[str, str]],
    main_input_weights: dict[str, dict[str, float]],

    rows_by_component: dict[str, list[Any]],                                                            #|fetch_scores_by_state()
    extra_input_vals: dict[str, str],                                                                    #|Get from the Frontend
    extra_input_weights: dict[str, float],

    equity: float,
    macro_input_weights: Weights,
    gear_scale: GearScale
) -> MarketState:
    vola_instr_weights = return_vol_indice_weights(selected_market = selected_market) 
    #------------------Pull metric dics----------------#
    extra_inputs = extra_input_scores(rows_by_component=rows_by_component, 
                                      selected_values=extra_input_vals, 
                                      weights=extra_input_weights)
    
    main_inputs = main_input_scores(states_map=states_map, 
                                   selected_values=main_input_vals, 
                                   weights=main_input_weights)
    #------------------Calc individual metrics----------------#
    trend_norm_for_risk = trend_risk_score(main_inputs["trend"]["dir_score"], states_map["trend"], main_input_weights["trend"])                                                                                                                           
    term_norm_for_risk = max(0.0, min(1.0, float(main_inputs["term_structure"]["risk_score"]))) 

    trend_score = trend_normalized(main_inputs["trend"]["dir_score"])
    trend_strength = trend_strength_calc(extra_input_vals["under"], 
                                         extra_input_vals["elliott"], 
                                         extra_input_vals["Opening-Drive"],
                                         trend_score, 
                                         main_inputs["term_structure"]["dir_score"],
                                         selected_market=selected_market,
                                         trend_state = trend_state(trend_score)
                                         )
    
    vol_strength = volatility_strength_calc(vola = vola_score,
                                            term_structure_score = main_inputs["term_structure"]["dir_score"],
                                            sent_vola = extra_input_vals["vola"],
                                            vola_state = Vol_state(vola_score)
                                            )

    scores = []
    for item in extra_inputs:
        scores.append(extra_inputs[item])
    for item in main_inputs:
        scores.append(main_inputs[item]["risk_score"])
    conviction = compute_conviction_score(scores) if scores else 1.0
    #------------------Risk Calc----------------#
    w = macro_input_weights.__dict__
    vola_weight_sum = sum(vola_instr_weights.values())
    vola_risk = (
        sum(
            main_inputs[item]["risk_score"] * weight
            for item, weight in vola_instr_weights.items()
        ) / vola_weight_sum
        if vola_weight_sum > 0
        else 0.0
    )
    risk_weighted = (                                                                                                           #|Every componentriskscore with their weight
        extra_inputs["sentiment"] * w["sentiment"]
        + extra_inputs["elliott"] * w["elliott"]
        + extra_inputs["market_profile"] * w["market_profile"]
        + vola_risk * w["vola"]
        + trend_norm_for_risk * w["trend"]
        + equity * w["equity"]
        + term_norm_for_risk * w["term_structure"]
        )
    weight_sum = sum(w.values())
    rs_norm = (risk_weighted / weight_sum) if weight_sum > 0 else 0.0                                                           #|Final Riskscore accumulated
    #------------------Gear Settings----------------#
    gs = gear_scale
    if rs_norm > gs.first:
        gear = 1
    elif rs_norm > gs.second:
        gear = 2
    elif rs_norm > gs.third:
        gear = 3
    elif rs_norm > gs.fourth:
        gear = 4
    else:
        gear = 5
    #------------------MarketState ingestion----------------#
    market_state = get_state(selected_market)
    market_state.gear = gear
    market_state.vol_strength = vol_strength
    market_state.trend_strength = trend_strength
    market_state.conviction = conviction
    market_state.trend_score = trend_score
    market_state.vola_score = vola_score
    market_state.term_structure_score = main_inputs["term_structure"]["dir_score"]
    market_state.vol_state = Vol_state(vola_score)
    market_state.trend_state = trend_state(trend_score)
    market_state.conviction_state = conviction_state(conviction)
    market_state.trend_strength_state = Trendstrength_state(trend_strength)
    market_state.vola_strength_state = volstrength_state(vol_strength)
    market_state.term_structure_state = termstructure_state(
    main_inputs["term_structure"]["dir_score"]
    )
    return market_state, rs_norm
"""________________________________________________________________________________________________"""
"""
Calculates a simple moving average for the provided series or values. 
The helper is used to smooth price data before deriving alignment and volatility states.
"""
def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).mean() 
"""________________________________________________________________________________________________"""
"""
Derives volatility component states from fetched market data. 
It calculates moving averages for each volatility instrument and maps price alignment into cockpit component labels.
"""
def compute_vola_api_states(
    market: str,
    close: dict[str, dict[str, pd.Series]],
    indice_states_map: dict[str, dict[str, dict[str, float]]],
) -> tuple[float, dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, float]]:
    symbols = MARKET_VOL_INDEX.get(market) 
    scores_by_symbol: dict[str, float] = {}
    scores: list[float] = []
    selections: dict[str, dict[str, str]] = {}
    tf_states_by_symbol: dict[str, dict[str, str]] = {}
    lengths = SMA_LENGTHS
    for component, symbol in symbols.items():                                                   #|For each (potential) vol indice 
        tf_states: dict[str, str] = {}

        for tf_label in TF_WEIGHTS:                                                             #|For each timeframe
            series = close[symbol][tf_label]                                                    #|Get the closes of that vol indice with a specific timeframe

            if series.empty:
                tf_states[tf_label] = "n/a"                                                     #|Default fallback
                tf_states_by_symbol[symbol] = tf_states            
                return (1, 
                        selections, 
                        tf_states_by_symbol, 
                        scores_by_symbol)

            s1 = sma(series, lengths["sma1"])
            s2 = sma(series, lengths["sma2"])
            s3 = sma(series, lengths["sma3"])

            tf_states[tf_label] = alignment_state(                                              #|State alignment 
                series.iloc[-1],
                s1.iloc[-1],
                s2.iloc[-1],
                s3.iloc[-1],
            )

        selections[symbol] = {
            "micro": api_state_to_component_state(tf_states.get("1H", "Mixed")),                #|Dict building with defaultfallback (Conversion)
            "meso": api_state_to_component_state(tf_states.get("4H", "Mixed")),
            "macro": api_state_to_component_state(tf_states.get("D", "Mixed")),
            "mega": api_state_to_component_state(tf_states.get("W", "Mixed")),
        }
        
        summary = main_input_scores(
            {component: indice_states_map[component]},
            {component: tf_states},
            {component: TF_WEIGHTS},
        )
        scores_by_symbol[symbol] = summary[component]["dir_score"]
        scores.append(summary[component]["dir_score"])                                          #|Score for each indice
        tf_states_by_symbol[symbol] = tf_states

    
    return sum(scores) / len(scores) if not None else 0, selections, tf_states_by_symbol, scores_by_symbol
"""________________________________________________________________________________________________________________"""
"""
Scales a raw component value into a zero-to-one range using configured bounds. 
Values outside the configured range are clipped so one extreme input cannot distort the final score.
"""
def _normalize(x: float, bounds: ComponentBounds) -> float:
    low, high = bounds.min, bounds.max
    if high == low:
        return 0.0
    norm_output = (x - low) / (high - low)
    return max(0.0, min(1.0, float(norm_output)))
"""________________________________________________________________________________________________________________"""
"""
Combines selected component states into normalized trend, volatility, and term-structure scores. 
It applies timeframe weights and uses the database state tables as the scoring source.
"""
def component_scores(
    selections: dict[str, str],                                                                                                 #|Key, Value e.g. "intra" : "Momentum Up"
    state_table: dict[str, dict[str, float]],                                                                                   #|See load_state_table in DB_default.py
    tf_weights: dict[str, float],                                                                                               #|See load_timeframe_weights in DB_default.py
):
    dir_sum = 0.0
    risk_sum = 0.0
    breakdown: dict[str, Any] = {}

    for timeframe, state_name in selections.items():                                                                            
        weight  = float(tf_weights.get(timeframe, 0.0))                                                                         
        st = state_table.get(state_name, {"dir": 0.0, "risk": 0.0})                                                             #|Gives the states of a specific input 
        dir_score = weight * float(st["dir"])                                                                                   #|Timeframeweight Multiplicated by the Direction-Score
        risk_score = weight * float(st["risk"])                                                                                 #|Teimframeweight Multiplicated by the Risk-Score
        dir_sum += dir_score                                                                                                    #|Sum of all Component_states (Direction)
        risk_sum += risk_score                                                                                                  #|Sum of all Component_states (Risk)
        breakdown[timeframe] = {                                                                                                #|For each timeframe put the variables into dictionary
            "state": state_name,
            "w": weight,
            "dir": st["dir"],
            "risk": st["risk"],
            "dir_contrib": dir_score,
            "risk_contrib": risk_score,
        }
    return dir_sum, risk_sum, breakdown                                                                                         #|Return calc
"""________________________________________________________________________________________________________________""" 
"""
Converts normalized trend direction into a risk score. 
Strong directional alignment lowers or raises risk depending on how the trend score is positioned around neutral.
"""
def trend_risk_score(
    trend_dir_score: float,                                                                                                     #|Input
    state_table: dict[str, dict[str, float]],                                                                                   #|States 
    tf_weights: dict[str, float],                                                                                               #|Timeframeweights
) -> float:                                                                                                                     #|Float return
    if not state_table or not tf_weights:                                                                                       #|Defense
        return 0.0
    dir_values = [float(v.get("dir", 0.0)) for v in state_table.values()]                                                       #|Gets each Direction Score
    if not dir_values:                                                                                                          #|Defense
        return 0.0                                                                                                          
    max_dir = max(dir_values)                                                                                                   #|MAX of individual state dir
    min_dir = min(dir_values)                                                                                                   #|MIN of individual state dir
    max_score = sum(float(w) * max_dir for w in tf_weights.values())                                                            #|Computing max possible score
    min_score = sum(float(w) * min_dir for w in tf_weights.values())                                                            #|Computing min possible score
    denom = max_score - min_score                                                                                               #|Norm Diff. (6)
    if denom == 0:
        return 0.0
    center = (max_score + min_score) / 2.0                                                                                      #|This it the middle of the Parabola (0 because Norm. Dis.)
    norm = (trend_dir_score - center) / denom                                                                                   #|norm at Best/MIN (0,5)
    score = 1.0 - (2.0 * (norm**2))
    normalized = (score - 0.5) / 0.5                                                                                            #|With a Score 0f 0,5 (Best conditions)-->No risk
    return max(0.0, min(1.0, float(normalized)))                                                                                #|Defensive Output to Gap once more
"""________________________________________________________________________________________________________________"""
"""
Normalizes a raw directional value into a bounded minus-one-to-one range. 
This keeps extreme state combinations from overpowering the final trend calculation.
"""
def _norm_dir(value: float, max_abs: float = 3.0) -> float:
    if max_abs <= 0:                                                                                                           #|Defense
        return 0.0
    x = max(-max_abs, min(max_abs, float(value)))                                                                              #|Manual Cap to Upside and downside for defense
    return x / max_abs
"""________________________________________________________________________________________________________________"""
"""
Converts a directional trend value into the cockpit zero-to-one trend scale. 
The result can be displayed beside volatility and risk scores.
"""
def trend_normalized(dir_value: float) -> float:
    if dir_value is None:                                                                                                      #|Defense
        return 0.0
    val = -float(dir_value) / 3.0
    return max(-1.0, min(1.0, val))                                                                                            #|Manual Cap to Upside and downside for defense
"""________________________________________________________________________________________________________________"""
"""
Builds normalized trend and volatility display scores from the raw component outputs. 
Market-specific volatility index weights are applied before the final volatility score is returned.
"""
def compute_normalized_scores(
    breakdown: dict[str, dict[str, Any]],                                                                                       #|Dictionary called by compute_risk_and_gear_from_db
    selected_market: str,                                                                                                       #|For Dir Score see below
) -> dict:     
    vola_instr_weights = return_vol_indice_weights(selected_market = selected_market)
    
    comps = breakdown["components"]
    #------------------Trend Normalized----------------#
    trend_dir_sum = float(comps["trend"]["dir_score"])
    trend_norm = trend_normalized(trend_dir_sum)                                                                                #|Final Normalized
    #------------------Vola Normalized-----------------#
    w = vola_instr_weights                                                                                                      #|See Data/Content/DataTables
    vix_dir  = float(comps["vix"]["dir_score"])                                                                                 #|Getting Vol Scores
    vvix_dir = float(comps["vvix"]["dir_score"])
    cor1_dir = float(comps["cor1m"]["dir_score"])
    vola_raw = (                                                                                                                #|Weighting
        w.get("vix", 0.0) * vix_dir
        + w.get("vvix", 0.0) * vvix_dir
        + w.get("cor1m", 0.0) * cor1_dir
    )
    vola_norm = _norm_dir(vola_raw, max_abs=3.0)                                                                               #|Final Normalized
    risk_norm = float(breakdown["risk_norm"])
    return {                                                                                                                   #|Return in Dictionary {}
        "trend_score": trend_norm,      
        "vola_score": vola_norm,
        "risk_score": risk_norm,
    }
