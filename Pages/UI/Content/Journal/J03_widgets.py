#J03_widgtes.py
"""
This file contains journal actions that would make the main page too crowded. 
It handles edited rows, delete actions, and downloadable checklist exports for the journal UI.
Keep as boolean parameter for now and split everything
Boolean Functions for Buttons
"""
"""________________________________________________________________________________________________""" 
import pandas as pd 
import sqlite3 
from Pages.DB.Content.Riskmanagement.R02_DB_paths import SQL_JOURNAL
from Pages.Data.Content.Journal.J03_Datasets import TRADE_COLS, TAG_COLS, TD_COLS, FLOAT_COLS, INT_COLS
from Pages.Calculation.Content.Journal.J03_Calc import normalize_cell
"""________________________________________________________________________________________________"""
"""
Compares the edited journal table with the original dataframe and writes changed fields back to the database. 
Only edited rows and editable columns are updated.
"""
def edit_fields(edited_df: pd.DataFrame, df: pd.DataFrame)-> str:
        trade_updates = {}                                                                                  #|{trade_db_id:{col_name: value}}
        tag_updates = {}                                                                                    #|("...")
        for _, row in edited_df.iterrows():                                                                 #|for each row (index gets ignored _,)
            trade_db_id = int(row["trade_db_id"])                                                           #|val(trade_db_id) into int
            original_row = df.loc[df["trade_db_id"] == row["trade_db_id"]].iloc[0]                          #|Matching Trade_db_id selected
            trade_changes = {}
            tag_changes = {}
            for col in edited_df.columns:
                if col == "trade_db_id":                                                                    #|Skip trade_db_id col                                
                    continue
                new_val = normalize_cell(col, row.get(col), TD_COLS, INT_COLS, FLOAT_COLS)                  #|Conversion of cell (edited cell)
                old_val = normalize_cell(col, original_row.get(col), TD_COLS, INT_COLS, FLOAT_COLS)         #|Conversion of cell (original cell)
                if new_val == old_val:                                                                      #|Skip if no change
                    continue                                                                
                if col in TRADE_COLS:                                                                       #|Separation between Tag and Trade cols                                        
                    trade_changes[col] = new_val                                                            #|add to matching col-identifier 
                elif col in TAG_COLS:
                    tag_changes[col] = new_val
            if trade_changes:                                                                               #|If change in dict add to macro dict under trade_db_id
                trade_updates[trade_db_id] = trade_changes
            if tag_changes:
                tag_updates[trade_db_id] = tag_changes
    #-----DB manipulation
        if trade_updates or tag_updates:                                                                    #|on change of one of those dicts
            con = sqlite3.connect(SQL_JOURNAL)
            with con:
                for trade_db_id, updates in trade_updates.items():                                          #|For every item aka every changed trade
                    for col, val in updates.items():                                                        #|For every column changed     
                        con.execute(
                            f"UPDATE trades SET {col} = ? WHERE id = ?",
                            (val, trade_db_id),
                        )
                for trade_db_id, updates in tag_updates.items():                                            #|("...") for tags
                    for col, val in updates.items():
                        con.execute(
                            f"UPDATE trade_tags SET {col} = ? WHERE trade_db_id = ?",
                            (val, trade_db_id),
                        )
            saved_trades = sum(len(v) for v in trade_updates.values())                                      #|Number of changes, even inner dict from trade_updates via .values()   
            saved_tags = sum(len(v) for v in tag_updates.values())                                          #| ("...")
            return (f"Saved {saved_trades} trade field(s), {saved_tags} tag field(s).")
        else:
            return ("No changes to save.")
"""________________________________________________________________________________________________""" 
"""
Deletes only the journal rows selected in the Streamlit table. 
It reads the selected trade ids and removes those records from storage.
"""
def delete_selected_rows(selected_row: pd.DataFrame) -> int:
    delete_ids = selected_row.loc[selected_row['delete'] == True, "trade_db_id"].tolist()                  #|Creates a list of trade ids that will be deleted
    if delete_ids:
        con = sqlite3.connect(SQL_JOURNAL)
        with con:
            con.executemany("DELETE FROM trades WHERE id = ?", [[int(tid)] for tid in delete_ids])         #|for each trade id ->SQL query
    if sqlite3.Error:
        return "There was an Error in the database"
    con.close()
    return len(delete_ids), delete_ids                                                                     #|Number of Trades that were deleted
"""________________________________________________________________________________________________""" 
"""
Deletes every journal trade from the database. 
The return value reports how many rows were removed so the UI can confirm the action.
"""
def delete_all_rows() -> int:
        con = sqlite3.connect(SQL_JOURNAL)
        with con:
            cur = con.execute("DELETE FROM trades")
        if sqlite3.Error:
            return "There was an Error in the database"
        con.close() 
        return cur.rowcount
"""________________________________________________________________________________________________""" 
"""
Builds an Excel download from the current trade checklist dataframe. 
The file is prepared in memory and exposed through a Streamlit download button.
"""
def download_tradechecklist(df: pd.DataFrame):
    export_lines = []
    for _, row in df.sort_values("trade_db_id", ascending=False).iterrows():
        trade_db_id = int(row["trade_db_id"])
        trade_id = row.get("trade_id", "")
        note_val = row.get("notes") or ""
        export_lines.append(f"Trade ID: {trade_db_id}")
        export_lines.append(f"Trade Code: {trade_id}")
        export_lines.append(note_val)
        export_lines.append("-" * 40)
    export_txt = "\n".join(export_lines).strip()
    return export_txt
