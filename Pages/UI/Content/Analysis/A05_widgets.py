#A05_widgets.py
"""
This module renders reusable analysis widgets. 
It builds performance cards, charts, filter controls, and daily candle data for the analysis page.
"""
"""________________________________________________________________________________________________""" 
import streamlit as st 
import altair as alt 
import pandas as pd 
from typing import Any
from Pages.Data.Content.Analysis.A05_Datatables import TAG_OPTIONS, WIN_THRESHOLD, LOSS_THRESHOLD
from Pages.Calculation.Content.Analysis.A05_Calc import blank_condition, available_fields, fill_and_drop
"""________________________________________________________________________________________________"""
"""
Renders the headline performance metrics from the statistics dictionary. 
It formats values, applies positive or negative coloring, and displays them as compact Streamlit HTML blocks.
"""
def performance_overview(stats: dict[str, Any]):
    rows = [                                                                                                        #|Statistics calculated by performance_stats() see A05_Calc
        ("Net PnL", stats["net_pnl"], True),
        ("Revenue", stats["revenue"], True),
        ("Loss", stats["loss_sum"], False),
        ("Win Rate", f"{stats['win_rate']*100:.1f}%" if stats["win_rate"] is not None else "n/a", True),
        ("Profit Factor", f"{stats['profit_factor']:.2f}" if stats["profit_factor"] is not None else "n/a", True),
        ("Trades", stats["wins"] + stats["losses"] + stats["breakevens"], None),
        ("Wins / Losses / BE", f"{stats['wins']} / {stats['losses']} / {stats['breakevens']}", None),
    ]
    st.markdown("<div class='card'><h4>Performance Overview</h4>", unsafe_allow_html=True)
    for label, val, positive in rows:                                                                               #|For every stat
        color_class = "metric-green" if positive else "metric-red" if positive is False else ""                     #|Metric colouring dependent on performance
        if isinstance(val, (int, float)) and not isinstance(val, bool):                                             #|Ensuring metric datatype
            txt = f"{val:.2f}"
        else:
            txt = str(val)
        st.markdown(
            f"<div class='metric-label'>{label}</div>"                                                              #|Display stat-name
            f"<div class='metric-value {color_class}'>{txt}</div>",                                                 #|Colouring value based on performance
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)                                                               
"""________________________________________________________________________________________________"""
"""
Renders daily PnL as an Altair bar chart. 
Dates are cleaned first and bars are colored by win, loss, or neutral thresholds.
"""
def render_daily_bar_chart(daily_df: pd.DataFrame):
    if daily_df.empty:
        st.info("No PnL data yet.")
        return                                                                                          #|Return nothing if table empty
    chart_data = daily_df.copy()
    chart_data["date"] = pd.to_datetime(chart_data["date"], errors="coerce")                            #|Dateconversion
    chart_data = chart_data.dropna(subset=["date"])                                                     #|Drop Na rows
    if chart_data.empty:
        st.info("No PnL data yet.")                                                                     #|Second safety if values only contained na's
        return
    bars = (                                                                                            #|Chart configuration
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("date:T", title="Date"),                                                            #|T=Temporal type
            y=alt.Y("pnl:Q", title="PnL"),                                                              #|Q=Quantitative datatype
            color = (
                alt.when(alt.datum.pnl >= WIN_THRESHOLD)
                .then(alt.value("#2ecc71"))
                .when(alt.datum.pnl <= LOSS_THRESHOLD)
                .then(alt.value("#e74c3c"))
                .otherwise(alt.value("#b8b8b8"))
                ),
            tooltip=["date:T", "pnl:Q", "trade_count:Q"]                                                #|This appears when you hover over bar
        )
    )   
    st.altair_chart(bars, use_container_width=True)
"""________________________________________________________________________________________________"""
"""
Renders the cumulative equity curve from daily PnL values. 
The function sorts days chronologically and plots the running total as a line chart.
"""
def render_equity_curve(daily_df: pd.DataFrame): 
    if daily_df.empty:
        st.info("No PnL data yet.")
        return                                                                                          #|Safety return nothing if df empty
    chart_data = daily_df.copy()
    chart_data["date"] = pd.to_datetime(chart_data["date"], errors="coerce")                            #|Date conversion
    chart_data = chart_data.dropna(subset=["date"])
    if chart_data.empty:
        st.info("No PnL data yet.")
        return                                                                                          #|Second safety check if table only contained na's
    chart_data = chart_data.sort_values("date")                                                         #|Sort by date
    chart_data["equity"] = chart_data["pnl"].cumsum()
    line = (                                                                                            #|Chart configuration
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("equity:Q", title="Equity Curve"),
            tooltip=["date:T", "equity:Q", "pnl:Q"],
        )
    )
    st.altair_chart(line, use_container_width=True)
