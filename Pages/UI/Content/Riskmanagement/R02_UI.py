# RO2_UI.py
"""
This Streamlit page renders the risk-management workflow. 
It collects market, position, stop, target, and state inputs, then calculates and stores the trade plan.
"""
"""____________________________________________________________________________________________________"""
import streamlit as st
import time
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from Pages.Data.Content.Cockpit.C01_DataTables import MARKETS
from Pages.Data.Content.Riskmanagement.R02_DataTables import(POINT_VALUES, 
                                                                TICK_VALUES,
                                                                GEAR_MULT,
                                                                CORR_LOOKBACK,
                                                                ATR_BAR_SIZE,
                                                                CORR_BAR_SIZE,
                                                                ensure_defaults, 
                                                                )
from Pages.DB.Content.Journal.J03_DB_Default import insert_trade_tags, insert_trade_sql
from Pages.Calculation.Content.Riskmanagement.R02_Calc import (market_to_symbol, 
                                                                compute_atr, 
                                                                returns_series,
                                                                align_returns, 
                                                                round_to_step,
                                                                stop_loss_calc,
                                                                tradingplan_value,
                                                                )
from Pages.DB.Content.Riskmanagement.R02_DB_Default import (insert_current_trade, 
                                                            latest_close_for_market, 
                                                            ensure_current_trades_schema,
                                                            update_journal_exit, 
                                                            delete_current_trade, 
                                                            load_current_trades, 
                                                            fetch_closes,
                                                            fetch_hlc
                                                            )
