#A05_UI.py 
"""
This file renders the analysis Streamlit page. It loads journal data, applies user filters, 
and arranges the resulting metrics, charts, and tables.
this includes:
    Candle bar and linecharts
    Scatters
    and performance separation by tags
"""
"""________________________________________________________________________________________________""" 
import pandas as pd
import streamlit as st
from Pages.Calculation.Content.Analysis.A05_Calc import (prepare_analysis_df, 
                                                        filter_df,
                                                        compute_pnl_table,
                                                        performance_stats,
                                                        daily_summary,
                                                        )
from Pages.UI.Content.Analysis.A05_widgets import (metric_card,
                                                    render_daily_bar_chart,
                                                    render_equity_curve,
                                                    performance_overview,
                                                    wins_losses_duration_chart,
                                                    wins_losses_by_category,
                                                    scatter_pnl_vs,
                                                    scatter_time_vs,
                                                    profit_efficiency_section,
                                                    render_tag_filters,
                                                    ensure_filter_state
                                                    )
from Pages.DB.Content.Journal.J03_DB_Default import trades_with_tags_df
from Pages.Data.Content.Analysis.A05_Datatables import REQUIRED_COLS, WIN_THRESHOLD, LOSS_THRESHOLD
"""_______________________________________________________________________________________________"""
def A05_main():
    """
    Title, Layout
    """ 
    st.set_page_config("Analysis", layout="wide")
    st.title("Analysis")
    st.divider()
    """________________________________________________________________________________________________""" 
    """
    Stats calculation and dataframe structure checks for data analysis.
    """
    st.markdown("<div class='hero'>", unsafe_allow_html=True)
    df = trades_with_tags_df()                                                                                      #|Dataframe with tags and trades
    ensure_filter_state()                                                                                           #|Default state for Tags                                                                     
    render_tag_filters(df)
    st.markdown("</div>", unsafe_allow_html=True)                                                                   #|Design
    filtered_df = filter_df(df, st.session_state["tag_groups"])                                                     #|session state with tags
    pnl_df = compute_pnl_table(filtered_df, REQUIRED_COLS)                                                          #|Dataframe formed with required cols
    stats = performance_stats(pnl_df, WIN_THRESHOLD, LOSS_THRESHOLD)                                                  #|stats calculated by pnl table
    daily_df = daily_summary(pnl_df)                                                                                #|Dateconversion and cum Pnl
    analysis_df = prepare_analysis_df(pnl_df)                                                                       #|Dataframe with multiple entries and cols for analysis
    pnl_series = pd.to_numeric(pnl_df.get("PnL"), errors="coerce")                                                  #|PnL dataseries
    risk_series = (                                                                                                 #|Risk series (Calc right here)
        pd.to_numeric(pnl_df.get("stop"), errors="coerce")
        * pd.to_numeric(pnl_df.get("point_value"), errors="coerce")
        * pd.to_numeric(pnl_df.get("size"), errors="coerce")
    )
    win_mask = pnl_series >= WIN_THRESHOLD                                                                           #|Winners mask
    loss_mask = pnl_series <= LOSS_THRESHOLD                                                                         #|Losers mask
    wins = pnl_series[win_mask].dropna()                                                                            #|Safety
    losses = pnl_series[loss_mask].dropna()
    win_risks = risk_series[win_mask].dropna()                                                                      #|("...")
    hit_rate = (len(wins) / (len(wins) + len(losses))) if (len(wins) + len(losses)) > 0 else None                   #|hitrate calc under safety
    avg_win = wins.mean() if not wins.empty else None                                                       
    avg_loss = losses.mean() if not losses.empty else None
    if hit_rate is None or avg_win is None or avg_loss is None:                                                     #|ensuring computation
        ev_value = None
        rrr_value = None
    else:
        ev_value = (hit_rate * avg_win) - abs((1 - hit_rate) * avg_loss)
        if not win_risks.empty:
            rrr_value = (wins / win_risks).replace([pd.NA, pd.NaT, float("inf"), float("-inf")], pd.NA).dropna()    #|First calc, then errors replaced, then all dropped NA
            rrr_value = rrr_value.mean() if not rrr_value.empty else None
        else:
            rrr_value = None
    """________________________________________________________________________________________________""" 
    """
    Design elements: Metric cards
    """
    st.subheader("Performance")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Net PnL", f"{stats['net_pnl']:.2f}")
    with c2:
        wr_txt = f"{stats['win_rate']*100:.1f}%" if stats["win_rate"] is not None else "n/a"
        metric_card("Win Rate", wr_txt)
    with c3:
        pf_txt = f"{stats['profit_factor']:.2f}" if stats["profit_factor"] is not None else "n/a"
        metric_card("Profit Factor", pf_txt)
    with c4:
        ev_txt = f"{ev_value:.2f}" if ev_value is not None else "n/a"
        metric_card("EV", ev_txt)
    with c5:
        rrr_txt = f"{rrr_value:.2f}" if rrr_value is not None else "n/a"
        metric_card("RRR", rrr_txt)
    st.divider()
    """________________________________________________________________________________________________""" 
    """
    Equity-Curve and Candlestickcharts
    """
    left, right = st.columns([2, 1])
    with left:
        st.markdown("<div class='card'><h4>Daily Performance</h4>", unsafe_allow_html=True)
        tab_bar, tab_candle = st.tabs(["Bars", "Equity Curve"])
        with tab_bar:
            render_daily_bar_chart(daily_df)
        with tab_candle:
            render_equity_curve(daily_df)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        performance_overview(stats)
    st.divider()
    """________________________________________________________________________________________________""" 
    st.subheader("Trade Durations")
    wins_losses_duration_chart(analysis_df)
    st.subheader("Win/Loss Distribution")
    c_day, c_month = st.columns(2)
    with c_day:
        wins_losses_by_category(                                                                            #|Dataanalysis via Daytype
            analysis_df,
            "day_name",
            "Day of Week",
            [
                "Monday", 
            "Tuesday", 
            "Wednesday", 
            "Thursday", 
            "Friday", 
            "Saturday", 
            "Sunday"
            ],
        )
    with c_month:
        wins_losses_by_category(                                                                            #|Dataanalysis via Monthtype
            analysis_df,
            "month_name",
            "Month",
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
        )
    st.divider()
    """________________________________________________________________________________________________""" 
    """
    MFE, MAE Charts on Pnl
    """
    st.subheader("PnL vs Excursions")
    s1, s2 = st.columns(2)
    with s1:
        scatter_pnl_vs(analysis_df, "mfe", "MFE")
    with s2:
        scatter_pnl_vs(analysis_df, "mae", "MAE")
    st.divider()
    """________________________________________________________________________________________________"""
    """
    MFE,MAE Charts on Open/Close times
    """ 
    st.subheader("Excursions vs Open/Close Time")
    t1, t2 = st.columns(2)
    with t1:
        scatter_time_vs(analysis_df, "open_hour", "mfe", "MFE vs Open Time")
    with t2:
        scatter_time_vs(analysis_df, "open_hour", "mae", "MAE vs Open Time")
    t3, t4 = st.columns(2)
    with t3:
        scatter_time_vs(analysis_df, "close_hour", "mfe", "MFE vs Close Time")
    with t4:
        scatter_time_vs(analysis_df, "close_hour", "mae", "MAE vs Close Time")
    st.divider()
    """________________________________________________________________________________________________""" 
    st.subheader("Profit Efficiency")
    profit_efficiency_section(analysis_df)

if __name__ == "__main__":
    A05_main()
