"""Plotly visualisations: propagation graph, geo map, process bar chart."""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx

SEVERITY_COLORS = {
    "Low": "#4caf50",
    "Moderate": "#8bc34a",
    "Significant": "#ffc107",
    "High": "#ff7043",
    "Critical": "#d32f2f",
}


def _impact_color(score: float) -> str:
    if score <= 20:
        return SEVERITY_COLORS["Low"]
    if score <= 40:
        return SEVERITY_COLORS["Moderate"]
    if score <= 60:
        return SEVERITY_COLORS["Significant"]
    if score <= 80:
        return SEVERITY_COLORS["High"]
    return SEVERITY_COLORS["Critical"]


def plot_process_bar(process_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of process impact scores."""
    if process_df.empty:
        return go.Figure()

    df = process_df.sort_values("impact_score", ascending=True).tail(15)
    colors = [_impact_color(s) for s in df["impact_score"]]

    fig = go.Figure(go.Bar(
        x=df["impact_score"],
        y=df["process"],
        orientation="h",
        marker_color=colors,
        text=df["severity"],
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Impact: %{x:.1f}/100<br>"
            "Assets: %{customdata[0]}<extra></extra>"
        ),
        customdata=df[["asset_count"]].values,
    ))
    fig.update_layout(
        title="Business Process Impact",
        xaxis=dict(title="Impact Score (0–100)", range=[0, 105]),
        yaxis=dict(title=""),
        height=max(300, len(df) * 40),
        margin=dict(l=10, r=60, t=40, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_propagation_graph(
    all_paths: dict,
    all_impacts: dict,
    asset_index: dict,
    max_nodes: int = 80,
) -> go.Figure:
    """Plotly network graph showing impact propagation paths."""
    if not all_paths:
        return go.Figure()

    # Build subgraph from paths
    G = nx.DiGraph()
    for asset_id, path in all_paths.items():
        for i in range(len(path) - 1):
            G.add_edge(path[i], path[i + 1])

    # Limit to top-N nodes by impact to keep the graph readable
    sorted_nodes = sorted(all_impacts.keys(), key=lambda x: all_impacts[x], reverse=True)
    top_nodes = set(sorted_nodes[:max_nodes])
    subgraph_nodes = [n for n in G.nodes() if n in top_nodes]
    G = G.subgraph(subgraph_nodes)

    if not G.nodes():
        return go.Figure()

    pos = nx.spring_layout(G, seed=42, k=2.0)

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=0.8, color="#cccccc"),
        hoverinfo="none",
    )

    node_x, node_y, node_text, node_color, node_size, node_hover = [], [], [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        impact_pct = all_impacts.get(node, 0.0) * 100
        info = asset_index.get(node, {})
        name = info.get("name", node)
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_color.append(impact_pct)
        node_size.append(max(8, min(24, impact_pct / 4)))
        node_hover.append(
            f"<b>{name}</b><br>"
            f"ID: {node}<br>"
            f"Impact: {impact_pct:.1f}/100<br>"
            f"Type: {info.get('type', '')}<br>"
            f"Criticality: {info.get('criticality', '')}"
        )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        textfont=dict(size=7),
        hovertext=node_hover,
        hoverinfo="text",
        marker=dict(
            size=node_size,
            color=node_color,
            colorscale=[
                [0.0, SEVERITY_COLORS["Low"]],
                [0.2, SEVERITY_COLORS["Moderate"]],
                [0.4, SEVERITY_COLORS["Significant"]],
                [0.7, SEVERITY_COLORS["High"]],
                [1.0, SEVERITY_COLORS["Critical"]],
            ],
            cmin=0, cmax=100,
            colorbar=dict(title="Impact", thickness=12),
            line=dict(width=1, color="white"),
        ),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=f"Propagation Graph ({len(G.nodes())} assets shown)",
        showlegend=False,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=10, r=10, t=40, b=10),
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_geo_map(geo_df: pd.DataFrame) -> go.Figure:
    """Scatter geo map of affected locations."""
    if geo_df.empty:
        return go.Figure()

    # City-level coordinates lookup (top maritime ports)
    CITY_COORDS: dict[str, tuple[float, float]] = {
        "New York": (40.71, -74.01),
        "Dubaï": (25.20, 55.27),
        "Dubai": (25.20, 55.27),
        "Singapour": (1.35, 103.82),
        "Singapore": (1.35, 103.82),
        "Yokohama": (35.44, 139.64),
        "Tokyo": (35.69, 139.69),
        "Santos": (-23.96, -46.33),
        "Marseille": (43.30, 5.37),
        "Hambourg": (53.55, 9.99),
        "Hamburg": (53.55, 9.99),
        "Rio de Janeiro": (-22.91, -43.17),
        "Brême": (53.07, 8.80),
        "Bremen": (53.07, 8.80),
        "Amsterdam": (52.37, 4.90),
        "Le Havre": (49.49, 0.11),
        "Dunkerque": (51.03, 2.38),
        "Ningbo": (29.87, 121.55),
        "Busan": (35.10, 129.04),
        "Nantes": (47.22, -1.55),
        "Rotterdam": (51.92, 4.48),
        "Anvers": (51.22, 4.40),
        "Antwerp": (51.22, 4.40),
        "Los Angeles": (34.05, -118.24),
        "Shanghai": (31.23, 121.47),
        "Hong Kong": (22.32, 114.17),
    }

    lats, lons, texts, colors, sizes = [], [], [], [], []
    for _, row in geo_df.iterrows():
        city = row["location"].split(",")[0].strip()
        if city in CITY_COORDS:
            lat, lon = CITY_COORDS[city]
        else:
            continue
        lats.append(lat)
        lons.append(lon)
        texts.append(
            f"<b>{row['location']}</b><br>"
            f"Max Impact: {row['max_impact']:.1f}/100<br>"
            f"Assets: {row['asset_count']}<br>"
            f"Severity: {row['severity']}"
        )
        colors.append(row["max_impact"])
        sizes.append(max(10, min(40, row["max_impact"] / 2.5)))

    if not lats:
        return go.Figure(go.Scattergeo()).update_layout(title="No mappable locations found")

    fig = go.Figure(go.Scattergeo(
        lat=lats, lon=lons,
        text=texts,
        hoverinfo="text",
        mode="markers",
        marker=dict(
            size=sizes,
            color=colors,
            colorscale=[
                [0.0, SEVERITY_COLORS["Low"]],
                [0.2, SEVERITY_COLORS["Moderate"]],
                [0.4, SEVERITY_COLORS["Significant"]],
                [0.7, SEVERITY_COLORS["High"]],
                [1.0, SEVERITY_COLORS["Critical"]],
            ],
            cmin=0, cmax=100,
            colorbar=dict(title="Impact", thickness=12),
            line=dict(width=1, color="white"),
        ),
    ))
    fig.update_layout(
        title="Geographic Impact",
        geo=dict(
            showland=True,
            landcolor="rgb(235,235,235)",
            showocean=True,
            oceancolor="rgb(210,230,245)",
            showcountries=True,
            countrycolor="white",
            showcoastlines=True,
            coastlinecolor="white",
            projection_type="natural earth",
        ),
        height=420,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def severity_badge_html(label: str) -> str:
    color = SEVERITY_COLORS.get(label, "#9e9e9e")
    return (
        f'<span style="background:{color};color:white;padding:2px 10px;'
        f'border-radius:12px;font-weight:bold;font-size:0.85em">{label}</span>'
    )
