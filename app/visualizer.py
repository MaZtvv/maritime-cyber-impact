"""Plotly visualisations — naval / defence operational aesthetic."""

import pandas as pd
import plotly.graph_objects as go
import networkx as nx

# ---------------------------------------------------------------------------
# Marine Nationale colour palette — navy / white / red institutional
# ---------------------------------------------------------------------------

SEVERITY_COLORS = {
    "Low":         "#0F8A5F",  # operational green
    "Moderate":    "#1D5F9F",  # institutional blue
    "Significant": "#A97913",  # restrained gold
    "High":        "#D65F00",  # operational orange
    "Critical":    "#C6002B",  # French red
}

# Retained for API compatibility; badges now use solid colours
SEVERITY_BG_COLORS = {
    "Low":         "rgba(5,150,105,0.1)",
    "Moderate":    "rgba(37,99,235,0.1)",
    "Significant": "rgba(180,83,9,0.1)",
    "High":        "rgba(220,104,3,0.12)",
    "Critical":    "rgba(198,0,43,0.12)",
}

_NAVY_BG   = "#F1F3F7"  # page background
_CARD_BG   = "#FFFFFF"  # chart / card surfaces
_BORDER    = "#D8DEE8"  # borders
_TEXT_PRI  = "#111827"  # primary text
_TEXT_SEC  = "#667085"  # secondary text
_GRID      = "rgba(0,38,84,0.10)"  # chart grid lines
_STEEL     = "#002654"  # navy accent


def _score_to_label(score: float) -> str:
    if score <= 20:   return "Low"
    if score <= 40:   return "Moderate"
    if score <= 60:   return "Significant"
    if score <= 80:   return "High"
    return "Critical"


def _impact_color(score: float) -> str:
    return SEVERITY_COLORS[_score_to_label(score)]


# ---------------------------------------------------------------------------
# Process bar chart
# ---------------------------------------------------------------------------

def plot_process_bar(process_df: pd.DataFrame) -> go.Figure:
    if process_df.empty:
        return _empty_figure("Aucune donnée de processus")

    df = process_df.sort_values("impact_score", ascending=True).tail(15)
    colors = [_impact_color(s) for s in df["impact_score"]]

    fig = go.Figure(go.Bar(
        x=df["impact_score"],
        y=df["process"],
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(width=0),
        ),
        text=df["impact_score"].apply(lambda x: f"{x:.0f}"),
        textposition="outside",
        textfont=dict(size=10, color=_TEXT_SEC, family="IBM Plex Mono, monospace"),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Score : %{x:.1f}/100<br>"
            "Actifs : %{customdata[0]}<extra></extra>"
        ),
        customdata=df[["asset_count"]].values,
    ))
    fig.update_layout(
        **_base_layout(height=max(280, len(df) * 36)),
        xaxis=dict(
            title="",
            range=[0, 112],
            tickfont=dict(size=9, color=_TEXT_SEC, family="IBM Plex Mono, monospace"),
            gridcolor=_GRID,
            zeroline=False,
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=9, color=_TEXT_PRI),
        ),
        margin=dict(l=4, r=50, t=8, b=8),
    )
    return fig


# ---------------------------------------------------------------------------
# Propagation network graph
# ---------------------------------------------------------------------------

