#J03_DB_paths.py
"""
This module defines journal database path constants. 
It keeps journal storage locations separate from query and UI logic.
"""
"""____________________________________________________________________________________________________"""
from pathlib import Path 
"""____________________________________________________________________________________________________"""
BASE_DIR = Path(__file__).resolve().parents[1]                                                          #|Creates a normalized relative file path to its parent(current folder)
CHECKLIST_PATH = BASE_DIR / "Checklist_Trades.db"
SQL_JOURNAL = BASE_DIR / "Journal.db"
"""____________________________________________________________________________________________________"""
