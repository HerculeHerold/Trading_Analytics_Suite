#C01_DB_default.py
"""
This module manages cockpit database defaults and loading helpers. 
It creates required tables, seeds scoring data, and reads scores, weights, bounds, and market closes.
"""
"""________________________________________________________________________________________________________________"""
import pandas as pd
import sqlite3                                                                                                      
from Pages.DB.Content.Cockpit.C01_DB_paths import DEFAULTS_DB, LOG_DB_PATH, TF_DB_PATHS                            
from typing import Dict                                                                                                                                                                              #|dataclasses for functions
from Pages.Data.Content.Cockpit.C01_DataTables import TF_WEIGHTS, GearScale, ComponentBounds, Weights
from typing import Any
"""________________________________________________________________________________________________________________"""
"""
Opens the cockpit SQLite database connection used by setup and loading helpers. 
Keeping the connection logic in one place makes schema and query functions easier to maintain.
"""
def connect():
    con = sqlite3.connect(DEFAULTS_DB)
    con.execute("PRAGMA foreign_keys = ON;")
    return con
con = connect()
"""________________________________________________________________________________________________________________"""
"""
Creates the cockpit configuration tables if they do not already exist. 
The schema stores state scores, timeframe weights, bounds, global weights, gear scales, and profile inputs.
"""
def ensure_schema():
    con = connect()
    with con:
        con.executescript(
            """
        -- state tables (editable)
        CREATE TABLE IF NOT EXISTS states (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          component   TEXT NOT NULL,   -- 'trend','vix','vvix','cor1m','term_structure',...
          state_name  TEXT NOT NULL,
          dirscore    REAL,            -- may be NULL for some components
          riskscore   REAL NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ux_states
          ON states(component, state_name);

        -- timeframe weights per component
        CREATE TABLE IF NOT EXISTS timeframe_weights (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          component TEXT NOT NULL,
          timeframe TEXT NOT NULL,
          weight    REAL NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ux_tf_w
          ON timeframe_weights(component, timeframe);

        -- bounds for normalization (min/max per input)
        CREATE TABLE IF NOT EXISTS bounds (
          key TEXT PRIMARY KEY,   -- 'sentiment','elliott','market_profile','equity', 'Opening-Drive'
          min REAL NOT NULL,
          max REAL NOT NULL
        );

        -- weights for RiskScore (weights)
        CREATE TABLE IF NOT EXISTS risk_weights (
          key TEXT PRIMARY KEY,   -- 'sentiment','elliott','vola','market_profile','trend','equity','term_structure', 'Opening-Drive'
          weight REAL NOT NULL
        );

        -- gear scales (IFS thresholds)
        CREATE TABLE IF NOT EXISTS gear_scales (
          id INTEGER PRIMARY KEY CHECK (id=1),
          first  REAL NOT NULL,
          second REAL NOT NULL,
          third  REAL NOT NULL,
          fourth REAL NOT NULL,
          fifth  REAL NOT NULL
        );
        """
        )
    con.close()

"""________________________________________________________________________________________________________________"""
"""
Loads all state scores for one cockpit component from the database. 
The result is keyed by state name so selectors and calculations can reuse the same source of truth.
"""
def load_state_table(component: str) -> dict[str, dict[str, float]]:
    con = connect()
    cur = con.execute(
        "SELECT state_name, dirscore, riskscore "
        "FROM states WHERE component=? ORDER BY state_name",
        (component,),                                                                                               #|Tuples with single value
    )
    rows = cur.fetchall()                                                                                           #|Get all Vals
    con.close()                                                                                                     #|Close .db before formatting
    
    out: Dict[str, Dict[str, float]] = {}                                                                           #|Formats the output into dictionary
    for name, d, r in rows:                                                                                         
        out[name] = {"dir": (d if d is not None else 0.0), "risk": float(r)}                                        #|Injects values from Query
    return out
"""________________________________________________________________________________________________________________"""
"""
Loads the configured timeframe weights for one component. 
These weights decide how much intraday, trading, micro, and macro states contribute to the final score.
"""
def load_timeframe_weights(component: str) -> Dict[str, float]:
    con = connect()
    cur = con.execute(
        "SELECT timeframe, weight FROM timeframe_weights WHERE component=?",
        (component,),
    )
    rows = cur.fetchall()
    con.close()
    return {tf: float(w) for tf, w in rows}
"""________________________________________________________________________________________________________________"""
"""
Loads normalization bounds for cockpit components from the database. 
The rows are converted into ComponentBounds objects so score normalization uses typed configuration.
"""
def load_bounds() -> Dict[str, ComponentBounds]:
    con = connect()
    cur = con.execute("SELECT key, min, max FROM bounds")
    row = cur.fetchall()
    d = {k: ComponentBounds(mn, mx) for k, mn, mx in row}                                                           #|Similar logic like above formatting query
    con.close()
    return d