def plot_propagation_graph(
    all_paths: dict,
    all_impacts: dict,
    asset_index: dict,
    max_nodes: int = 80,
) -> go.Figure:
    if not all_paths:
        return _empty_figure("Aucun chemin de propagation")

    G = nx.DiGraph()
    for asset_id, path in all_paths.items():
        for i in range(len(path) - 1):
            G.add_edge(path[i], path[i + 1])

    sorted_nodes = sorted(all_impacts.keys(), key=lambda x: all_impacts.get(x, 0), reverse=True)
    top_nodes = set(sorted_nodes[:max_nodes])
    subgraph_nodes = [n for n in G.nodes() if n in top_nodes]
    G = G.subgraph(subgraph_nodes)

    if not G.nodes():
        return _empty_figure("Graphe vide après filtrage")

    pos = nx.spring_layout(G, seed=42, k=2.5)

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=0.8, color="rgba(0,38,84,0.24)"),
        hoverinfo="none",
    )

    node_x, node_y, node_color, node_size, node_hover, node_text = [], [], [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        impact_pct = all_impacts.get(node, 0.0) * 100
        info = asset_index.get(node, {})
        name = info.get("name", node)
        node_x.append(x)
        node_y.append(y)
        node_color.append(impact_pct)
        node_size.append(max(6, min(20, impact_pct / 5)))
        node_text.append(node if impact_pct > 50 else "")
        node_hover.append(
            f"<b>{name}</b><br>"
            f"ID : {node}<br>"
            f"Impact : {impact_pct:.1f}/100<br>"
            f"Type : {info.get('type', '')}<br>"
            f"Criticité : {info.get('criticality', '')}"
        )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        textfont=dict(size=6, color=_TEXT_SEC, family="IBM Plex Mono, monospace"),
        hovertext=node_hover,
        hoverinfo="text",
        marker=dict(
            size=node_size,
            color=node_color,
            colorscale=[
                [0.0,  "#E7ECF3"],
                [0.2,  SEVERITY_COLORS["Low"]],
                [0.4,  SEVERITY_COLORS["Significant"]],
                [0.7,  SEVERITY_COLORS["High"]],
                [1.0,  SEVERITY_COLORS["Critical"]],
            ],
            cmin=0, cmax=100,
            colorbar=dict(
                title=dict(text="Impact", font=dict(size=9, color=_TEXT_SEC)),
                tickfont=dict(size=8, color=_TEXT_SEC),
                thickness=10,
                len=0.7,
                bgcolor=_CARD_BG,
                bordercolor=_BORDER,
                borderwidth=1,
            ),
            line=dict(width=0.7, color="#FFFFFF"),
        ),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        **_base_layout(height=460),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=4, r=4, t=8, b=4),
        annotations=[dict(
            text=f"{len(G.nodes())} actifs — {len(G.edges())} liens de dépendance",
            xref="paper", yref="paper", x=0, y=1.01,
            showarrow=False,
            font=dict(size=8, color=_TEXT_SEC),
        )],
    )
    return fig


# ---------------------------------------------------------------------------
# Geographic map
# ---------------------------------------------------------------------------

_CITY_COORDS: dict[str, tuple[float, float]] = {
    "New York": (40.71, -74.01),
    "Dubaï": (25.20, 55.27), "Dubai": (25.20, 55.27),
    "Singapour": (1.35, 103.82), "Singapore": (1.35, 103.82),
    "Yokohama": (35.44, 139.64),
    "Tokyo": (35.69, 139.69),
    "Santos": (-23.96, -46.33),
    "Marseille": (43.30, 5.37),
    "Hambourg": (53.55, 9.99), "Hamburg": (53.55, 9.99),
    "Rio de Janeiro": (-22.91, -43.17),
    "Brême": (53.07, 8.80), "Bremen": (53.07, 8.80),
    "Amsterdam": (52.37, 4.90),
    "Le Havre": (49.49, 0.11),
    "Dunkerque": (51.03, 2.38),
    "Ningbo": (29.87, 121.55),
    "Busan": (35.10, 129.04),
    "Nantes": (47.22, -1.55),
    "Rotterdam": (51.92, 4.48),
    "Houston": (29.76, -95.37),
    "Anvers": (51.22, 4.40), "Antwerp": (51.22, 4.40),
    "Los Angeles": (34.05, -118.24),
    "Shanghai": (31.23, 121.47),
    "Hong Kong": (22.32, 114.17),
}


