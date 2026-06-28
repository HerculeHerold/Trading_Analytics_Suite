#C01_charts_rendering.py
"""
This module renders cockpit chart components. 
It builds gauge and bar visualizations for volatility, trend, risk, strength, and conviction scores.
"""
"""________________________________________________________________________________________________""" 
from streamlit_echarts import st_echarts                                                        
"""________________________________________________________________________________________________"""  
"""
Renders an ECharts gauge for the normalized volatility score. 
The gauge uses fixed bounds and color bands so volatility risk is readable at a glance.
"""
def render_vol_echart_gauge(title: str, score: float, min_val=0, max_val=1):                    #|We need a name, the score, and the bounds
    option = {
        "title": {
            "text": title,
            "left": "center",                                                                   #|Allignment to the left/right
            "top": "5%",                                                                        #|Allignment to the top/bottom
            "textStyle": {"color": "#FFFFFF", "fontSize": 16}                                 #|Color and fontsize editable      
        },                                                                                      #|Java packaging
        "series": [
            {   
                "type": "gauge",                                                                #|Type of Echart                                      
                "startAngle": 180,                                                              #|Degrees
                "endAngle": 0,
                "min": min_val,                                                                 #|Bounds
                "max": max_val,
                "center": ["50%", "65%"],                                                       #|Horizontal and vertical position of the Gauge
                "radius": "90%",                                                                #|Size relative to the available area
                "axisLine": {
                    "lineStyle": {                                                              #|Separated chart areas
                        "width": 15,
                        "color": [
                            (0.33,"#E74C3C"),
                            (0.66, "#D9D9D9"),
                            (1.00,"#2ECC71")
                        ],
                    }
                },
                "axisTick": {"show": False},                                                   #|No Tick values of axis
                "splitLine": {"show": False},                                                  #|major dividers horizontally on the ring
                "pointer": {                                                                   #|Needle attributes
                    "show": True,                           
                    "length": "65%",
                    "width": 3,
                    "itemStyle": {"color": "#FFFFFF"},
                },
                "anchor": {                                                                    #|Middlepoint by the needle
                    "show": False,
                    "size": 8,
                    "itemStyle": {"color": "#FFFFFF"}
                },
                "detail": {"show": False},                                                     
                "data": [{"value": score}],                                 
                "animation": False,                                                            
            }
        ],
        "backgroundColor": "#0E1117",
    }

    st_echarts(option, height="500px")
"""________________________________________________________________________________________________""" 
"""
Renders an ECharts gauge for directional trend score. 
The scale runs from bearish to bullish so the current trend bias is visible immediately.
"""
def render_trend_echart_gauge(title: str, score: float, min_val=-1, max_val=1):
    """Renders one clean institutional ECharts half-gauge."""
    
    option = {
        "title": {
            "text": title,
            "left": "center",
            "top": "5%",
            "textStyle": {"color": "#FFFFFF", "fontSize": 16}
        },
        "series": [
            {
                "type": "gauge",
                "startAngle": 180,
                "endAngle": 0,
                "min": min_val,
                "max": max_val,
                "center": ["50%", "65%"],
                "radius": "90%",
                "axisLine": {
                    "lineStyle": {
                        "width": 15,
                        "color": [
                            (0.33, "#E74C3C"),
                            (0.66, "#D9D9D9"),
                            (1.00, "#2ECC71"),
                        ],
                    }
                },
                "axisTick": {"show": False},
                "splitLine": {"show": False},
                "pointer": {
                    "show": True,
                    "length": "65%",
                    "width": 3,
                    "itemStyle": {"color": "#FFFFFF"},
                },
                "anchor": {
                    "show": False,
                    "size": 8,
                    "itemStyle": {"color": "#FFFFFF"}
                },
                "detail": {"show": False},
                "data": [{"value": score}],
                "animation": False,
            }
        ],
        "backgroundColor": "#0E1117",
    }

    st_echarts(option, height="500px")