"""________________________________________________________________________________________________"""
"""
HTML based design for Analysis page 
"""
Page_design = st.markdown(
    """
    <style>
    .card {background:#161c27; padding:14px 16px; border-radius:10px; border:1px solid #2a3444;}
    .card h4 {margin:0 0 8px 0; color:#f2f2f2;}
    .metric-label {color:#c6cdd9; font-size:13px;}
    .metric-value {color:#b7f7f7; font-weight:700; font-size:18px;}
    .metric-green {color:#47d47b;}
    .metric-red {color:#ff6b6b;}
    </style>
    """,
    unsafe_allow_html=True,
)
"""________________________________________________________________________________________________"""
"""
Renders one reusable metric card for the analysis dashboard. 
It wraps a label and value in the shared HTML styling used by the page.
"""
def metric_card(label: str, value: str):
    st.markdown(
        f"<div class='card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>",
        unsafe_allow_html=True,
    )
"""________________________________________________________________________________________________"""
"""
Builds the profit-efficiency view for realized and potential trade outcomes. 
It prepares the needed columns, renders summary cards, and compares captured PnL with available opportunity.
"""
def profit_efficiency_section(df: pd.DataFrame): 
    data = df.copy()
    data["trade_label"] = data["trade_id"]
    data = fill_and_drop(data, "trade_label", "trade_db_id", extra = ("PnL",))
    if data is None: 
        return
    data = data[data["PnL"] >= WIN_THRESHOLD]                                                            #|Mask for profit efficiency (winning trade only when WIN_THRESHOLD surpassed)
    data["PnL_plus_Potential"] = data["PnL"] + data["Potential_Value"].fillna(0)                        #|Compute MAX PnL
    bars = data[["trade_label", "PnL", "PnL_plus_Potential", "risk"]].copy()                            #|Bars consist of Tradelabel with normal PnL and max PnL
    bars = bars.melt(                                                                                   #|Formatting wide df into long
        id_vars=["trade_label"],
        value_vars=["PnL", "PnL_plus_Potential", "risk"],                                               
        var_name="metric",
        value_name="value",
    )
    chart = (
        alt.Chart(bars)
        .mark_bar()
        .encode(
            x=alt.X("trade_label:N", title="Trade ID"),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color(
                "metric:N",
                scale=alt.Scale(
                    domain=["PnL", "PnL_plus_Potential", "risk"],
                    range=["#2ecc71", "#e5ff00", "#ff0000"],
                ),
            ),
            tooltip=["trade_label:N", "metric:N", "value:Q"],
        )
    )
    st.altair_chart(chart, use_container_width=True)                                                    #|Return chart

    efficiency = data["PnL"] / data["PnL_plus_Potential"]                                               #|Overall Efficiency for each row
    efficiency = efficiency.replace([pd.NA, pd.NaT, float("inf"), float("-inf")], pd.NA).dropna()
    if not efficiency.empty:
        st.metric("Profit Efficiency", f"{efficiency.mean() * 100:.1f}%")                               #|Mean + Display
    else:
        st.metric("Profit Efficiency", "n/a")
"""________________________________________________________________________________________________"""
"""
Shows how trade duration differs between wins and losses. 
The chart helps identify whether profitable and losing trades behave differently over time.
"""
def wins_losses_duration_chart(df: pd.DataFrame):
    data = fill_and_drop(df, "duration_minutes", extra=("result",))
    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "duration_minutes:Q",
                bin=alt.Bin(maxbins=20),                                                                #|Dataranges displayed in intervals of X (in this case 20)
                title="Duration (minutes)",
            ),
            y=alt.Y("count():Q", title="Trades"),
            color=alt.Color("result:N", scale=alt.Scale(domain=["Win", "Loss"], range=["#2ecc71", "#e74c3c"])),
            tooltip=[
                alt.Tooltip("count():Q", title="Trades"),
                alt.Tooltip("result:N", title="Result"),
                alt.Tooltip("duration_hms:N", title="Duration"),
            ],
        )
    )
    st.altair_chart(chart, use_container_width=True)
