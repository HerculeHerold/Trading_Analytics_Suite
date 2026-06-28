#C01_DB_paths.py
"""
This module defines cockpit database path constants. 
It keeps file paths in one place so database helpers can connect consistently.
"""
from pathlib import Path
"""________________________________________________________________________________________________________________"""
BASE_DIR = Path(__file__).resolve().parents[1]                                                                      #|Creates a normalized relative file path to its parent(current folder)
SQL_JOURNAL = BASE_DIR / "Journal.db"
"""________________________________________________________________________________________________________________"""
"""For seed defaults and overall database structure in DB_default.py"""
DEFAULTS_DB = BASE_DIR / "Defaults.db"
"""________________________________________________________________________________________________________________"""
"""For Logs in Cockpit.py"""
LOG_DB_PATH = BASE_DIR / "Log.DB"
"""________________________________________________________________________________________________________________"""
"""
Volatility State via API
Different timeframes got different db's for oversight
"""
TIMEFRAME_DB_DIR = Path("Pages/DB/Timeframe_dbs")
TF_DB_PATHS = {
    "1H": TIMEFRAME_DB_DIR / "vola_1h.db",
    "4H": TIMEFRAME_DB_DIR / "vola_4h.db",
    "D": TIMEFRAME_DB_DIR / "vola_1d.db",
    "W": TIMEFRAME_DB_DIR / "vola_1w.db",
}
"""________________________________________________________________________________________________________________"""
"""Markets txt for market tickers (adding or deleting for example)"""
MARKETS_TXT = BASE_DIR / "Markets.txt"
"""________________________________________________________________________________________________________________"""
