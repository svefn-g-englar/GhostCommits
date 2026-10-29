"""Plotly visualizations for repository activity and contributor concentration."""

from __future__ import annotations

from typing import Any, Dict, List

import plotly.graph_objects as go


COLORS = {"green": "#C82F4A", "grid": "#3D272A", "text": "#AA998D", "panel": "#12090B"}


def activity_timeline(timeline: List[Dict[str, Any]]) -> go.Figure:
    months = [item["month"] for item in timeline]
    commits = [item["commits"] for item in timeline]
    fig = go.Figure(
        go.Scatter(
            x=months,
            y=commits,
            mode="lines+markers",
            fill="tozeroy",
            line={"color": COLORS["green"], "width": 2},
            marker={"color": COLORS["panel"], "line": {"color": COLORS["green"], "width": 2}, "size": 7},
            fillcolor="rgba(200,47,74,.10)",
            hovertemplate="%{x}<br>%{y} commits<extra></extra>",
        )
    )
    fig.update_layout(
        height=300,
        margin={"l": 10, "r": 10, "t": 15, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COLORS["text"], "family": "DM Mono"},
        xaxis={"gridcolor": COLORS["grid"], "showline": False, "title": None},
        yaxis={"gridcolor": COLORS["grid"], "showline": False, "title": "commits"},
        hoverlabel={"bgcolor": COLORS["panel"], "font_color": "#EEE5D7"},
        showlegend=False,
    )
    return fig


def signal_profile(packet: Dict[str, Any]) -> go.Figure:
    stats = packet["statistics"]
    inactivity = min(100, (stats.get("days_inactive") or 0) / 18)
    issue_pressure = min(100, stats.get("open_items", 0) / 5)
    community = min(100, stats.get("stars", 0) / 100)
    evidence = min(100, len(packet.get("evidence", [])) * 8)
    fig = go.Figure(go.Scatterpolar(
        r=[inactivity, issue_pressure, community, evidence, inactivity],
        theta=["Dormancy", "Open work", "Community", "Evidence", "Dormancy"],
        fill="toself",
        line={"color": COLORS["green"], "width": 2},
        fillcolor="rgba(200,47,74,.16)",
        marker={"color": "#EEE5D7", "size": 4},
        hovertemplate="%{theta}: %{r:.0f}/100<extra></extra>",
    ))
    fig.update_layout(
        height=330,
        margin={"l": 30, "r": 30, "t": 20, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": COLORS["text"], "family": "DM Mono", "size": 10},
        polar={"bgcolor": "rgba(0,0,0,0)", "radialaxis": {"visible": False, "range": [0, 100]}, "angularaxis": {"gridcolor": COLORS["grid"], "linecolor": COLORS["grid"]}},
        showlegend=False,
    )
    return fig