"""________________________________________________________________________________________________"""
"""
Groups trades by a selected category and counts wins versus losses. 
The ordered bar view makes it easier to compare markets, strategies, or states.
"""
def wins_losses_by_category(df: pd.DataFrame, field: str, title: str, order: list[str]):
    data = fill_and_drop(df, field, extra=("result",))                                                  #|Drop field if na                                                                                        #|If no data skip iteration
    chart = (
        alt.Chart(data)                                                                                 #|Chart_Config
        .mark_bar()
        .encode(
            x=alt.X(f"{field}:N", sort=order, title=title),
            y=alt.Y("count():Q", title="Trades"),
            color=alt.Color("result:N", scale=alt.Scale(domain=["Win", "Loss"], range=["#2ecc71", "#e74c3c"])),
            tooltip=[f"{field}:N", "count():Q", "result:N"],
        )
    )
    st.altair_chart(chart, use_container_width=True)
"""________________________________________________________________________________________________"""
"""
Plots trade PnL against a selected numeric field. 
This helps inspect whether variables such as MAE, MFE, or risk size relate to final outcome.
"""
def scatter_pnl_vs(df: pd.DataFrame, field: str, title: str):
    data = fill_and_drop(df, "PnL" , extra = (field, "result"))
    chart = (
        alt.Chart(data)
        .mark_circle(size=70, opacity=0.8)
        .encode(
            x=alt.X("PnL:Q", title="PnL"),
            y=alt.Y(f"{field}:Q", title=title),
            color=alt.Color("result:N", scale=alt.Scale(domain=["Win", "Loss"], range=["#2ecc71", "#e74c3c"])),
            tooltip=["trade_id:N", "PnL:Q", alt.Tooltip(f"{field}:Q", title=title), "result:N"],
        )
    )
    st.altair_chart(chart, use_container_width=True)
"""________________________________________________________________________________________________"""
"""
Plots a selected value against a time-based field. 
It is used to check whether opening or closing time patterns affect trade behavior.
"""
def scatter_time_vs(df: pd.DataFrame, time_field: str, value_field: str, title: str):
    data =  fill_and_drop(df, time_field, extra = (value_field, "result"))
    chart = (
        alt.Chart(data)
        .mark_circle(size=70, opacity=0.8)
        .encode(
            x=alt.X(f"{time_field}:Q", title="Time (hours)"),
            y=alt.Y(f"{value_field}:Q", title=title),
            color=alt.Color("result:N", scale=alt.Scale(domain=["Win", "Loss"], range=["#2ecc71", "#e74c3c"])),
            tooltip=[
                "trade_id:N",
                alt.Tooltip(f"{time_field}:Q", title="Time (h)"),
                alt.Tooltip(f"{value_field}:Q", title=title),
                "result:N",
            ],
        )
    )
    st.altair_chart(chart, use_container_width=True) 
"""________________________________________________________________________________________________"""
"""
Creates the default analysis filter group in Streamlit session state. 
This prevents the filter UI from failing before the user adds conditions.
"""
def ensure_filter_state():
    st.session_state.setdefault("tag_groups", [{"conditions": [blank_condition()]}])
