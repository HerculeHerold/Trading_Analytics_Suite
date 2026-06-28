#J03_Datasets
"""
This module creates the default trade checklist dataset. 
It centralizes the journal columns so the UI and database layer use the same structure.
"""
"""________________________________________________________________________________________________"""  
from Pages.DB.Content.Journal.J03_DB_paths import CHECKLIST_PATH
"""________________________________________________________________________________________________""" 
"""
Creates an empty trade checklist dataframe with the expected journal columns. 
The structure gives exports and manual reviews a consistent column order.
"""
def create_Trade_Checklist():
    with open(CHECKLIST_PATH, "w", encoding="utf-8") as txt:
        txt.write("""--- Default Checklist ---"""
        )
    with open(CHECKLIST_PATH, "r", encoding="utf-8") as txt:
        return txt.read()
"""________________________________________________________________________________________________""" 
"""
Splits the columns into eachs dependencies
"""
TRADE_COLS = {
    "trade_id",
    "size",
    "direction",
    "market",
    "entry",
    "stop",
    "profit",
    "breakeven",
    "trailing",
    "min_risk",
    "max_risk",
    "st_atr",
    "lt_atr",
    "point_value",
    "exits",
    "exit_time",
    "mfe",
    "mae",
    "notes",
    "created_at",
}
TAG_COLS = {
    "strategy",
    "trend_state",
    "vola_state",
    "term_structure_state",
    "gear",
    "conviction",
    "trend_strength",
    "vola_strength",
    "gear_state",
    "conviction_state",
    "trend_strength_state",
    "vola_strength_state",
}
INT_COLS = {"size", "gear"}
FLOAT_COLS = {
    "entry",
    "stop",
    "profit",
    "breakeven",
    "trailing",
    "min_risk",
    "max_risk",
    "st_atr",
    "lt_atr",
    "point_value",
    "exits",
    "mfe",
    "mae",
    "conviction",
    "trend_strength",
    "vola_strength",
}
TD_COLS = {"created_at", "exit_time"}
