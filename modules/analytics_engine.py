import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
import config

PLOTLY_THEME = "plotly_dark"
COLOR_MAP = {
    "available": config.COLORS["status_available"],
    "occupied": config.COLORS["status_occupied"],
    "reserved": config.COLORS["status_reserved"],
    "unavailable": config.COLORS["text_secondary"]
}

def create_occupancy_pie_chart(slots: List[Dict[str, Any]]) -> go.Figure:
    """Generates Donut chart of slot status breakdown."""
    if not slots:
        fig = go.Figure()
        fig.add_annotation(text="No Slot Data Available", showarrow=False, font=dict(size=16, color="white"))
        fig.update_layout(template=PLOTLY_THEME)
        return fig
        
    df = pd.DataFrame(slots)
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    
    colors = [COLOR_MAP.get(s, "#94A3B8") for s in status_counts["status"]]
    
    fig = px.pie(
        status_counts,
        values="count",
        names="status",
        hole=0.55,
        color="status",
        color_discrete_map=COLOR_MAP,
        title="Parking Space Status Breakdown"
    )
    fig.update_traces(textinfo="percent+label", hovertemplate="%{label}: %{value} slots (%{percent})")
    fig.update_layout(
        template=PLOTLY_THEME,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

def create_zone_occupancy_bar_chart(slots: List[Dict[str, Any]]) -> go.Figure:
    """Generates stacked bar chart of occupancy by zone."""
    if not slots:
        fig = go.Figure()
        fig.update_layout(template=PLOTLY_THEME)
        return fig
        
    df = pd.DataFrame(slots)
    zone_df = df.groupby(["zone", "status"]).size().unstack(fill_value=0).reset_index()
    
    for col in ["available", "occupied", "reserved", "unavailable"]:
        if col not in zone_df.columns:
            zone_df[col] = 0
            
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Available", x=zone_df["zone"], y=zone_df["available"], marker_color=config.COLORS["status_available"]))
    fig.add_trace(go.Bar(name="Occupied", x=zone_df["zone"], y=zone_df["occupied"], marker_color=config.COLORS["status_occupied"]))
    fig.add_trace(go.Bar(name="Reserved", x=zone_df["zone"], y=zone_df["reserved"], marker_color=config.COLORS["status_reserved"]))
    fig.add_trace(go.Bar(name="Unavailable", x=zone_df["zone"], y=zone_df["unavailable"], marker_color="#64748B"))
    
    fig.update_layout(
        barmode="stack",
        title="Occupancy Distribution by Zone",
        template=PLOTLY_THEME,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Zone",
        yaxis_title="Number of Slots",
        margin=dict(t=40, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    return fig

def create_occupancy_timeline_chart(snapshots: List[Dict[str, Any]]) -> go.Figure:
    """Generates occupancy percentage timeline graph."""
    if not snapshots:
        fig = go.Figure()
        fig.add_annotation(text="No Historical Analytics Recorded Yet", showarrow=False, font=dict(size=16, color="#94A3B8"))
        fig.update_layout(template=PLOTLY_THEME, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
        
    df = pd.DataFrame(snapshots)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["occupancy_pct"],
        mode="lines+markers",
        name="Occupancy %",
        line=dict(color=config.COLORS["accent_blue"], width=3),
        fill="tozeroy",
        fillcolor="rgba(0, 180, 216, 0.15)"
    ))
    
    fig.update_layout(
        title="Occupancy Rate Trend Over Time (%)",
        template=PLOTLY_THEME,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Timestamp",
        yaxis_title="Occupancy (%)",
        yaxis=dict(range=[0, 100]),
        margin=dict(t=40, b=20, l=20, r=20)
    )
    return fig

def create_revenue_timeline_chart(snapshots: List[Dict[str, Any]]) -> go.Figure:
    """Generates revenue growth trend line."""
    if not snapshots:
        fig = go.Figure()
        fig.add_annotation(text="No Revenue Data Recorded Yet", showarrow=False, font=dict(size=16, color="#94A3B8"))
        fig.update_layout(template=PLOTLY_THEME, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
        
    df = pd.DataFrame(snapshots)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["revenue"],
        mode="lines+markers",
        name="Cumulative Revenue (₹)",
        line=dict(color="#00E676", width=3)
    ))
    
    fig.update_layout(
        title="Cumulative Simulated Revenue Trend (₹)",
        template=PLOTLY_THEME,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Timestamp",
        yaxis_title="Revenue (₹)",
        margin=dict(t=40, b=20, l=20, r=20)
    )
    return fig

def create_reservation_status_chart(reservations: List[Dict[str, Any]]) -> go.Figure:
    """Generates breakdown chart for reservation statuses."""
    if not reservations:
        fig = go.Figure()
        fig.add_annotation(text="No Reservation Records", showarrow=False, font=dict(size=16, color="#94A3B8"))
        fig.update_layout(template=PLOTLY_THEME, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
        
    df = pd.DataFrame(reservations)
    counts = df["status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    
    status_colors = {
        "active": "#00B4D8",
        "completed": "#00E676",
        "cancelled": "#FF5252",
        "expired": "#FF9100"
    }
    
    fig = px.bar(
        counts,
        x="status",
        y="count",
        color="status",
        color_discrete_map=status_colors,
        title="Reservation Status Breakdown",
        text_auto=True
    )
    fig.update_layout(
        template=PLOTLY_THEME,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Status",
        yaxis_title="Count",
        margin=dict(t=40, b=20, l=20, r=20),
        showlegend=False
    )
    return fig