"""________________________________________________________________________________________________"""
"""
Renders the interactive filter builder for analysis tags and trade fields. 
It lets the user add groups, combine conditions, and pass the resulting structure into dataframe filtering.
"""
def render_tag_filters(df):
    ensure_filter_state()
    ops_str = ["==", "!=", "contains", "not contains"]                                                                  #|Default operations
    ops_num = ["==", "!=", ">", "<", ">=", "<="]                                                                        #|Default operations

    st.subheader("Filters")
    st.divider()
    for gi, group in enumerate(st.session_state["tag_groups"]):
        st.markdown(f"**Tag group {gi+1}**")
        for ci, cond in enumerate(group["conditions"]):                                                                 #|For every group
            cols = st.columns([3, 2, 3, 1])                                                                             #|Field, Op, Value, delete
            with cols[0]:                           
                cond["field"] = st.selectbox(
                    "Field",
                    options=available_fields(df),                                                                       #|Tags loaded
                    index=available_fields(df).index(cond["field"]) if cond["field"] in available_fields(df) else 0,    #|Protection from prior selectbox entry without it being in available_fields(df)
                    key=f"field_{gi}_{ci}",                                                                             #|Each selectbox with its key                                                                                             
                )
            series = df[cond["field"]] if cond["field"] else pd.Series(dtype=object)
            ops = ops_str if series.dtype == "O" else ops_num                                                           #|Check series are str (Usecase of operations based on tags see above)
            with cols[1]:
                cond["op"] = st.selectbox("Op", options=ops, key=f"op_{gi}_{ci}")                                       #|Selectbox with own keys
            with cols[2]:                                                                                               
                if cond["field"] in TAG_OPTIONS:                                                                        #|If Tag exists
                    cond["value"] = st.selectbox(
                        "Value",
                        options=TAG_OPTIONS[cond["field"]],                                                             #|specific states for that field
                        index=TAG_OPTIONS[cond["field"]].index(cond["value"]) if cond["value"] in TAG_OPTIONS[cond["field"]] else 0, #("..." see above same logic at index)
                        key=f"val_{gi}_{ci}",
                    )
                else:
                    cond["value"] = st.text_input("Value", cond["value"], key=f"val_{gi}_{ci}")                         #|If no states manual text input
            with cols[3]:
                if st.button("Delete", key=f"del_{gi}_{ci}"):                                                           #|Id with condition id and group id
                    group["conditions"].pop(ci)                                                                         #|Deletes condition by id (Not group)
                    st.rerun()
        if st.button("AND", key=f"add_cond_{gi}"):                                                                      #|AND with id
            group["conditions"].append(blank_condition())                                                               #|Default condition, new condition in group
            st.rerun()
    if st.button("OR"):                                                                                                 #|OR doesnt need own id
        st.session_state["tag_groups"].append({"conditions": [blank_condition()]})                                      #|New default group            
        st.rerun()
    if st.button("Reset filters"):                                                                                      
        st.session_state["tag_groups"] = [{"conditions": [blank_condition()]}]                                          #|completely reseting groups and conditions
        st.rerun()
"""________________________________________________________________________________________________"""
"""
Converts intraday trade results into daily candle-style values. 
It aggregates each day into open, high, low, and close values based on cumulative PnL movement.
"""
def daily_candles(df: pd.DataFrame) -> list[Any]:
    #Safety Check, looking if data is actually in df for further computation
    if "PnL" not in df.columns:
        return []
    if "exit_time" not in df.columns and "created_at" not in df.columns:
        return []
    work = df[["PnL"]].copy()
    if "exit_time" in df.columns:
        work["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
    else:
        work["exit_time"] = pd.NaT
    if "created_at" in df.columns:
        work["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    else:
        work["created_at"] = pd.NaT
    #------------------------------------------------------   
    work["day"] = work["exit_time"].dt.date                                                                         #|Dateconversion, taking date from exit_time
    work.loc[work["day"].isna(), "day"] = work.loc[work["day"].isna(), "created_at"].dt.date                        #|If rows in work[day] are still na take the date from "created_at"
    work = work.dropna(subset=["PnL", "day"])                                                                       #|Second safety if created_at still included nas
    if work.empty:
        return []                                                                                                   #|safety return
    grouped = work.groupby("day")["PnL"].sum().reset_index().sort_values("day")                                     #|summing pnl per group day(index) before sorting values by day and resetting index
    data = []
    prev_close = 0.0
    for _, row in grouped.iterrows():
        date_str = row["day"].isoformat()                                                                           #|Date conversion into isoformat
        day_sum = float(row["PnL"])                                                                                 #|PnL of that day
        o = prev_close                                                                                              #|First default                                                              
        c = o + day_sum                                                                                             #|PnL + default
        h = max(o, c)                                                                                               #|MAX of all opens or closes inside that day
        l = min(o, c)                                                                                               #|MIN of all opens or closes inside that day
        prev_close = c                                                                                              #|Then last close
        if day_sum > 100:                                                                                           #|Design
            col = "#2ecc71"
        elif day_sum < -100:
            col = "#e74c3c"
        else:
            col = "#95a5a6"
        data.append(
            {
                "name": date_str,
                "value": [o, c, l, h],
                "itemStyle": {"color": col, "color0": col, "borderColor": col, "borderColor0": col},
            }                                                                                                       #|Adding to data
        )
    return data