def plot_geo_map(geo_df: pd.DataFrame) -> go.Figure:
    if geo_df.empty:
        return _empty_figure("Aucune donnée géographique")

    lats, lons, texts, colors, sizes = [], [], [], [], []
    for _, row in geo_df.iterrows():
        city = row["location"].split(",")[0].strip()
        if city not in _CITY_COORDS:
            continue
        lat, lon = _CITY_COORDS[city]
        lats.append(lat)
        lons.append(lon)
        texts.append(
            f"<b>{row['location']}</b><br>"
            f"Impact max : {row['max_impact']:.1f}/100<br>"
            f"Actifs : {row['asset_count']}<br>"
            f"Sévérité : {row['severity']}"
        )
        colors.append(row["max_impact"])
        sizes.append(max(8, min(32, row["max_impact"] / 3.0)))

    if not lats:
        return _empty_figure("Aucune localisation cartographiable")

    fig = go.Figure(go.Scattergeo(
        lat=lats, lon=lons,
        text=texts, hoverinfo="text",
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
            colorbar=dict(
                title=dict(text="Impact", font=dict(size=9, color=_TEXT_SEC)),
                tickfont=dict(size=8, color=_TEXT_SEC),
                thickness=10,
                bgcolor=_CARD_BG,
                bordercolor=_BORDER,
                borderwidth=1,
            ),
            line=dict(width=0.8, color=_BORDER),
        ),
    ))
    fig.update_layout(
        **_base_layout(height=380),
        geo=dict(
            showland=True,      landcolor="#ECEFF4",
            showocean=True,     oceancolor="#DCE8F7",
            showcountries=True, countrycolor="#B8C2D2",
            showcoastlines=True, coastlinecolor="#AAB6C8",
            showframe=False,
            projection_type="natural earth",
            bgcolor=_CARD_BG,
        ),
        margin=dict(l=0, r=0, t=8, b=0),
    )
    return fig


# ---------------------------------------------------------------------------
# Batch priority chart
# ---------------------------------------------------------------------------

def plot_batch_priority(ranked_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart for batch threat ranking."""
    if ranked_df.empty:
        return _empty_figure("Aucune menace analysée")

    df = ranked_df.head(20).iloc[::-1]  # top 20, lowest first for horizontal bar
    colors = [_impact_color(s) for s in df["global_impact"]]

    labels = df.apply(
        lambda r: f"#{r['rank']}  {str(r['event_id'])[:16]}",
        axis=1,
    )

    fig = go.Figure(go.Bar(
        x=df["global_impact"],
        y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=df["global_impact"].apply(lambda x: f"{x:.0f}"),
        textposition="outside",
        textfont=dict(size=10, color=_TEXT_SEC, family="IBM Plex Mono, monospace"),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Impact : %{x:.1f}/100<br>"
            "Type : %{customdata[0]}<br>"
            "Sévérité : %{customdata[1]}<extra></extra>"
        ),
        customdata=df[["event_type", "severity_label"]].values,
    ))
    fig.update_layout(
        **_base_layout(height=max(280, len(df) * 38)),
        xaxis=dict(
            title="", range=[0, 112],
            tickfont=dict(size=9, color=_TEXT_SEC, family="IBM Plex Mono, monospace"),
            gridcolor=_GRID, zeroline=False,
        ),
        yaxis=dict(title="", tickfont=dict(size=9, color=_TEXT_PRI, family="IBM Plex Mono, monospace")),
        margin=dict(l=4, r=50, t=8, b=8),
    )
    return fig


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def severity_badge_html(label: str, small: bool = False) -> str:
    """Solid institutional badge: coloured background, white text."""
    color = SEVERITY_COLORS.get(label, "#6B7280")
    size = "0.62em" if small else "0.7em"
    return (
        f'<span style="'
        f'background:{color};color:#FFFFFF;'
        f'padding:3px 9px;letter-spacing:0.08em;'
        f'font-size:{size};font-weight:800;'
        f'text-transform:uppercase;border-radius:2px;'
        f'box-shadow:0 1px 0 rgba(0,0,0,0.12);">'
        f'{label.upper()}'
        f'</span>'
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _base_layout(height: int = 400) -> dict:
    return dict(
        height=height,
        showlegend=False,
        hovermode="closest",
        plot_bgcolor=_CARD_BG,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=_TEXT_SEC, size=10),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=_BORDER,
            font=dict(color=_TEXT_PRI, size=11),
        ),
    )


def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=_TEXT_SEC, size=11, family="monospace"),
    )
    fig.update_layout(**_base_layout(height=200))
    return fig