"""________________________________________________________________________________________________""" 
"""
Renders an ECharts gauge for the final risk score. 
Color thresholds separate low, medium, and high risk environments for the cockpit.
"""
def render_risk_echart_gauge(title: str, score: float, min_val=0, max_val=1):    
    option = {
        "title": {
            "text": title,
            "left": "center",
            "top": "5%",
            "textStyle": {"color": "#FFFFFF", "fontSize": 16}
        },
        "series": [
            {
                "type": "gauge",
                "startAngle": 180,
                "endAngle": 0,
                "min": min_val,
                "max": max_val,
                "center": ["50%", "65%"],
                "radius": "90%",
                "axisLine": {
                    "lineStyle": {
                        "width": 15,
                        "color": [
                            (0.33, "#2ECC71"),
                            (0.66, "#D9D9D9"),
                            (1.00, "#E74C3C"),
                        ],
                    }
                },
                "axisTick": {"show": False},
                "splitLine": {"show": False},
                "pointer": {
                    "show": True,
                    "length": "65%",
                    "width": 3,
                    "itemStyle": {"color": "#FFFFFF"},
                },
                "anchor": {
                    "show": True,
                    "size": 8,
                    "itemStyle": {"color": "#FFFFFF"}
                },
                "detail": {"show": False},
                "data": [{"value": score}],
                "animation": False,
            }
        ],
        "backgroundColor": "#0E1117",
    }

    st_echarts(option, height="500px")
"""________________________________________________________________________________________________"""
"""
Chooses the display color for trend or volatility strength values. 
The color changes as values move from weak through neutral to strong.
"""
def strength_color(value: float) -> str:
    if value >= 2/3:
        return "#2ECC71"   # green
    elif value <= -2/3:
        return "#E74C3C"   # red
    else:
        return "#BDC3C7"   # grey
"""________________________________________________________________________________________________""" 
"""
Renders a horizontal strength bar with dynamic width and color. 
It turns the numeric strength value into a simple visual indicator for the cockpit.
"""
def render_strength_bar(title: str, value: float):
    option = {
        "title": {                                                                                
            "text": title,                                                                        #|title
            "left": "center",                                                                     #|Title alignment
            "textStyle": {"color": "#EAEAEA", "fontSize": 14}                                   #|Fontszie....
        },
        "xAxis": {                                                                                #|Alligning the xAxis
            "type": "value",                                                                      #|Allginment to the xAxis |---
            "min": -1,                                                                            #|Bounds
            "max": 1,
            "splitLine": {"show": False},                                               
            "axisLabel": {"color": "#888"},
        },
        "yAxis": {                                                                                #|Alligning the yAxis
            "type": "category",
            "data": [""],                                                                         #|Same Value because at value Y, X changes
            "axisLine": {"show": False},
            "axisTick": {"show": False},
        },
        "series": [{
            "type": "bar",                                                                        #|Initializing Type of Chart
            "data": [value],
            "barWidth": 18, 
            "itemStyle": {
                "color": strength_color(value),
                "borderRadius": 6
            }
        }],
        "tooltip": {
            "formatter": f"{value:.2f}"                                                           #|Formatting Value to 2 decimal steps
        }
    }

    st_echarts(option, height="120px")
"""________________________________________________________________________________________________"""  
"""
Chooses the display color for conviction values. 
Strong conviction receives a more positive color, while weak conviction is shown as a warning.
"""
def conviction_strength_color(value: float) -> str:
    if value >= 0.6:
        return "#2ECC71"   
    elif value <= 0.4:
        return "#E74C3C"  
    else:
        return "#BDC3C7"  
"""________________________________________________________________________________________________"""  
"""
Renders the conviction score as a horizontal bar chart. 
The visual makes agreement between market inputs easier to read than a raw number alone.
"""
def conviction_bar_chart(title: str, value: float):
    option = {
        "title": {
            "text": title,
            "left": "center",
            "textStyle": {"color": "#EAEAEA", "fontSize": 14}
        },
        "xAxis": {
            "type": "value",
            "min": 0,
            "max": 1,
            "splitLine": {"show": False},
            "axisLabel": {"color": "#888"},
        },
        "yAxis": {
            "type": "category",
            "data": [""],
            "axisLine": {"show": False},
            "axisTick": {"show": False},
        },
        "series": [{
            "type": "bar",
            "data": [value],
            "barWidth": 18,
            "itemStyle": {
                "color": conviction_strength_color(value),
                "borderRadius": 6
            }
        }],
        "tooltip": {
            "formatter": f"{value:.2f}"
        }
    }

    st_echarts(option, height="120px")