"""________________________________________________________________________________________________________________"""
"""
Loads the global cockpit scoring weights from the database. 
These values define how trend, volatility, term structure, equity, and extra inputs are balanced.
"""
def load_weights() -> Weights:
    con = connect()
    cur = con.execute("SELECT key, weight FROM risk_weights")
    rows = cur.fetchall()
    m = {k: float(w) for k, w in rows}
    con.close()
    return Weights(
        sentiment=m.get("sentiment", 0.10),
        elliott=m.get("elliott", 0.10),
        vola=m.get("vola", 0.30),
        market_profile=m.get("market_profile", 0.15),
        trend=m.get("trend", 0.40),
        equity=m.get("equity", 0.25),
        term_structure=m.get("term_structure", 0.15),
    )
"""________________________________________________________________________________________________________________"""
"""
Loads the gear-scale thresholds from the cockpit database. 
The returned values support turning risk conditions into a practical sizing context.
"""
def load_gear_scale() -> GearScale:
    con = connect()
    cur = con.execute(
        "SELECT first, second, third, fourth, fifth FROM gear_scales WHERE id=1"
    )
    row = cur.fetchone()
    con.close()
    if not row:
        return GearScale(0.6, 0.5, 0.4, 0.3, 0.3)
    return GearScale(*map(float, row))
"""________________________________________________________________________________________________________________"""
"""
Seeds the cockpit database with default states, weights, bounds, and gear settings. 
Insert-or-ignore statements keep the defaults flexible, so running the setup repeatedly does not duplicate rows.
"""
def seed_defaults():
    ensure_schema()
    con = connect()
    with con:
        #Trend states
        trend_states = [                                                                                            #|List with individual tupples for each state ->See all below
            ("Momentum Up",   3, 0.0),
            ("Trendy Up",     3, 1.0),
            ("Choppy Up",     1, 2.0),
            ("Sideways",      0, 5.0),
            ("Choppy Down",  -1, 2.0),
            ("Trendy Down",  -3, 1.0),
            ("Momentum Down", -3, 0.0),
        ]
        for n, d, r in trend_states:
            con.execute(
                "INSERT OR IGNORE INTO states(component,state_name,dirscore,riskscore) "
                "VALUES('trend',?,?,?)",
                (n, d, r),
            )
        #Opening Drive
        opening_drive_states = [
            ("Up",1, 0.5),
            ("Sideways",0, 1.0),
            ("Down",-1, 0.5),
        ]
        for n, d, r in opening_drive_states:
            con.execute(
                "INSERT OR IGNORE INTO states(component,state_name,dirscore,riskscore) "
                "VALUES('Opening-Drive',?,?,?)",
                (n, d, r),
            )
        #VIX/VVIX/COR1M states (up/neutral/down)
        for comp in ("VIX", "VVIX", "COR1M"):
            base = [
                ("Up",      1, 0.0),
                ("Neutral", 0, 1.0),
                ("Down",   -1, 0.0),
            ]
            for n, d, r in base:
                con.execute(
                    "INSERT OR IGNORE INTO states(component,state_name,dirscore,riskscore) "
                    "VALUES(?,?,?,?)",
                    (comp, n, d, r),
                )

        #Term-Structure states (Contango / Neutral / Backwardation)
        term_states = [
            ("Contango",       1.0, 0.5),  
            ("Neutral",        0.0, 1),
            ("Backwardation",  -1.0, 0.5),  
        ]
        for n, d, r in term_states:
            con.execute(
                "INSERT OR IGNORE INTO states(component,state_name,dirscore,riskscore) "
                "VALUES('term_structure',?,?,?)",
                (n, d, r),
            )

        #Timeframe weights
        tfw = [
            # trend
            ("trend", "intra",   0.10),
            ("trend", "trading", 0.20),
            ("trend", "micro",   0.30),
            ("trend", "macro",   0.40),
            # vola (vix/vvix/cor1m)
            ("vix",   "micro", 0.15),
            ("vix",   "meso",  0.20),
            ("vix",   "macro", 0.30),
            ("vix",   "mega",  0.35),
            ("vvix",  "micro", 0.15),
            ("vvix",  "meso",  0.20),
            ("vvix",  "macro", 0.30),
            ("vvix",  "mega",  0.35),
            ("cor1m", "micro", 0.15),
            ("cor1m", "meso",  0.20),
            ("cor1m", "macro", 0.30),
            ("cor1m", "mega",  0.35),
            # term-structure 
            ("term_structure", "shortterm", 0.40),
            ("term_structure", "nearterm",  0.30),
            ("term_structure", "midterm",   0.20),
            ("term_structure", "longterm",  0.10),
        ]
        for c, t, wtf in tfw:
            con.execute(
                "INSERT OR IGNORE INTO timeframe_weights(component,timeframe,weight) "
                "VALUES(?,?,?)",
                (c, t, wtf),
            )

        # --- Bounds (extra inputs)
        defaults_bounds = [
            ("sentiment",      0, 1),
            ("elliott",        0, 1),
            ("market_profile", 0, 1),
            ("equity",         0, 1),
            ("Opening-Drive",         -1, 1),
        ]
        for k, mn, mx in defaults_bounds:
            con.execute(
                "INSERT OR IGNORE INTO bounds(key,min,max) VALUES(?,?,?)",
                (k, mn, mx),
            )

        # --- Risk weights (meta)
        for k, wval in [
            ("sentiment",      0.10),
            ("elliott",        0.10),
            ("vola",           0.60),
            ("market_profile", 0.15),
            ("trend",          0.70),
            ("equity",         0.25),
            ("term_structure", 0.20),
        ]:
            con.execute(
                "INSERT OR IGNORE INTO risk_weights(key,weight) VALUES(?,?)",
                (k, wval),
            )

        # --- Gear scales
        con.execute(
            "INSERT OR IGNORE INTO gear_scales(id,first,second,third,fourth,fifth) "                                
            "VALUES(1,0.60,0.50,0.40,0.30,0.30)"
        )

        # --- Elliott Waves (Impuls / Korrektur)
        for n, d, r in [
            ("Impulswelle",    1, 0.0),
            ("Korrekturwelle", -1, 1.0),
        ]:
            con.execute(
                "INSERT OR IGNORE INTO states(component,state_name,dirscore,riskscore) "
                "VALUES('elliott_type',?,?,?)",
                (n, d, r),
            )

        # --- Market Profile Day types
        for n, d, r in [
            ("Trend-Day",          2, 0),
            ("Normal-Day",         0, 1),
            ("P-Day",              1, 0.6),
            ("b-Day",              1, 0.6),
            ("Double-Distribution",0, 0.2),
        ]:
            con.execute(
                "INSERT OR IGNORE INTO states(component,state_name,dirscore,riskscore) "
                "VALUES('market_profile_day',?,?,?)",
                (n, d, r),
            )

        # --- Sentiment sub-variables
        for comp in ("sent_underlying", "sent_vola_seasonal", "sent_aaii", "sent_fng"):
            for n, r in [
                ("Negative", 0.0),
                ("Neutral",  1.0),
                ("Positive", 0.0),
            ]:
                con.execute(
                    "INSERT OR IGNORE INTO states(component,state_name,dirscore,riskscore) "
                    "VALUES(?,?,NULL,?)",
                    (comp, n, r),
                )

    con.close()
