#A05_Calc.py
"""
This module prepares journal data for analysis views. 
It cleans trade records, applies filters, and calculates performance tables used by the analysis page.
"""
"""________________________________________________________________________________________________"""
from typing import Any, Sequence
import pandas as pd 
from functools import reduce
from Pages.Calculation.Content.Journal.J03_Calc import compute_potential, compute_pnl
"""________________________________________________________________________________________________"""
"""
Converts a trade duration from raw seconds into an HH:MM:SS text value. 
Missing values are shown as n/a so the analysis table stays readable.
"""
def format_duration(seconds: float) -> str:
    if pd.isna(seconds):                                                                                #|Safety
        return "n/a"
    seconds = max(0, int(seconds))                                                                      #|No negs + int conversion
    h, rem = divmod(seconds, 3600)                                                                      #|Format seconds to hour                                                                    
    m, s = divmod(rem, 60)                                                                              #|Format seconds to minute
    return f"{h:02d}:{m:02d}:{s:02d}"                                                                   #|Converted output of Duration of Trade
"""________________________________________________________________________________________________"""
"""
Creates the enriched dataframe used by the analysis dashboard. 
It converts raw journal columns into clean numeric and datetime fields, 
then adds risk, potential, result, duration, and calendar features.
"""
def prepare_analysis_df(pnl_df: pd.DataFrame) -> pd.DataFrame:
    df = pnl_df.copy()
    df["created_at"] = pd.to_datetime(df.get("created_at"), errors="coerce")
    df["exit_time"] = pd.to_datetime(df.get("exit_time"), errors="coerce")
    df["mfe"] = pd.to_numeric(df.get("mfe"), errors="coerce")
    df["mae"] = pd.to_numeric(df.get("mae"), errors="coerce")
    df["PnL"] = pd.to_numeric(df.get("PnL"), errors="coerce")
    df["entry"] = pd.to_numeric(df.get("entry"), errors="coerce")
    df["exits"] = pd.to_numeric(df.get("exits"), errors="coerce")
    df["size"] = pd.to_numeric(df.get("size"), errors="coerce")
    df["point_value"] = pd.to_numeric(df.get("point_value"), errors="coerce")
    df["direction"] = df.get("direction").astype(str).str.lower()

    df["risk"] = df["size"] * df["point_value"] * df["stop"]
    df["Potential"] = df.apply(compute_potential, axis=1)
    df["Potential_Value"] = df["size"] * df["Potential"] * df["point_value"]
    df["PnL_plus_Potential"] = df["PnL"] + df["Potential_Value"]
    df["is_win"] = df["PnL"] > 0
    df["result"] = df["is_win"].map({True: "Win", False: "Loss"})                                       #|Series getting mask
    df["duration_seconds"] = (df["exit_time"] - df["created_at"]).dt.total_seconds()
    df["duration_minutes"] = df["duration_seconds"] / 60
    df["duration_hms"] = df["duration_seconds"].apply(format_duration)
    df["day_name"] = df["exit_time"].dt.day_name()
    df["month_name"] = df["exit_time"].dt.month_name()
    df["open_hour"] = df["created_at"].dt.hour + df["created_at"].dt.minute / 60.0
    df["close_hour"] = df["exit_time"].dt.hour + df["exit_time"].dt.minute / 60.0
    return df
"""________________________________________________________________________________________________"""
"""
Creates the default structure for one analysis filter condition. 
The returned dictionary matches the fields used by the filter UI and the dataframe filtering logic.
"""
def blank_condition() -> dict[str, Any]:
    return {"field": None, "op": "==", "value": ""}
"""________________________________________________________________________________________________"""
"""
Builds the list of dataframe columns that can be used in analysis filters. 
Technical identifiers are excluded so the user only sees meaningful trade fields.
"""
def available_fields(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if col not in ("trade_db_id", "created_at")]
"""________________________________________________________________________________________________"""
"""
Applies one filter rule to a pandas Series and returns a boolean mask. 
Text operators use string matching, while numeric operators convert the input value before comparing.
"""
def apply_condition(series: pd.Series, operator: str, value: str) -> pd.Series:
    if series.dtype == "O":                                                                             #|str-->tags are str
        if operator == "==":
            return series.fillna("").astype(str) == str(value)                                          #|Returns series where tag is met with operator-cond
        if operator == "!=":
            return series.fillna("").astype(str) != str(value)
        if operator == "contains":
            return series.fillna("").astype(str).str.contains(str(value))
        if operator == "not contains":
            return ~series.fillna("").astype(str).str.contains(str(value))                              #|~ = invertcondition
    else:  # numeric
        try:
            num = float(value)
        except Exception:
            return pd.Series(False, index=series.index)
        if operator == "==": return series == num
        if operator == "!=": return series != num
        if operator == ">": return series > num
        if operator == "<": return series < num
        if operator == ">=": return series >= num
        if operator == "<=": return series <= num
    return pd.Series(True, index=series.index)                                                          #|If both conditions fail, mask of true boolean with series index
"""________________________________________________________________________________________________"""
"""
Applies the user-defined filter groups to the analysis dataframe. 
Conditions inside one group are combined with AND, while separate groups are combined with OR.
"""
def filter_df(df: pd.DataFrame, groups):
    if not groups:
        return df                                                                                       #|Return whole df if no conditions
    group_masks = []
    for g in groups:                                                                                    #|Multiple groups
        cond_masks = []
        for cond in g["conditions"]:                                                                    #|multiple conditions
            field, op, val = cond["field"], cond["op"], cond["value"]                                   #|Condition Format
            if not field:
                continue                                                                                #|Skip iteration if field empty
            cond_masks.append(apply_condition(df[field], op, val))                                      #|Apply boolean mask where this condition is true inside the df
        if cond_masks:
            group_masks.append(reduce(lambda a, b: a & b, cond_masks))                                  #|Connection to AND from group_masks
    if not group_masks:
        return df
    final_mask = reduce(lambda a, b: a | b, group_masks)                                                #|Connection to OR from group_masks
    return df[final_mask]                                                                               #|bool mask