from Pages.UI.Content.Riskmanagement.R02_Tradingplan import render_trading_plan
from Pages.Calculation.Content.Riskmanagement.R02_Math_Functions import correlation, beta
from Pages.Calculation.Content.Cockpit.C01_State_Logging import get_state
"""____________________________________________________________________________________________________"""
def R02_main():
    """
    Ensuring database format for consistent trade-logging
    """
    ensure_defaults() 
    markets = MARKETS
    directions = ["Long", "Short"]
    """____________________________________________________________________________________________________"""
    """
    Top Risk-Settings with number inputs 
    """

    st.set_page_config("Riskmanagement", layout="wide")
    l, lm, mm, rm, r = st.columns(5)
    with l:
        st.header("Riskmanagement")
    with lm:
        st.number_input("Equity", min_value=0, step=1, key="rm_equity")
    with mm:
        st.number_input("MAX Buying Power", min_value=0, step=1, key="rm_max_bp")
    with rm:
        st.number_input("Trade Risk (%)", min_value=0.0, step=0.1, key="rm_trade_risk")
    with r:
        st.number_input("MAX Daily Risk (%)", min_value=0.0, step=0.1, key="rm_max_daily_risk")
    st.divider()
    st.number_input("Number of open Positions", min_value=1, step=1, key="rm_num_pos")
    st.number_input("Number of Contracts", min_value=1, step=1, key="rm_num_contracts")
    num_pos = int(st.session_state["rm_num_pos"])
    num_contracts = int(st.session_state["rm_num_contracts"])
    """____________________________________________________________________________________________________"""
    """
    Selectboxes values and keys in sessionstate for optional logging or background calculation
    """
    st.subheader("Trade-Metrics")
    left, leftmiddle, rightmiddle, right = st.columns(4)
    with left:
        entry = st.number_input("Entry", step=1.0)
        direction_value = st.selectbox(
            "Direction", options=directions, key="dr")

    with leftmiddle:
        market_value = st.selectbox("Market", options=markets, key="mkt")
        market_state = get_state(market_value)                                                                  #|Gets market STATES of the current market
        strategy_options = ["Vola-Reversion", "Vola-Momentum"]
        trend_strength = float(getattr(market_state, "trend_strength", 0.0))                                    #|Unpacking states for each market  
        trend_state = getattr(market_state, "trend_state", "")                                              
        vola_state = getattr(market_state, "vol_state", "")                                                 
        trend_strength_state = getattr(market_state, "trend_strength_state", "")
        vola_strength_state = getattr(market_state, "vola_strength_state", "")
        strategy = st.selectbox("Strategy", options=strategy_options, key="str")
        
    with rightmiddle:
        left_atr, right_atr = st.columns(2)
        with left_atr:
            st_atr = st.number_input(
                "Shortterm ATR length",
                min_value=1,
                step=1,
                value=st.session_state.get("st_atr_len", 9),
            )
            lt_atr = st.number_input(
                "Longterm ATR length",
                min_value=1,
                step=1,
                value=st.session_state.get("lt_atr_len", 50),
            )
        with right_atr:
            st_market = st.session_state.get("mkt", markets[0])
            st_symbol = market_to_symbol(st_market)
            st_len = int(
                st.session_state.get(st.session_state.get("st_atr_len", 9), 9
                )
            )
            lt_len = int(
                st.session_state.get(
                    "lt_atr_len_1", st.session_state.get("lt_atr_len", 50)
                )
            )
            rows = fetch_hlc(st_len, lt_len, st_symbol) 
            if not rows:
                st_value, lt_value = 1.0 , 1.0
            else:
                st_value, lt_value = compute_atr(rows, st_len, lt_len, include_latest=True)                     #|Compute ATR by marketdata db entries
            st.metric(                                                                                      
                f"ATR",                                                                                         #|ATR-Values displayed 
                f"{st_value:.4f}" if st_value is not None else "n/a",
            )
            st.metric(
                "ATR Avg",
                f"{lt_value:.4f}" if lt_value is not None else "n/a",
            )
    with right:
        mae_w = st.number_input("MAE Winners", step=0.1)
        mae_l = st.number_input("MAE Losers", step=0.1)
    st.divider()
    """____________________________________________________________________________________________________"""
    """
    Market Correlation and Beta showcases
    """
    st.subheader("Market Correlations and Beta")
    corr_left, corr_mid, corr_right = st.columns(3)
    with corr_left:
        st.caption("Additional Markets")
        add1 = market_to_symbol(st.selectbox(f"Market B", options = markets))                                                 #|Market inputs
        add2 = market_to_symbol(st.selectbox(f"Market C", options = markets))
        add3 = market_to_symbol(st.selectbox(f"Market D", options = markets))
    with corr_mid:
        st.caption("Correlation")
        current_symbol = market_to_symbol(st_market)                                                        #|Symbol Conversion
        cr_closes = fetch_closes(st_market, CORR_BAR_SIZE, ATR_BAR_SIZE)                                    #|close series for current market 
        current_rets = returns_series(CORR_LOOKBACK, cr_closes, CORR_BAR_SIZE)                              #|Convert to return series for comparison 
        for label, mkt in [("B", add1), ("C", add2), ("D", add3)]:                                          #|loop with markets selected in addX selectboxes above  
            if mkt == "None":
                continue
            other_symbol = mkt                                                                              #|Symbol Conversion
            os_closes = fetch_closes(other_symbol, CORR_BAR_SIZE, ATR_BAR_SIZE)
            other_rets = returns_series(CORR_LOOKBACK, os_closes, CORR_BAR_SIZE)                            #|return series of i symbol
            x, y = align_returns(current_rets, other_rets, CORR_LOOKBACK)                                   #|market data allgning (See fetch_close_series())
            corr_val = correlation(x, y, min(len(x), len(y))) if x and y else None
            st.metric(f"Corr {label}", f"{corr_val:.3f}" if corr_val is not None else "n/a")
    with corr_right:
        st.caption("Beta")                                                                                  #|Same logic as above("") just for Beta 
        for label, mkt in [("B", add1), ("C", add2), ("D", add3)]:
            if mkt == "None":
                continue
            other_symbol = mkt
            os_closes = fetch_closes(other_symbol, CORR_BAR_SIZE, ATR_BAR_SIZE)
            other_rets = returns_series(CORR_LOOKBACK, os_closes, CORR_BAR_SIZE)
            x, y = align_returns(current_rets, other_rets, CORR_LOOKBACK)
            beta_val = beta(x, y, min(len(x), len(y))) if x and y else None
            st.metric(f"Beta {label}", f"{beta_val:.3f}" if beta_val is not None else "n/a")
    st.divider()
    """____________________________________________________________________________________________________"""
    gear = market_state.gear
    conviction = market_state.conviction
    gear_mult = float(GEAR_MULT.get(gear, 1.0))
    """____________________________________________________________________________________________________"""
    """
    All Risk Settings 
    """
    rows = fetch_hlc(st_len, lt_len, st_market)
    st_atr_val, lt_atr_val = compute_atr(rows, st_len, lt_len, include_latest=True)
    st_atr = st_atr_val or 0.01
    lt_atr = lt_atr_val or 0.01
    direction = direction_value
    atr_ratio = st_atr / lt_atr 
    point_value = float(POINT_VALUES.get(st_market, 0.0))
    tick_value = float(TICK_VALUES.get(st_market, 0.25))

    stop_loss = round_to_step(stop_loss_calc(mae_l, atr_ratio, st_atr), tick_value)
    take_profit = round_to_step(max(stop_loss * 2, mae_l * 2), tick_value)                                      #|Just a factor for a goal, since I trail I dont use tp
    breakeven = round_to_step((mae_l),tick_value)
    trailingstart = round_to_step(breakeven + (atr_ratio * mae_w), tick_value)

    real_risk = round_to_step(point_value * stop_loss * num_contracts, tick_value)
    real_payoff = round_to_step(point_value * take_profit * num_contracts, tick_value)
    real_risk_in_ticks = (stop_loss / tick_value) if tick_value else 0.0
    real_payoff_in_ticks = (take_profit / tick_value) if tick_value else 0.0
    rr = (real_payoff / real_risk) if real_risk else 0.0
    equity = float(st.session_state["rm_equity"])
    trade_risk_pct = float(st.session_state["rm_trade_risk"])
    max_bp = float(st.session_state["rm_max_bp"])
    max_risk = round_to_step(gear_mult * equity * (trade_risk_pct / 100.0), tick_value)
    min_risk = round_to_step(conviction * max_risk, tick_value)
    """____________________________________________________________________________________________________"""
    """
    Display risk settings 
    """
    st.subheader("Calculation")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("MIN Risk", min_risk)
        st.metric("MAX Risk", max_risk)
    with c2:
        st.metric("Real Risk in Ticks", round_to_step(real_risk_in_ticks, 1))
        st.metric("Real Pay-Off in Ticks", round_to_step(real_payoff_in_ticks, 1))
    with c3:
        st.metric("Real Risk", round_to_step(real_risk, tick_value))
        st.metric("Real Pay-Off", round_to_step(real_payoff, tick_value))
    with c4:
        st.metric("RR", round(rr, 2))
        st.metric("Point Value", point_value)
    """____________________________________________________________________________________________________"""
    """
    Risk Alarms 
    """
    if real_risk > max_risk or real_risk < min_risk:
        st.warning("Adjust Risk!")
    if (entry * num_contracts * point_value) > (equity * max_bp):
        st.warning("Adjust Contract Size!")
    st.divider()
    """____________________________________________________________________________________________________"""
    """
    Tradingplan Parameters
    """
    st.subheader("Tradingplan")
    render_trading_plan(
        entry=entry,
        stop=tradingplan_value(-stop_loss, entry, tick_value, direction),
        breakeven=tradingplan_value(breakeven, entry, tick_value, direction),
        trailing=tradingplan_value(trailingstart, entry, tick_value, direction),
        Take_Profit=tradingplan_value(take_profit, entry, tick_value, direction)
    )
    """____________________________________________________________________________________________________"""
    """
    Trade ingestions into Current Trades db
    """
    trade_id = f"{st_market}_{int(time.time())}"
    st.divider()
    ensure_current_trades_schema()
    if st.button("Add Trade to Journal", use_container_width=True): 
        trade_payload = {                                                                                           #|Insertion Values 
            "trade_id": trade_id, 
            "created_at": str(datetime.now().strftime("%H:%M:%S %d-%m-%Y")),  
            "size": num_contracts,
            "strategy": strategy,
            "direction": direction,
            "market": st_market,

            "entry": entry,
            "stop": stop_loss,
            "profit": take_profit,
            "breakeven": breakeven,
            "trailing": trailingstart,

            "min_risk": min_risk,
            "max_risk": max_risk,
            "st_atr": st_atr,
            "lt_atr": lt_atr,
            "point_value": point_value,
        }
        trade_db_id = insert_trade_sql(trade_payload)                                                               #|Returns trade_db_id for tags table since id is autoincrement and trade_id is comptuted here
        insert_trade_tags(trade_db_id, market_state)                                                                #|trade_db_id : references trade.id in trades table
        insert_current_trade(trade_payload)
        st.success("Trade saved.")
    """____________________________________________________________________________________________________"""
    """
    Displays current trades and allows them to be closed below.
    """
    trades = load_current_trades()
    st.title("TradeTracer")
    st.divider()
    st.subheader("Open Trades")
    if trades.empty:
        st.info("No open trades.")
    else:
        display_cols = [                                                                                            #|Cols shown on the current_trades table in the UI
            "trade_id",
            "created_at",
            "size",
            "market",
            "entry",
            "stop",
            "breakeven",
            "trailing",
            "direction",
            "strategy",
        ]
        st.dataframe(trades[display_cols], use_container_width=True)
        
        st.divider()

        st.subheader("Close Trade")                                     
        trade_ids = trades["trade_id"].tolist()
        selected = st.selectbox("Trade ID", trade_ids)                                                              #|Displays id's of current trades 
        if st.button("Close Selected Trade"):
            market = trades.loc[trades["trade_id"] == selected, "market"].iloc[0]                                   #|fetches specific market of selected trade
            exit_price = latest_close_for_market(market)                                                            #|fetches close for that market of the selected trade
            if exit_price is None:
                st.error("No market data found for exit price.")
            else:
                exit_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
                update_journal_exit(selected, exit_price, exit_time)                                                #|Ingest exit values 
                delete_current_trade(selected)                                                                      #|Deletes trade by id 
                st.success(f"Closed {selected} at {exit_price:.2f}") 
                st.rerun()

    #st_autorefresh(interval=3_000, key="sync")                                                                      #|rerun every 3 seconds for syncing cockpit->risk page
    """____________________________________________________________________________________________________"""

if __name__ == "__main__":
    R02_main()