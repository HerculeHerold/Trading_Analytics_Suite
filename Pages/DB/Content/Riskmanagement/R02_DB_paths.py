#RO2_DB_paths.py
"""
This module defines risk-management database path constants. 
It centralizes storage paths used by the risk-management database layer.
"""
"""____________________________________________________________________________________________________"""
from pathlib import Path 
"""____________________________________________________________________________________________________"""
"""
Dynamic path/file handling via BASE_DIR 
"""
BASE_DIR = Path(__file__).resolve().parents[1] 
SQL_JOURNAL = BASE_DIR / "Journal.db"                                                         #|Creates a normalized relative file path to its parent(current folder)
"""____________________________________________________________________________________________________"""
MARKETDATA_DB = BASE_DIR / "Market_data.db"
CURRENT_TRADES_DB = BASE_DIR / "Current_trades.db"
"""____________________________________________________________________________________________________"""