"""________________________________________________________________________________________________"""
"""
Creates a copy of the dataframe and adds a calculated PnL column when all required trade columns exist. 
If required data is missing, it returns the same table shape with an empty PnL field.
"""
def compute_pnl_table(df: pd.DataFrame, required_cols: list[Any]) -> pd.DataFrame:

    pnl_df = df.copy()         
    if not all(c in pnl_df.columns for c in required_cols):                                             #|Check if all required cols are present
        pnl_df["PnL"] = None
        return pnl_df
    pnl_df["PnL"] = pnl_df.apply(compute_pnl, axis=1)                                                   #|PnL Calc for each row
    return pnl_df
"""________________________________________________________________________________________________"""
"""
Calculates the headline statistics shown in the analysis dashboard. 
It separates wins, losses, and breakeven trades, then derives net PnL, 
revenue, loss sum, win rate, and profit factor.
"""
def performance_stats(df: pd.DataFrame, wthr: float, lthr: float):
    stats = {
        "net_pnl": 0.0,
        "win_rate": None,
        "profit_factor": None,
        "wins": 0,
        "losses": 0,
        "breakevens": 0,
        "revenue": 0.0,
        "loss_sum": 0.0,
    }                                                                                                   #|Default dict
    if "PnL" not in df.columns:                                                                         #|Safety to ensure Calculation
        return stats
    pnl = df["PnL"].dropna()
    if pnl.empty:
        return stats

    wins_mask = pnl >= wthr
    losses_mask = pnl <= lthr
    breakeven_mask = ~(wins_mask | losses_mask)
    stats["wins"] = int(wins_mask.sum())
    stats["losses"] = int(losses_mask.sum())
    stats["breakevens"] = int(breakeven_mask.sum()) 
    stats["net_pnl"] = float(pnl.sum())
    stats["revenue"] = float(pnl[wins_mask].sum())
    loss_total = float(pnl[losses_mask].sum())  # negative
    stats["loss_sum"] = loss_total
    if stats["wins"] + stats["losses"] > 0:
        stats["win_rate"] = stats["wins"] / (stats["wins"] + stats["losses"])
    if loss_total < 0:
        stats["profit_factor"] = stats["revenue"] / abs(loss_total) if abs(loss_total) > 0 else None
    return stats

"""________________________________________________________________________________________________"""
"""
Aggregates trade performance by calendar day for the dashboard charts. 
It uses exit time first and falls back to creation time when a trade has no exit timestamp.
"""
def daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    if "PnL" not in df.columns:                                                                         
        return pd.DataFrame(columns=["date", "pnl", "trade_count"])                                     #|Returns dataframe with new pnl col once pnl not  in df
    if "exit_time" not in df.columns and "created_at" not in df.columns:
        return pd.DataFrame(columns=["date", "pnl", "trade_count"])                                     #|Same thing but with exit and entry time
    work = df[["PnL"]].copy()                                                                           #|pnl table
    if "exit_time" in df.columns:                                                                       
        work["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")                            #|Adding new column to pnl table and format it
    else:
        work["exit_time"] = pd.NaT                                                                      #|Else excluded
    if "created_at" in df.columns:                                                  
        work["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    else:
        work["created_at"] = pd.NaT                                                                     #|("...")
    work["date"] = work["exit_time"].dt.date                                                            #|Conversion of exit time to date to create datecol
    work.loc[work["date"].isna(), "date"] = work.loc[work["date"].isna(), "created_at"].dt.date         #|Where date is missing replace with date from created at
    work = work.dropna(subset=["date"])                                                                 #|remove rows where fallback still failed
    if work.empty:
        return pd.DataFrame(columns=["date", "pnl", "trade_count"])                                     #|return empty table if rows are empty
    daily = work.groupby("date").agg(pnl=("PnL", "sum"), trade_count=("PnL", "count")).reset_index()    #|Grouping by date, then reseting that index
    return daily
"""________________________________________________________________________________________________"""
"""
Creates a copy of the dataframe and adds a calculated PnL column when all required trade columns exist. 
If required data is missing, it returns the same table shape with an empty PnL field.
"""
def compute_pnl_table(df: pd.DataFrame, cols: list[Any]) -> pd.DataFrame:
    pnl_df = df.copy()
    if not all(c in pnl_df.columns for c in cols):                                                      #|Ensure Required cols present
        pnl_df["PnL"] = None
        return pnl_df
    pnl_df["PnL"] = df.apply(compute_pnl, axis=1)                                                       #|Function call
    return pnl_df                                                                                       #|Return updated table
"""________________________________________________________________________________________________"""
"""
Prepares chart input data by filling a display column from a backup column and removing incomplete rows. 
This keeps visualizations from receiving empty labels or missing numeric values.
"""
def fill_and_drop(
    df: pd.DataFrame,
    new_col: str,
    replacement_col: str | None = None,
    extra: Sequence[str] | None = None,
) -> pd.DataFrame:
    data = df.copy()
    if replacement_col is not None and replacement_col in data.columns:                                 #|Col to be replaced 
        data[new_col] = data[new_col].fillna(data[replacement_col].astype(str))                         #|New col created and conversed
    subset = [new_col]
    if extra is not None:
        subset.extend(extra)
    data = data.dropna(subset=subset)                                                                   #|New data in which nas should be dropped 
    if data.empty:
        return 
    return data






