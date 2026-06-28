#RO2_DB_default.py
"""
This file owns the database operations for currently open trades. 
It creates the table, inserts active trades, fetches market prices, and updates related journal exits.
CURRENT_TRADES_DB is the database file that stores current trades that are not closed yet. 
"""
"""____________________________________________________________________________________________________"""
import sqlite3
from Pages.DB.Content.Riskmanagement.R02_DB_paths import CURRENT_TRADES_DB, MARKETDATA_DB, SQL_JOURNAL
from Pages.DB.Content.Journal.J03_DB_Default import ensure_journal_schema
from Pages.Calculation.Content.Riskmanagement.R02_Calc import market_to_symbol
from Pages.Data.Content.Riskmanagement.R02_DataTables import ATR_BAR_SIZE
import pandas as pd 
from typing import Any 
"""____________________________________________________________________________________________________"""
"""
Creates or upgrades the table used to track currently open trades. 
The schema includes trade details, risk metrics, cockpit states, and optional broker identifiers.
"""
def ensure_current_trades_schema() -> None:
    con = sqlite3.connect(CURRENT_TRADES_DB)
    with con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS current_trades (
                --Trade Specific inputs
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                size INTEGER NOT NULL,
                strategy TEXT NOT NULL,
                direction TEXT NOT NULL,
                market TEXT NOT NULL,

                entry REAL NOT NULL,
                stop REAL NOT NULL,
                profit REAL NOT NULL,
                breakeven REAL NOT NULL,
                trailing REAL NOT NULL,
                
                --Other variables
                min_risk REAL NOT NULL,
                max_risk REAL NOT NULL,
                st_atr REAL NOT NULL,
                lt_atr REAL NOT NULL,
                point_value INT NOT NULL)
            """
        )
    con.close()
"""____________________________________________________________________________________________________"""
"""
Writes one active trade payload into the current-trades table. 
The function stores both trade execution fields and context fields so the trade can later be monitored or closed.
"""
def insert_current_trade(payload: dict) -> None:
    ensure_current_trades_schema()
    con = sqlite3.connect(CURRENT_TRADES_DB)
    with con:
        con.execute(
            """
            INSERT OR IGNORE INTO current_trades (
                --Trade Specific inputs
                trade_id, created_at, size, strategy, direction, market, 
                entry, stop, profit, breakeven, trailing, 
                min_risk, max_risk, st_atr, lt_atr, point_value
                
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (   #Trade Specific inputs
                payload["trade_id"],
                payload["created_at"],
                payload["size"],
                payload["strategy"],
                payload["direction"],
                payload["market"],

                payload["entry"],
                payload["stop"],
                payload["profit"],
                payload["breakeven"],
                payload["trailing"],

                payload["min_risk"],
                payload["max_risk"],
                payload["st_atr"],
                payload["lt_atr"],
                payload["point_value"]
            ),
        )
    con.close()
"""____________________________________________________________________________________________________"""
"""
Loads all open trades from the risk-management database into a dataframe. 
Empty storage returns an empty dataframe instead of failing the Streamlit table.
"""
def load_current_trades() -> pd.DataFrame:
    if not CURRENT_TRADES_DB.exists():                                                                  #|Safety 
        return pd.DataFrame()
    con = sqlite3.connect(CURRENT_TRADES_DB)
    try:
        df = pd.read_sql("SELECT * FROM current_trades ORDER BY created_at DESC", con)                  #|reads the Database as pd
    finally:
        con.close()
    return df
"""____________________________________________________________________________________________________"""
"""
Retrieves the newest close price for the selected market symbol. 
This gives the risk page a live reference price for open-trade calculations.
"""
def latest_close_for_market(market: str) -> float | None:
    if not MARKETDATA_DB.exists():
        return None                                                                                     #|Safety (Defense)
    symbol = market_to_symbol(market)                                                                   #|Conversion of market symbol input     
    con = sqlite3.connect(MARKETDATA_DB)                                                            
    try:
        row = con.execute(
            """
            SELECT close
            FROM ohlc
            WHERE symbol = ? AND (bar_size = ? OR bar_size IS NULL)
            ORDER BY bar_time DESC
            LIMIT 1
            """,
            (symbol, ATR_BAR_SIZE),
        ).fetchone()
    finally:
        con.close()
    if not row:
        return None
    return float(row[0])                                                                                #|last index of row
"""____________________________________________________________________________________________________"""
"""
Writes exit price and exit time back to the linked journal trade. 
This connects the open-trade tracker with the completed-trade journal record.
"""
def update_journal_exit(trade_id: str, exit_price: float, exit_time: str) -> None:
    ensure_journal_schema()                                                                             #|Default
    con = sqlite3.connect(SQL_JOURNAL)
    with con:
        con.execute(
            "UPDATE trades SET exits = ?, exit_time = ? WHERE trade_id = ?",                            #|Ingesting into Journal
            (exit_price, exit_time, trade_id),                                                          #|latest_close_for_market() as helper here
        )
    con.close()
"""____________________________________________________________________________________________________"""
"""
Removes one open trade from the current-trades table by id. 
It is used when a trade is closed or manually deleted from the risk-management page.
"""
def delete_current_trade(trade_id: str) -> None:
    if not CURRENT_TRADES_DB.exists():                                                                  
        return None                                                                                     #|Safety                                         
    con = sqlite3.connect(CURRENT_TRADES_DB)
    with con:
        con.execute("DELETE FROM current_trades WHERE trade_id = ?", (trade_id,))
    con.close()
"""____________________________________________________________________________________________________"""
"""
Fetches close-price series needed for correlation, beta, and ATR context. 
It queries the market-data table for the selected symbol and bar sizes used by the risk page.
"""
def fetch_closes(symbol:str, corr_bar_size:Any, atr_bar_size: Any):
    if not MARKETDATA_DB.exists():
            return []                                                                                   #|Defense
    con = sqlite3.connect(MARKETDATA_DB)
    try:
        rows = con.execute(
            """
            SELECT bar_time, close, bar_size
            FROM ohlc
            WHERE symbol = ? AND (bar_size = ? OR bar_size = ? OR bar_size IS NULL)
            ORDER BY bar_time ASC
            """,
            (symbol, corr_bar_size, atr_bar_size),
        ).fetchall()
    finally:
        con.close() 
    if not rows:                                                                                        #|Defense 
        return []  
    return rows 
"""____________________________________________________________________________________________________"""
"""
Fetches high, low, and close rows for ATR calculation. 
It requests enough history to cover both the short-term and long-term ATR windows.
"""
def fetch_hlc(shortterm_atr_l: int, longterm_atr_l: int, symbol: str):
    if shortterm_atr_l <= 0 or longterm_atr_l <= 0:                                                     #|Defense for securing safe calculation                              
            return []
    if not MARKETDATA_DB.exists():                                                                      #|Defense for securing database
        return []
    con = sqlite3.connect(MARKETDATA_DB)
    try:
        lookback = max(shortterm_atr_l, longterm_atr_l) + 1
        rows = con.execute(
            """
            SELECT high, low, close
            FROM ohlc
            WHERE symbol = ? AND (bar_size = ? OR bar_size IS NULL)
            ORDER BY bar_time DESC
            LIMIT ?
            """,
            (symbol, ATR_BAR_SIZE, lookback),
        ).fetchall()
    finally:
        con.close()
    if not rows:
        return []
    return rows 
