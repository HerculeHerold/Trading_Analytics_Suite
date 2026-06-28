#RO2_Tradingplan.py
"""
Displays the calculated trading-plan levels in the risk-management page. 
Entry, stop, breakeven, trailing, and take-profit values are shown in one compact layout.
"""
"""____________________________________________________________________________________________________"""
from streamlit_echarts import st_echarts
"""____________________________________________________________________________________________________"""
def render_trading_plan(entry, stop, breakeven, trailing, Take_Profit):
    data = [
        {"value": [stop, 0], "name": "Stop Loss", "itemStyle": {"color": "#ff3b30"}},
        {"value": [breakeven, 0], "name": "Breakeven", "itemStyle": {"color": "#ffcc00"}},
        {"value": [entry, 0], "name": "Entry", "itemStyle": {"color": "#0a84ff"}},
        {"value": [trailing, 0], "name": "Trailing", "itemStyle": {"color": "#af02ff"}},
        {"value": [Take_Profit, 0], "name": "Take Profit", "itemStyle": {"color": "#20ff02"}}
    ]
    padding = 0.2
    x_vals = [point["value"][0] for point in data]                                                         #|[0]=x-axis; point=specific item
    padding_num = (max(x_vals) - min(x_vals)) * padding
    option = {
        "xAxis": {
            "type": "value",                                                                               #|Passing multiple values
            "min": min(x_vals) - padding_num,
            "max": max(x_vals) + padding_num,
            "axisLine": {"show": True},
            "axisTick": {"show": False},
            "splitLine": {"show": False},
        },
        "yAxis": {
            "type": "category",
            "data": [" "],
            "axisLine": {"show": False},
            "axisTick": {"show": False},
        },
        "series": [
            {
                "type": "scatter",
                "symbolSize": 150,
                "data": data,
                "label": {
                    "show": True,
                    "formatter": "{b}\n{@[0]}",                                                             #|{b}=item Name;\n=linebreak;{@[0]}=current data item value at index                                
                    "color": "white",
                    "fontSize": 25,        
                    "fontWeight": "bold"
                },
            }
        ],
    }

    st_echarts(option, height=400)



