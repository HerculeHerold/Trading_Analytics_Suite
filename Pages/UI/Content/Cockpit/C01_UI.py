# Cockpit_UI.py 
"""
This Streamlit page renders the market cockpit. 
It collects trend, volatility, term-structure, and extra inputs, then displays the computed market state.
"""
"""_______________________________________________________________________________________________________________________""" 
import streamlit as st                                                                             
import pandas as pd                                                                                
from Pages.DB.Content.Cockpit.C01_DB_default import (load_state_table, 
                                                      load_timeframe_weights,
                                                      load_weights,
                                                      load_gear_scale,
                                                      fetch_timeframe_close,
                                                      fetch_scores_by_state,
                                                      ensure_schema,
                                                      seed_defaults,
                                                      ensure_log_schema)                                         
from Pages.Calculation.Content.Cockpit.C01_State_Logging import get_state                                     
from Pages.Calculation.Content.Cockpit.C01_Calc import (market_key,                                                                  
                                                _norm_dir,
                                                compute_cockpit_metrics,
                                                compute_vola_api_states
                                                )                           
from Pages.Data.Content.Cockpit.C01_DataTables import (MARKETS,
                                                        TF_PER_INDICE,
                                                        SENT_WEIGHTS,
                                                        MARKET_VOL_INDEX,
                                                        )                                          
from Pages.Data.Content.Cockpit.C01_Set_States import Vol_state, state_color
from Pages.UI.Content.Cockpit.C01_widgets import (market_checkbox,                                   
                                                market_fixed_selectbox,                            
                                                market_selectbox, 
                                                market_number_input,                                                                 
                                                )                                                  
from Pages.UI.Content.Cockpit.C01_charts_rendering import (render_risk_echart_gauge,                     
                                                render_trend_echart_gauge,                                    
                                                render_vol_echart_gauge,                           
                                                render_strength_bar,                               
                                                conviction_bar_chart)                                                      
