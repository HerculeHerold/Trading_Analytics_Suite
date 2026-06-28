#J03_DB_Default.py
"""
This module manages journal database schema and queries. 
It creates journal tables, inserts trades and tags, fetches joined records, and updates notes.
"""
from __future__ import annotations
import pandas as pd
import sqlite3
from typing import Any, Dict, List, Tuple
import pandas as pd
from Pages.DB.Content.Riskmanagement.R02_DB_paths import SQL_JOURNAL
"""____________________________________________________________________________________________________"""
"""
Creates the journal and trade-tag tables if they do not already exist. 
The schema separates raw trade execution data from market-state context used later for analysis.
"""
def ensure_journal_schema() -> None:
    con = sqlite3.connect(SQL_JOURNAL)
    con.execute("PRAGMA foreign_key = ON;")
    with con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,

                size INTEGER NOT NULL,
                direction TEXT NOT NULL,
                market TEXT NOT NULL,

                entry REAL NOT NULL,
                stop REAL NOT NULL,
                profit REAL NOT NULL,
                breakeven REAL NOT NULL,
                trailing REAL NOT NULL,

                min_risk REAL NOT NULL,
                max_risk REAL NOT NULL,

                st_atr REAL NOT NULL,
                lt_atr REAL NOT NULL,

                point_value REAL NOT NULL,
                exits REAL,
                exit_time TEXT,
                mfe REAL,
                mae REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS trade_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_db_id INTEGER NOT NULL,   -- references trades.id

                strategy TEXT NOT NULL,
                trend_state TEXT NOT NULL,
                vola_state TEXT NOT NULL,
                term_structure_state TEXT NOT NULL,

                gear INTEGER NOT NULL,
                conviction REAL NOT NULL,
                trend_strength REAL NOT NULL,
                vola_strength REAL NOT NULL,

                gear_state TEXT NOT NULL,
                conviction_state TEXT NOT NULL,
                trend_strength_state TEXT NOT NULL,
                vola_strength_state TEXT NOT NULL,

                FOREIGN KEY (trade_db_id) REFERENCES trades(id) ON DELETE CASCADE   -- If trade in trades deleted, delete here too (CASCADE)
            );
            """
    )
    con.close()
"""____________________________________________________________________________________________________""" 
"""
Inserts one completed trade record into the journal table. 
It maps the prepared trade dictionary to database columns and returns the new trade id.
"""
def insert_trade_sql(trade: Dict[str, Any]) -> int:
    
    ensure_journal_schema()
    con = sqlite3.connect(SQL_JOURNAL)
    con.execute("PRAGMA foreign_key = ON;")
    with con:
        cur = con.execute(
            """
            INSERT INTO trades (
                trade_id, size, direction, market,
                entry, stop, profit, breakeven, trailing,
                min_risk, max_risk, st_atr, lt_atr, point_value, exits, exit_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade["trade_id"],
                trade["size"],
                trade["direction"],
                trade["market"],
                trade["entry"],
                trade["stop"],
                trade["profit"],
                trade["breakeven"],
                trade["trailing"],
                trade["min_risk"],
                trade["max_risk"],
                trade["st_atr"],
                trade["lt_atr"],
                trade.get("point_value", 0.0),
                trade.get("exits"),
                trade.get("exit_time"),
            ),
        )
        trade_db_id = int(cur.lastrowid)                                                                #|id of lastrow
    con.close()
    return trade_db_id                                                                                  #|Referances trades.id 
