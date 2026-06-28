#J03_Calc.py
"""
This module calculates derived journal values from trade rows. 
It computes profit, potential, and normalized cell values before the journal is displayed or edited.
"""
"""________________________________________________________________________________________________""" 
import pandas as pd
"""________________________________________________________________________________________________""" 
"""
Calculates realized profit or loss for one journal row. 
It compares entry and exit prices, applies trade direction, and scales the result by size and point value.
"""
def compute_pnl(row):
        entry = pd.to_numeric(row.get("entry"), errors="coerce")                                    #|Fetches calc inputs
        exits = pd.to_numeric(row.get("exits"), errors="coerce")
        size = pd.to_numeric(row.get("size"), errors="coerce")
        point_value = pd.to_numeric(row.get("point_value"), errors="coerce")
        direction = str(row.get("direction") or "").strip().lower()
        if pd.isna(entry) or pd.isna(exits) or pd.isna(size) or pd.isna(point_value):
            return None                                                                             #|Defense
        if direction == "short":                                                                    #|Calc dependent on direction
            return float(point_value * size * (entry - exits))
        if direction == "long":
            return float(point_value * size * (exits - entry))
        return None                                                                                 #|If none of these true return None
"""________________________________________________________________________________________________""" 
"""
Calculates the still-available profit potential for one journal row. 
It compares entry and target levels, applies trade direction, and converts the result into trade points.
"""
def compute_potential(row):
        entry = pd.to_numeric(row.get("entry"), errors="coerce")                                    #|Fetches calc inputs
        mfe = pd.to_numeric(row.get("mfe"), errors="coerce")
        exits = pd.to_numeric(row.get("exits"), errors="coerce")
        direction = str(row.get("direction") or "").strip().lower()
        if pd.isna(entry) or pd.isna(mfe) or pd.isna(exits):
            return None                                                                             #|Defense
        if direction == "long":                                                                     #|Calc dependent on direction
            return float(mfe - max(exits - entry, 0))
        if direction == "short":
            return float(mfe - max(entry - exits, 0))
        return None                                                                                 #|If none of these true return None
"""________________________________________________________________________________________________""" 
"""
Normalizes edited journal cell values before they are written back to storage. 
The function converts timestamps, integers, floats, and empty values into consistent database-safe types.
"""
def normalize_cell(col, val, dt_cols: set[str], int_cols: set[str], float_cols: set[str]):
        if pd.isna(val):
            return None                                                                             #|Defense
        if col in dt_cols:                                                                          
            ts = pd.to_datetime(val, errors="coerce")                                               
            if pd.isna(ts):
                return None
            return ts.strftime("%H:%M:%S %d-%m-%Y")                                                 #|Date Conversion (TEXT)
        if col in int_cols:
            return int(val)                                                                         #|INTEGER Conversion
        if col in float_cols:
            return float(val)                                                                       #|REAL Conversion
        return str(val)                                                                             #|Any other value = str(TEXT)
"""________________________________________________________________________________________________""" 
"""
Recalculates derived journal columns after edits or imports. 
It normalizes timestamp columns and refreshes row-level PnL and potential values for the whole dataframe.
"""
def calc_row_vals(df: pd.DataFrame):
    if "exits" not in df.columns:                                                                   #|Defense to ensure calc
        df["exits"] = None
    if "exit_time" not in df.columns:
        df["exit_time"] = None
    # Normalize timestamps for editing
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")    
    if "exit_time" in df.columns:
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")                         #|("")

    df["Potential"] = df.apply(compute_potential, axis=1)                                          #|axis=1 by row; axis=0 by col
    df["Potential_Value"] = (
        pd.to_numeric(df.get("size"), errors="coerce")
        * pd.to_numeric(df.get("Potential"), errors="coerce")
        * pd.to_numeric(df.get("point_value"), errors="coerce")
    )
    df["Risk"] = (
        pd.to_numeric(df.get("stop"), errors="coerce")
        * pd.to_numeric(df.get("point_value"), errors="coerce")
        * pd.to_numeric(df.get("size"), errors="coerce")
    ) 
    df["PnL"] = df.apply(compute_pnl, axis=1)