"""_______________________________________________________________________________________________________________________""" 
def C01_main():
    ensure_schema() 
    seed_defaults()     
    ensure_log_schema()                                                                     
    st.set_page_config("Cockpit", layout="wide")                                                                                                                                            
    left, leftmiddle, rightmiddle, right = st.columns([1,1,1,1])                                        #|Columns for each input:                                                                                    
    with left:                                                                                          #|markets are selected here
        st.title("Cockpit")                                                                             #|Instantly gives the specific state for all Risk    
    with rightmiddle:                                                                                   #|Inputs of that specific market
        selected_market = rightmiddle.selectbox("Current Market:", MARKETS, key="cockpit_market")                                                                                       
    market_state = get_state(selected_market)                                                                                              
    with leftmiddle:                                                                                        
        equity_val = market_number_input("Equity", "equity_val", 0.5, 0.05)                             
    with right:                                                                                         
        l,m,r = st.columns(3)                                                                                   
        with m:                                                                                         #|Align centered Volatility Event    
            key_cb_a = market_key("cb_a")                                                               #|Toggles (Both cannot be active at the same time)
            key_cb_b = market_key("cb_b")                                                               #|market_key : Current State of specific market          
            
            def toggle_a():                                                                                
                if st.session_state.get(key_cb_a):                                                      
                    st.session_state[key_cb_b] = False                                                                                                                                         #|
            
            def toggle_b():                                                                             
                if st.session_state.get(key_cb_b):                                                      
                    st.session_state[key_cb_a] = False                                                  
            market_checkbox("Volatility Shock Down", "cb_a", on_change=toggle_a)                        #|Two separate boxes cancel each other out
            market_checkbox("Volatility Shock Up", "cb_b", on_change=toggle_b)                          

    st.divider()
    """____________________________________________________________________________________________________"""  
    left,right = st.columns(2)                                                                          
    with left:                                                                                          
        st.subheader("Trend Structure")                                                                 
    with right:                                                                                         #|Columns for the Headlines
        st.subheader("Elliott & Market Profile")                                                                                                
    left, right = st.columns(2)                                                                         
    with left:                                                                                          
        trend_states = load_state_table("trend")                                                        
        trend_opts = list(trend_states.keys())                                                          
        c1, c2, c3, c4 = st.columns(4)                                                                  
        if st.session_state.get(market_key("cb_a")) == True:                                            
            sel_trend = {                                                                               
                "intra":   market_fixed_selectbox("Intra", "Momentum Up", "trend_intra_up"),            
                "trading": market_fixed_selectbox("Trading", "Momentum Up", "trend_trading_up"),        #|Vol Event cb_a
                "micro":   market_fixed_selectbox("Micro", "Momentum Up", "trend_micro_up"),            #|-->Selectboxes switch into Momentum
                "macro":   market_fixed_selectbox("Macro", "Momentum Up", "trend_macro_up"),            #|--> Trends occupied due to Event
            }                                                                                           
        if st.session_state.get(market_key("cb_b")) == True:                                            
            sel_trend = {                                                                               
                "intra":   market_fixed_selectbox("Intra", "Momentum Down", "trend_intra_down"),        
                "trading": market_fixed_selectbox("Trading", "Momentum Down", "trend_trading_down"),    #|Vol Event cb_b 
                "micro":   market_fixed_selectbox("Micro", "Momentum Down", "trend_micro_down"),        #|-->Selectboxes switch into Momentum
                "macro":   market_fixed_selectbox("Macro", "Momentum Down", "trend_macro_down"),        #|--> Trends occupied due to Event
            }                                                                                           
        if not st.session_state.get(market_key("cb_a")) and not st.session_state.get(market_key("cb_b")):
            sel_trend = {                                                                               
                "intra":   market_selectbox("Intra", trend_opts, "trend_intra"),                        
                "trading": market_selectbox("Trading", trend_opts, "trend_trading"),                    #|Normal State with changeable selectboxes
                "micro":   market_selectbox("Micro", trend_opts, "trend_micro"),                        #|--->Trend based on Analysis
                "macro":   market_selectbox("Macro", trend_opts, "trend_macro"),                        
            }                                                                                           
        # Persist final trend choices as defaults for the market                                        
        market_state.inputs[market_key("trend_intra")] = sel_trend["intra"]                             #|Saving the States as new defaults when reopening
        market_state.inputs[market_key("trend_trading")] = sel_trend["trading"]                         #|the Pages while Terminal still on
        market_state.inputs[market_key("trend_micro")] = sel_trend["micro"]                             
        market_state.inputs[market_key("trend_macro")] = sel_trend["macro"]                             
        with right:                                                                                     
            # Elliott waves                                                                             #|Same for other Inputs
            elliott_opts = list(load_state_table("elliott_type").keys())                             
            elliott_choice = market_selectbox("Elliott-Waves Type", elliott_opts, "elliott_type")        
            #Opening Drive                                                                              
            op_opts = list(load_state_table("Opening-Drive").keys())                                   #|Loads the State Options from the default Table
            op_choice = market_selectbox("Opening-Drive", op_opts, "opening_drive")                     
            # Market Profile Day                                                                        
            mp_opts = list(load_state_table("market_profile_day").keys())                                 
            mp_choice = market_selectbox("Market Profile Day", mp_opts, "market_profile_day")           
            
    st.divider()
    """________________________________________________________________________________________________""" 
    # Vol comp                                                                                          
    left, right = st.columns(2)                                                                         
    with left:                                                                                          
        st.subheader("Volatility State")                                                                #|Headers
    with right:                                                                                         
        st.subheader("Term-Structure")                                                                  
    #Term Structure                                                                                     
    with right:                                                                                         
        term_opts = list(load_state_table("term_structure").keys()) 
        sel_term = {                                                                                    
            "shortterm": market_selectbox("Shortterm", term_opts, "term_short"),                        #|Each selectbox in same column
            "nearterm":  market_selectbox("Nearterm",  term_opts, "term_near"),                         #|Pattern: {State;Selectboxinput(Input)}
            "midterm":   market_selectbox("Midterm",   term_opts, "term_mid"),                          #|--->Selectbox named "Shortterm" has the option term_opts
            "longterm":  market_selectbox("Longterm",  term_opts, "term_long"),                         #|--->selterm inherits Values
        }
    indice_states = {
        component: load_state_table(component)
        for component in ["VIX", "VVIX", "COR1M"]
    }

    closes = fetch_timeframe_close(TF_PER_INDICE, list(MARKET_VOL_INDEX[selected_market].values()))
    for symbol, tf_labels in TF_PER_INDICE.items():
        closes.setdefault(symbol, {})
        for tf_label in tf_labels:
            if not isinstance(closes[symbol].get(tf_label), pd.Series):
                closes[symbol][tf_label] = pd.Series(dtype=float)
    api_vola_score, api_vola_states, api_tf_states, api_component_scores = compute_vola_api_states(
        selected_market,
        closes,
        indice_states,
    )
    with left:                                                                                        
        if api_tf_states:                                                                               
            rows = []                                                                                   
            symbol_components = {
                symbol: component
                for component, symbol in (
                    MARKET_VOL_INDEX.get(selected_market) 
                ).items()
            }
            for symbol, tf_states in api_tf_states.items():                                             
                component = symbol_components.get(symbol)
                score = None
                rows.append(                                                                            
                    {                                                                                   
                        "Instrument": symbol.replace("-USD", ""),                                       
                        "1H": tf_states.get("1H", "n/a"),                                               
                        "4H": tf_states.get("4H", "n/a"),                                               
                        "D": tf_states.get("D", "n/a"),                                                 
                        "W": tf_states.get("W", "n/a"),                                                 
                        "Score": f"{api_component_scores.get(symbol):.2f}" if api_component_scores is not None else "n/a",                        
                    }                                                                                   
                )                                                                                       
            vola_state_label = Vol_state(api_vola_score) if api_vola_score else "Neutral"                                               
            vola_score_text = f"{api_vola_score:.2f}" if api_vola_score is not None else "n/a"          
            st.dataframe(pd.DataFrame(rows), use_container_width=True)                                  
            color = state_color(vola_state_label)                                                       
            st.markdown(                                                                                
                f"""
                <div style="background:{color};padding:16px;border-radius:12px;color:#0b0f14;">
                    <div style="font-size:18px;font-weight:700;">{vola_state_label}</div>
                    <div style="font-size:28px;font-weight:800;">{vola_score_text}</div>
                </div>
                """,                                                                                    
                unsafe_allow_html=True,                                                                 
            )                                                                                           

    st.divider()
    """________________________________________________________________________________________________""" 
    c1, c2 = st.columns(2) 
    sent_under_opts = list(load_state_table("sent_underlying").keys())                                  #|Loads the Options for specific underlying
    sent_vola_opts = list(load_state_table("sent_vola_seasonal").keys())                           
    sent_aaii_opts = list(load_state_table("sent_aaii").keys())                                     
    sent_fng_opts = list(load_state_table("sent_fng").keys())                                                                                                                    #|
    with c1:                                                                                            
        sent_under = market_selectbox("Underlying Seasonal", sent_under_opts, "sent_under")             #|Same logic (sel_term)^^^^
        sent_aaii = market_selectbox("AAII Sentiment", sent_aaii_opts, "sent_aaii")                     
    with c2:                                                                                           
        sent_vola = market_selectbox("Vola Seasonal", sent_vola_opts, "sent_vola")                      
        sent_fng = market_selectbox("Fear & Greed Index", sent_fng_opts, "sent_fng")                    #|("")

    st.divider()
    """________________________________________________________________________________________________"""
    """
    Calculation of volatility, trend and other inputs. 
    Later on displaying in UI elements 
    """ 
    main_components = ["trend", "vix", "vvix", "cor1m", "term_structure"]
    states_map = {component: load_state_table(component) for component in main_components}
    main_input_weights = {
        component: load_timeframe_weights(component)
        for component in main_components
    }
    main_input_vals = {
        "trend": sel_trend,
        "term_structure": sel_term,
    }


    raw_extra_rows = fetch_scores_by_state(
        [
            "sent_underlying",
            "sent_vola_seasonal",
            "sent_aaii",
            "sent_fng",
            "market_profile_day",
            "elliott_type",
        ]
    )
    rows_by_component = {
        "under": raw_extra_rows["sent_underlying"],
        "vola": raw_extra_rows["sent_vola_seasonal"],
        "aaii": raw_extra_rows["sent_aaii"],
        "fng": raw_extra_rows["sent_fng"],
        "market_profile": raw_extra_rows["market_profile_day"],
        "elliott": raw_extra_rows["elliott_type"],
    }
    extra_input_vals = {
        "under": sent_under,
        "vola": sent_vola,
        "aaii": sent_aaii,
        "fng": sent_fng,
        "market_profile": mp_choice,
        "elliott": elliott_choice,
        "Opening-Drive": op_choice,
    }

    macro_input_weights = load_weights()
    gear_scale = load_gear_scale()

    market_state, risk = compute_cockpit_metrics(
        selected_market=selected_market,
        vola_score = api_vola_score, 
        states_map=states_map,
        main_input_vals=main_input_vals,
        main_input_weights=main_input_weights,
        rows_by_component=rows_by_component,
        extra_input_vals=extra_input_vals,
        extra_input_weights=SENT_WEIGHTS,
        equity=equity_val,
        macro_input_weights=macro_input_weights,
        gear_scale=gear_scale,
    )

    gear = market_state.gear
    trend = market_state.trend_score
    vola = api_vola_score if api_vola_score is not None else _norm_dir(market_state.vola_score, max_abs=3.0)
    conviction_score = market_state.conviction
    trend_strength = market_state.trend_strength
    vol_strength = market_state.vol_strength

    st.subheader("Current Gear & Barometers")                                                           
    c1, c2, c3, c4 = st.columns(4)                                                                      #|Metrics, formatted string 2 decimal spots
    c1.metric("Gear", gear)                                                                             
    c2.metric("RiskScore", f"{risk:.2f}")                                                               
    c3.metric("Trend-Barometer", f"{-trend:.2f}")                                                        
    c4.metric("Vola-Barometer",  f"{vola:.2f}")                                                         
    rcol, _ = st.columns([1, 3])                                                                        

    st.divider()
    """________________________________________________________________________________________________""" 
    left, middle, right = st.columns([1, 1, 1])                                                         
    with left:                                                                                          #|Barometers/gauges rendered
        render_trend_echart_gauge("Trend-Barometer", -trend)                                             #|Trend^
    with middle:                                                                                        
        render_vol_echart_gauge("Vola-Barometer", vola)                                                 #|Vola^
    with right:                                                                                         
        render_risk_echart_gauge("Risk-Barometer", risk)                                                #|Risk^

    st.divider()
    """________________________________________________________________________________________________""" 
    #Compute                                                                                            #|
    lleft,rright= st.columns([1,8])                                                                     #|Barcharts with metric next to them
    with lleft:                                                                                         #|under each other [1;8]->Sizing
        st.metric("Conviction Score: ", f"{conviction_score:.2f}")                                      
    with rright:                                                                                        
        conviction_bar_chart("Conviction",conviction_score)                                            
    lleft,rright= st.columns([1,8])                                                                     
    with lleft:                                                                                         
        st.metric("Trend-Strength", f"{trend_strength:.2f}")                                            
    with rright:                                                                                        
        render_strength_bar("Trend Strength",trend_strength)                                                                                  
    lleft,rright= st.columns([1,8])                                                                     
    with lleft:                                                                                         
        st.metric("Volatility-Strength", f"{vol_strength:.2f}")                                         
    with rright:                                                                                        
        render_strength_bar("Volatility Strength",vol_strength)  

    st.divider()
    """________________________________________________________________________________________________""" 
    
if __name__ == "__main__": 
    C01_main()


