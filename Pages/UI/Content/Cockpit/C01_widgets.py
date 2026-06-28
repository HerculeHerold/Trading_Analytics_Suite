#Cockpit_widgets.py
"""
This module wraps cockpit Streamlit inputs. It keeps market-specific widget state consistent across select boxes, fixed values, checkboxes, and numeric inputs.
"""
"""________________________________________________________________________________________________"""
import streamlit as st                                                                                  
from Pages.Calculation.Content.Cockpit.C01_State_Logging import get_state
from Pages.Calculation.Content.Cockpit.C01_Calc import _selected_market, market_key
"""________________________________________________________________________________________________"""
"""
Returns the per-market widget state dictionary from Streamlit session state. 
It creates the nested storage structure when the selected market is opened for the first time.
"""
def _market_state():                                                                                    
    return get_state(_selected_market())                                                                #|Gets the Market STATES (see State_Logging) via session_state
"""________________________________________________________________________________________________"""
"""
Renders a selectbox whose value is stored separately for each market. 
This lets the user switch markets without losing the previous market-specific selection.
"""
def market_selectbox(label: str, options: list[str], key_suffix: str) -> str:                           
    market_state = _market_state()                                                                      #|("")
    key = market_key(key_suffix)                                                                        #|Individual key for each component per Market
    default_val = market_state.inputs.get(key, options[0] if options else "")                           #|Gets the default value of each state
    if key not in st.session_state or st.session_state[key] not in options:                             #|Initialized value yet? or is value a legal dropdown?
        st.session_state[key] = default_val                                                             #|e.g. on program start
    value = st.selectbox(label, options, key=key)                                                       #|Onchange of the selectbox we have a New Value
    market_state.inputs[key] = value                                                                    #|Refreshing value of component for market (key)
    return value                                                                                        
"""________________________________________________________________________________________________"""
"""
Renders a disabled selectbox for market states forced by volatility-shock logic. 
It still writes the value into the same market-scoped state structure as editable widgets.
"""
def market_fixed_selectbox(label: str, value: str, key_suffix: str) -> str:                             #|Same logic as above
    market_state = _market_state()                                                                    
    key = market_key(key_suffix)                                                                        
    if key not in st.session_state:                                                                     #|If Value isnt initialized:
        st.session_state[key] = value                                                                   #|current value will be taken
    selected = st.selectbox(label, [value], key=key)                                                    
    market_state.inputs[key] = selected                                                                 #|Refreshing state
    return selected                                                                                     
"""________________________________________________________________________________________________"""
"""
Renders a checkbox stored under the active market key. 
The optional callback allows linked checkboxes, such as opposite volatility-shock states, to control each other.
"""
def market_checkbox(                                                                                    
    label: str,                                                                                         
    key_suffix: str,                                                                                    
    default: bool = False,                                                                              
    on_change=None,                                                                                     
) -> bool:                                                                                              
    market_state = _market_state()                                                                      
    key = market_key(key_suffix)                                                                        
    default_val = bool(market_state.inputs.get(key, default))                                           #|Again gets the key or else we have false State
    if key not in st.session_state:                                                                     #|If value isnt initialized we take the session_state stored
        st.session_state[key] = default_val                                                             
    value = st.checkbox(label, key=key, on_change=on_change)                                            
    market_state.inputs[key] = bool(value)                                                              
    return bool(value)                                                                                  
"""________________________________________________________________________________________________"""
"""
Renders a number input stored separately for the active market. 
This keeps values like equity or manual scores stable when the cockpit market changes.
"""
def market_number_input(label: str, key_suffix: str, default: float, step: float):
    selected_market = _selected_market()
    market_state = get_state(selected_market)
    key = market_key(key_suffix)
    if key not in st.session_state:
        st.session_state[key] = market_state.inputs.get(key, default)
    value = st.number_input(label, step=step, key=key)
    market_state.inputs[key] = value
    return value