"""________________________________________________________________________________________________________________"""
"""
Creates the cockpit logging tables used for market-state snapshots and change history. 
The schema stores both the latest calculated state and historical changes.
"""
def ensure_log_schema() -> None:
    con = sqlite3.connect(LOG_DB_PATH)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS cockpit_log (
                c_nr INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_text TEXT,
                ts_unix REAL,
                change_type TEXT,
                timeframe TEXT,
                metric_changed TEXT,
                prior_value TEXT,
                value_now TEXT
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS cockpit_log_values (
                c_nr INTEGER PRIMARY KEY,
                trend_score_before REAL,
                trend_score_after REAL,
                vol_score_before REAL,
                vol_score_after REAL,
                conviction_before REAL,
                conviction_after REAL,
                term_score_before REAL,
                term_score_after REAL
            )
            """
        )                                                                                       #|Default databank for log-changes
        cols = {
            row[1]
            for row in con.execute("PRAGMA table_info(cockpit_log)").fetchall()                 #|Fetching schema info of that specific col
        }                                                                                       #|row[1] = column name
        if "timeframe" not in cols:
            con.execute("ALTER TABLE cockpit_log ADD COLUMN timeframe TEXT")
        value_cols = {
            row[1]
            for row in con.execute("PRAGMA table_info(cockpit_log_values)").fetchall()         #|Fetching schema info of that specific col
        }
        for col_name in (
            "trend_score_before",
            "trend_score_after",
            "vol_score_before",
            "vol_score_after",
            "conviction_before",
            "conviction_after",
            "term_score_before",
            "term_score_after",
        ):
            if col_name not in value_cols:                                                    #|Defense
                con.execute(
                    f"ALTER TABLE cockpit_log_values ADD COLUMN {col_name} REAL"
                )
        con.commit()
    finally:
        con.close() 
"""________________________________________________________________________________________________________________"""
"""
Fetches the latest close values for each symbol and timeframe label requested by the cockpit. 
The nested result lets API-driven volatility states compare markets across multiple timeframes.
"""
def fetch_timeframe_close(tf_labels: dict[str, list[str]], 
                          symbols: list[str], 
                          limit: int = 5000) -> dict[str, dict[str, pd.Series]]:
    item_closes : dict[str, dict[str[list[float]]]] = {}
    for item in symbols:
        item_closes[item] = {}
        for tf in tf_labels[item]:
                db_path = TF_DB_PATHS.get(tf)
                if db_path is None or not db_path.exists():
                    item_closes[item][tf] = []
                    continue                                                                                        #|For type consistency just store a new --->Code keeps working
                con = sqlite3.connect(db_path)
                rows = con.execute(
                    """
                    SELECT bar_time, close
                    FROM ohlc
                    WHERE symbol = ? AND bar_size = ?
                    ORDER BY bar_time DESC
                    LIMIT ?
                    """,
                    (item, tf, limit),                                                                              #|Parameter inputs
                ).fetchall()
                if not rows:
                    item_closes[item][tf]
                    continue
                item_closes[item][tf] = pd.Series([float(close) for _bar_time, close in rows])
                con.close()
    return item_closes
"""________________________________________________________________________________________________________________"""
"""
Converts a set of timeframe states into one instrument-level score. 
It averages available component states and ignores missing values so incomplete data can still be displayed.
"""
def instrument_score(tf_states: dict[str, str]) -> float | None:
    total = 0.0
    weight_sum = 0.0
    for tf, state in tf_states.items():                                                                     #|For every timeframe look at the states
        if state == "n/a" or state is None: 
            return None                                                                                     #|Defense if single state is none whole state is none
        weight = TF_WEIGHTS[tf]
        con = connect()
        score = con.execute("SELECT dirscore FROM states WHERE state_name = ?", state).fetchone
        con.close()
        total += weight * score
        weight_sum += weight
    if weight_sum == 0:
        return None
    return total / weight_sum
"""________________________________________________________________________________________________"""
"""
Fetches database score rows for several cockpit components at once. 
The grouped result is used to build selectbox options and calculation lookup maps efficiently.
"""
def fetch_scores_by_state(components: list[str])->dict[str, list[Any]]: 
    con = connect()
    component_vals = {}
    for component in components:                                                                                   
        rows = con.execute(                                                                                 #|Connection to the database
            "SELECT state_name, dirscore, riskscore "                                                       
            "FROM states WHERE component=? ORDER BY state_name",                                            
            (component,),                                                                                   #|loads the options of the "component" from the database
        ).fetchall() 
        component_vals[component] = rows                                                                    #|fetchall=get all
    con.close()                                                                                             #|returns all options and the scores
    return component_vals
"""________________________________________________________________________________________________________________"""
"""
Loads state score dictionaries for multiple components in one pass. 
This prepares the calculation layer with every component lookup it needs for a cockpit run.
"""
def load_states_per_component(components: list[str]) -> dict[str, dict[str, dict[str, float]]]:
    con = connect()
    component_states = {}
    for item in components:
        rows = con.execute(
            "SELECT state_name, dirscore, riskscore "
            "FROM states WHERE component=? ORDER BY state_name",
            (item,),                                                                                               
        ).fetchall()
        component_states[item] = rows 
    con.close()                                                                                                     
    
    out: dict[str, dict[str, dict[str, float]]] = {}                                                                           
    for name, state, d, r in rows:                                                                                         
        out[name] = {state:{"dir": (d if d is not None else 0.0), "risk": float(r)}}                                        
    return out
"""________________________________________________________________________________________________________________"""
"""
Loads timeframe-weight dictionaries for multiple components in one pass. 
The result keeps component scoring fast and avoids repeated database queries.
"""
def load_timeframe_weights_per_component(components: list[str]) -> dict[str, dict[str, float]]:
    con = connect()
    component_tf_weights = {}
    for item in components:
        rows = con.execute(
            "SELECT timeframe, weight FROM timeframe_weights WHERE component=?",
            (item,),
        ).fetchall
        component_tf_weights[item] = rows
    con.close()
    out: dict[str, dict[str, float]] = {}                                                                           
    for name, tf, weight in rows:                                                                                         
        out[name] = {tf:{"weight": (weight if weight is not None else 0.0)}}                                        
    return out
