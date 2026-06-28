Trading Analytics Suite
=======================

This application is a modular Streamlit application for structured
analysis, planning, and review of trading decisions. The project combines a
market cockpit, risk management, trade journal, and performance analysis in a
local demo version with prepared SQLite sample data.

The application was built to solve several common problems in a trading
workflow:

- Market and volatility states are made visible and comparable.
- Risk, position size, stop, take-profit, and trade plan values are calculated
  in one central workflow.
- Planned trades can be transferred from risk management into the journal.
- Journal data can be reviewed, filtered, and analyzed visually.
- All functional areas are clearly separated, which makes the code easier to
  maintain, test, and extend.


Project Idea
------------

Many trading tools mix database access, calculations, and UI code inside one
large script. This project intentionally separates those responsibilities into
dedicated modules. This keeps every file easy to understand from a functional
point of view: database files load and store data, data files hold static
configuration, calculation files compute values, and UI files display those
values in Streamlit.

The application is intended as a public demo version. It includes local SQLite
databases with sample data so that the pages can be started and tested
immediately.


Main Features
-------------

1. Cockpit
   The cockpit evaluates market, trend, volatility, and term-structure states.
   These inputs are converted into scores and visual gauges that support a fast
   market overview.

2. Riskmanagement
   The risk management page calculates position size, risk, ATR-based values,
   stop-loss, take-profit, breakeven, trailing start, correlation, and beta.
   Planned trades can be saved and processed later.

3. Journal
   The journal displays saved trades, allows editing of exit values and notes,
   and calculates metrics such as PnL and trade potential.

4. Analysis
   The analysis page evaluates journal data. It displays performance metrics,
   daily results, equity curve, efficiency, trade duration, categories, and
   filterable trade groups.


Module Structure
----------------

The project follows a clear separation of responsibilities between modules:

- DB - Databases
  This module contains database paths, SQLite schemas, insert, update, and
  fetch functions, as well as the local sample databases.

- Data - Data
  This module contains static tables, constants, configurations, state
  definitions, and fixed selection values.

- UI - User Interface
  This module contains the Streamlit pages, widgets, charts, and visible layout
  elements.

- Calculation - Calculations
  This module contains business logic, score calculations, risk management
  formulas, performance evaluations, and mathematical helper functions.


Folder Structure
----------------

The program is divided into the modules described above. Every software page
follows the same storage pattern:

Project_Folder\Module\Content\Software_page\File_name

Examples:

- Pages\UI\Content\Cockpit\C01_UI.py
- Pages\DB\Content\Journal\J03_DB_Default.py
- Pages\Data\Content\Riskmanagement\R02_DataTables.py
- Pages\Calculation\Content\Analysis\A05_Calc.py

The Streamlit navigation is intentionally kept as a thin start and wrapper
structure in the root and Pages area:

- Home.py
- Pages\C01.py
- Pages\R02.py
- Pages\J03.py
- Pages\A05.py

These files import the actual UI functions from the modular project structure.
This keeps the Streamlit sidebar usable without dissolving the functional
folder architecture.


Simplified Project Tree
-----------------------

Analysissheet_Python
|
+-- Home.py
+-- README.txt
+-- Pages
    |
    +-- C01.py
    +-- R02.py
    +-- J03.py
    +-- A05.py
    |
    +-- DB
    |   +-- Content
    |   |   +-- Cockpit
    |   |   +-- Journal
    |   |   +-- Riskmanagement
    |   |   +-- Defaults.db
    |   |   +-- Journal.db
    |   |   +-- Current_trades.db
    |   |   +-- Market_data.db
    |   |   +-- Log.DB
    |   |   +-- Checklist_Trades.db
    |   +-- Timeframe_dbs
    |
    +-- Data
    |   +-- Content
    |       +-- Analysis
    |       +-- Cockpit
    |       +-- Journal
    |       +-- Riskmanagement
    |
    +-- Calculation
    |   +-- Content
    |       +-- Analysis
    |       +-- Cockpit
    |       +-- Journal
    |       +-- Riskmanagement
    |
    +-- UI
        +-- Content
            +-- Analysis
            +-- Cockpit
            +-- Journal
            +-- Riskmanagement


Application Requirements
------------------------

Required software:

- Python 3.10 or newer
- pip
- SQLite support

SQLite does not need a separate driver installation for this project. The app
uses Python's built-in sqlite3 module.

Required Python packages:

- streamlit
- pandas
- altair
- streamlit-echarts
- streamlit-autorefresh

Recommended installation command:

pip install streamlit pandas altair streamlit-echarts streamlit-autorefresh


Run The Application
-------------------

Open a terminal in the project folder and start Streamlit with:

streamlit run Home.py

After startup, Streamlit opens the application in the browser. The available
pages appear in the sidebar:

- C01 - Cockpit
- R02 - Riskmanagement
- J03 - Journal
- A05 - Analysis


Database Notes
--------------

The project uses local SQLite databases inside Pages\DB. The included databases
contain sample data for demonstration and testing. They are not intended to
represent live broker data or private trading records.

Important database files:

- Defaults.db stores default cockpit states, bounds, weights and gear settings.
- Market_data.db stores sample OHLC market data.
- Journal.db stores sample journal trades and tag information.
- Current_trades.db stores currently planned or open trades.
- Log.DB stores cockpit state-change logs.
- Timeframe_dbs contains timeframe-specific volatility sample data.


Development Notes
-----------------

When adding a new software page, keep the existing architecture:

Project_Folder\Module\Content\Software_page\File_name

For example, a new page named Portfolio should place its files like this:

- Pages\UI\Content\Portfolio\P01_UI.py
- Pages\DB\Content\Portfolio\P01_DB_Default.py
- Pages\Data\Content\Portfolio\P01_DataTables.py
- Pages\Calculation\Content\Portfolio\P01_Calc.py

This keeps UI, data, database access, and calculations separated from the
beginning.


Public Demo Scope
-----------------

This repository is a portfolio/demo version of a trading analytics workflow. It
shows the structure, calculations, UI flow and database design of the project
with local sample data. It is not financial advice and should not be used as an
automated trading system without further validation, broker integration checks
and production-level risk controls.
