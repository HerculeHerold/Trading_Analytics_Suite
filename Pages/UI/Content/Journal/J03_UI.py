#J03_Journal.py
"""
This Streamlit page renders the trading journal. 
It displays saved trades, allows editing notes and selected fields, and exposes export and delete actions.
"""
"""________________________________________________________________________________________________""" 
"""
This is the User-Interface of the UI Page
"""
"""________________________________________________________________________________________________""" 
import io as io
from datetime import datetime
import streamlit as st
from Pages.DB.Content.Journal.J03_DB_Default import ensure_journal_schema, trades_with_tags_df, update_notes
from Pages.Calculation.Content.Journal.J03_Calc import calc_row_vals
from Pages.Data.Content.Journal.J03_Datasets import create_Trade_Checklist
from Pages.UI.Content.Journal.J03_widgets import download_tradechecklist, edit_fields, delete_selected_rows
"""________________________________________________________________________________________________""" 
def J03_main():

    ensure_journal_schema()                                                                                 #|DB Schema safety
    st.set_page_config("Journal", layout="wide")
    st.header("Journal")
    st.divider()
    df = trades_with_tags_df()                                                                  
    checklist_template = create_Trade_Checklist()
    calc_row_vals(df)
    delete_df = df.copy()
    delete_df["delete"] = False
    """________________________________________________________________________________________________""" 
    """
    Dataeditor for Data manipulation and editing individual trades via dataframe 
    """
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "trade_db_id": st.column_config.TextColumn("ID", disabled=True),
            "exits": st.column_config.NumberColumn("Exits", help="Set exit price once trade is closed"),
            "exit_time": st.column_config.DatetimeColumn("Exit Time", format="YYYY-MM-DD HH:mm:ss"),
            "created_at": st.column_config.DatetimeColumn("Created At", format="YYYY-MM-DD HH:mm:ss"),
        },
        disabled=["trade_db_id", "PnL", "Risk"],
        key="trades_editor",
    )

    if st.button("Save changes"):
        edit_fields(edited_df, df)

    """________________________________________________________________________________________________"""
    """
    Data editor for deleting selected trades
    """ 
    selected_rows = st.data_editor(
        delete_df[["trade_db_id", "trade_id", "market", "delete"]],
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "trade_db_id": st.column_config.TextColumn("ID", disabled=True),
            "delete": st.column_config.CheckboxColumn("Delete"),
        },
        disabled=["trade_db_id", "trade_id", "market", "direction"],
        key="trades_delete_editor",
    )
    if st.button("Delete selected Rows"):
        delete_selected_rows(selected_rows)
    """________________________________________________________________________________________________""" 
    """
    Header
    """
    st.subheader("Trade Notes")
    if df.empty:
        st.info("No trades available.")
    """________________________________________________________________________________________________""" 
    """
    Number of trade notes being shown.
    """
    max_id = 20
        #max_id = int(df["trade_db_id"].max())
    show_count = st.number_input(
        "How many trades to show?",
        min_value=1,
        max_value=max_id,
        value=min(20, max_id),
        step=1,
    )
    """________________________________________________________________________________________________"""
    """
    with .split()
        ->trade_id = "ES_1713783600"
        ->parts = ["ES", "1713783600"]
    --->See Riskmanagement trade_id creation->Conversion happens here again (f"{selected_market}_{int(time.time())}")
    """
    df_notes = df.sort_values("trade_db_id", ascending=False).head(int(show_count))
    for _, row in df_notes.iterrows():                                                                  #|For each row/trade
        trade_id = row.get("trade_id", "")
        trade_db_id = int(row["trade_db_id"])
        note_val = row.get("notes") or checklist_template
        entry_time_txt = "n/a"
        if trade_id and isinstance(trade_id, str) and "_" in trade_id:                                  #|Securing trade_id structure
            parts = trade_id.split("_")
            if len(parts) >= 2 and parts[1].isdigit():                                                  #|UNIX timestamp conversion
                entry_time_txt = datetime.fromtimestamp(int(parts[1])).strftime("%Y-%m-%d %H:%M:%S")    #|Getting the second part (numeric) and converting it into a timestamp 
        with st.expander(f"Trade ID {trade_db_id}"):
            with st.form(key=f"note_form_{trade_db_id}"):
                st.caption(f"Trade ID: {trade_id}" if trade_id else "Trade ID: n/a")
                st.caption(f"Entry Time: {entry_time_txt}")
                note_text = st.text_area("Notes", value=note_val, height=120)
                if st.form_submit_button("Save note"):
                    update_notes(notes_by_trade_db_id={trade_db_id: note_text})
                    st.success("Note saved.")

    st.subheader("Export Notes")
    st.download_button("Download Trade Checklists", download_tradechecklist(df))
    st.divider()

if __name__ == "__main__":
    J03_main()
