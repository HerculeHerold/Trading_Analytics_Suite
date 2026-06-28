#RO2_DataTables.py
"""
This module initializes risk-management defaults in Streamlit session state. 
It keeps settings, position values, and trade metadata available across page reruns.
"""
"""____________________________________________________________________________________________________"""
import streamlit as st 
"""____________________________________________________________________________________________________"""
POINT_VALUES = {
    "MES1!": 5,
    "MGC1!": 10,
    "MCL1!": 100,
    "MNQ1!": 2,
}
"""____________________________________________________________________________________________________"""
TICK_VALUES = {
    "MES1!": 0.25,
    "MGC1!": 0.1,
    "MCL1!": 0.01,
    "MNQ1!": 0.25,
}
"""____________________________________________________________________________________________________"""
GEAR_MULT = {
    1: 0.5,
    2: 0.75,
    3: 1.0,
    4: 1.25,
    5: 1.5,
}
"""____________________________________________________________________________________________________"""
ATR_BAR_SIZE = "5 mins"
CORR_BAR_SIZE = "60 mins"
CORR_LOOKBACK = 50
"""____________________________________________________________________________________________________"""
"""
Initializes missing Streamlit session-state defaults for the risk-management page. 
This gives settings, position inputs, and tracking fields stable values after every rerun.
"""
def ensure_defaults():
    # Settings defaults
    st.session_state.setdefault("rm_equity", 50000)
    st.session_state.setdefault("rm_max_bp", 4)
    st.session_state.setdefault("rm_trade_risk", 0.5)
    st.session_state.setdefault("rm_max_daily_risk", 1.0)

    # Position defaults
    st.session_state.setdefault("rm_num_pos", 1)
    st.session_state.setdefault("rm_num_contracts", 1)

    # Other defaults
    st.session_state.setdefault("rm_tp_needed", False)
    st.session_state.setdefault("st_atr_len", 9)
    st.session_state.setdefault("lt_atr_len", 50)


    