"""____________________________________________________________________________________________________"""
"""
Stores the cockpit state tags connected to a journal trade. 
It copies market state, strength, conviction, strategy, and score values so later analysis can filter by context.
"""
def insert_trade_tags(trade_db_id: int, state) -> None:
    ensure_journal_schema()                                                                             #|Default

    #Pulling attributes from states 
    strategy = getattr(state, "strategy", "Vola-Reversion")
    trend_state = getattr(state, "trend_state") 
    vola_state = getattr(state, "vol_state")
    term_structure_state = getattr(state, "term_structure_state") 
    gear = getattr(state, "gear")
    conviction = getattr(state, "conviction")
    trend_strength = getattr(state, "trend_strength")
    vol_strength = getattr(state, "vol_strength")
    gear_state = getattr(state, "gear_state") or f"Gear {getattr(state, 'gear')}"
    conviction_state = getattr(state, "conviction_state") 
    trend_strength_state = getattr(state, "trend_strength_state")
    vola_strength_state = getattr(state, "vola_strength_state") 
    
    #Attributes ingestion into Journal
    con = sqlite3.connect(SQL_JOURNAL)
    with con:
        con.execute(
            """
            INSERT INTO trade_tags (
                trade_db_id,
                strategy, trend_state, vola_state, term_structure_state,
                gear, conviction, trend_strength, vola_strength,
                gear_state, conviction_state, trend_strength_state, vola_strength_state
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade_db_id,
                strategy,
                trend_state,
                vola_state,
                term_structure_state,
                gear,
                conviction,
                trend_strength,
                vol_strength,
                gear_state,
                conviction_state,
                trend_strength_state,
                vola_strength_state,
            ),
        )
    con.close()
"""____________________________________________________________________________________________________"""
"""
Loads the latest journal trades from the database for display. 
The limit keeps the UI responsive while still showing the most recent trade history.
"""
def fetch_trades(limit: int = 500) -> List[Tuple]:
    ensure_journal_schema()
    con = sqlite3.connect(SQL_JOURNAL)
    con.execute("PRAGMA foreign_key = ON;")
    cur = con.execute(
        """
        SELECT
            t.trade_id, t.size, t.direction, t.market, t.entry, t.stop, t.profit,
            t.breakeven, t.trailing, t.min_risk, t.max_risk, t.st_atr, t.lt_atr,
            t.point_value, t.exits, t.exit_time,
            t.created_at
        FROM trades t
        ORDER BY t.created_at DESC
        LIMIT ?
        """,
        (int(limit),),
    )
    rows = cur.fetchall()
    con.close()
    return rows
"""____________________________________________________________________________________________________"""
"""
Loads journal trades together with their saved market-state tags.
The joined dataframe is the main input for the analysis dashboard.
"""
def trades_with_tags_df() -> pd.DataFrame:
    ensure_journal_schema()
    con = sqlite3.connect(SQL_JOURNAL)
    con.execute("PRAGMA foreign_key = ON;")
    df = pd.read_sql(
        """
        SELECT
            t.id AS trade_db_id,                                                                        
            t.trade_id, t.size, t.direction, t.market, t.entry, t.stop, t.profit,
            t.breakeven, t.trailing, t.min_risk, t.max_risk, t.st_atr, t.lt_atr,
            t.point_value, t.exits, t.exit_time, t.mfe, t.mae, t.notes,
            t.created_at,
            tg.strategy, tg.trend_state, tg.vola_state, tg.term_structure_state,
            tg.gear, tg.conviction, tg.trend_strength, tg.vola_strength,
            tg.gear_state, tg.conviction_state, tg.trend_strength_state, tg.vola_strength_state
        FROM trades t
        LEFT JOIN trade_tags tg ON tg.trade_db_id = t.id
        ORDER BY t.created_at DESC
        """,
        con,
    )
    con.close()
    return df
"""____________________________________________________________________________________________________"""
"""
Updates journal notes for the selected trade ids. 
Only note text is changed, which keeps analytical trade fields untouched during note editing.
"""
def update_notes(notes_by_trade_db_id: Dict[int, str]) -> None:
    if not notes_by_trade_db_id:                                                                        #|If no notes were provided, stop
        return
    ensure_journal_schema()
    con = sqlite3.connect(SQL_JOURNAL)
    con.execute("PRAGMA foreign_key = ON;")
    with con:
        if notes_by_trade_db_id:
            for trade_db_id, notes in notes_by_trade_db_id.items():
                con.execute(
                    "UPDATE trades SET notes = ? WHERE id = ?",
                    (notes, trade_db_id),
                )
    con.close()
"""____________________________________________________________________________________________________"""



