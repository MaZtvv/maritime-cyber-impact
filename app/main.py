"""Maritime Cyber Impact Analyser — Streamlit entry point."""

import sys
from pathlib import Path

# Allow sibling imports regardless of how Streamlit is launched
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd

from data_loader import load_all_data
from event_classifier import classify_event, DESCRIPTION_SCORES
from impact_engine import run_analysis, score_to_label
from geo_analyzer import aggregate_geo_impact
from visualizer import (
    plot_process_bar,
    plot_propagation_graph,
    plot_geo_map,
    severity_badge_html,
    SEVERITY_COLORS,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Maritime Cyber Impact Analyser",
    page_icon="🛡️",
    layout="wide",
)

st.markdown("""
<style>
.metric-card {
    background: #1e293b;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}
.metric-value { font-size: 2.2em; font-weight: 700; color: #f1f5f9; }
.metric-label { font-size: 0.85em; color: #94a3b8; margin-top: 4px; }
.section-title { font-size: 1.1em; font-weight: 600; margin-top: 1em; margin-bottom: 0.3em; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data…")
def get_data():
    return load_all_data()

data = get_data()
events_df: pd.DataFrame = data["events"]

# ---------------------------------------------------------------------------
# Sidebar — Event input
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🛡️ Maritime Cyber Impact")
    st.caption("Operational impact analysis for maritime IT/OT events")
    st.divider()

    input_mode = st.radio(
        "Event input mode",
        ["Select existing event", "Enter new event (free text)"],
        index=0,
    )

    selected_event_row = None
    classification_info = None

    if input_mode == "Select existing event":
        event_options = (
            events_df["id"] + " — " + events_df["type"] + " | " + events_df["description"]
        ).tolist()
        chosen = st.selectbox("Choose an event", event_options, index=0)
        event_id = chosen.split(" — ")[0].strip()
        selected_event_row = events_df[events_df["id"] == event_id].iloc[0]

        st.markdown("**Selected event details**")
        st.markdown(f"- **Type:** {selected_event_row['type']}")
        st.markdown(f"- **Severity:** {selected_event_row['severity']}")
        st.markdown(f"- **Description:** {selected_event_row['description']}")
        st.markdown(f"- **Source:** {selected_event_row['source']}")

    else:
        free_text = st.text_area(
            "Describe the event",
            placeholder="e.g. Network completely unavailable at port…",
            height=100,
        )
        if free_text.strip():
            classification_info = classify_event(free_text)
            st.markdown("**Auto-classification result**")
            st.markdown(f"- **Matched:** {classification_info['matched_description']}")
            st.markdown(f"- **Type:** {classification_info['event_type']}")
            st.markdown(f"- **Confidence:** {classification_info['confidence']:.0f}%")

            override_type = st.selectbox(
                "Override event type (optional)",
                ["— keep auto-detected —", "Panne Système", "Attaque Détectée",
                 "Incident", "Alerte", "Maintenance"],
            )
            override_severity = st.selectbox(
                "Severity",
                ["medium", "low", "high", "critical"],
            )
            # Build a synthetic event row
            detected_type = (
                classification_info["event_type"]
                if override_type.startswith("—")
                else override_type
            )
            selected_event_row = pd.Series({
                "id": "new-event",
                "name": "User-entered event",
                "type": detected_type,
                "severity": override_severity,
                "description": classification_info["matched_description"],
                "source": "manual",
                "related_assets": "",
                "related_attacks": "",
            })

    st.divider()
    run_btn = st.button("🔍 Run Impact Analysis", use_container_width=True, type="primary")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("Maritime Cyber Impact Analyser")

if not run_btn or selected_event_row is None:
    st.info(
        "Select or describe a cyber event in the sidebar and click **Run Impact Analysis**."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Run analysis
# ---------------------------------------------------------------------------
with st.spinner("Computing operational impact…"):
    result = run_analysis(selected_event_row, data)
    result.geo_impacts = aggregate_geo_impact(
        {k: v for k, v in zip(
            result.asset_impacts["asset_id"],
            result.asset_impacts["impact"] / 100.0,
        )},
        data["asset_index"],
    )

# ---------------------------------------------------------------------------
# Summary cards
# ---------------------------------------------------------------------------
badge = severity_badge_html(result.severity_label)
sev_color = SEVERITY_COLORS.get(result.severity_label, "#9e9e9e")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-value" style="color:{sev_color}">'
        f'{result.global_impact:.0f}<span style="font-size:0.5em">/100</span></div>'
        f'<div class="metric-label">Global Operational Impact</div>'
        f'<div style="margin-top:6px">{badge}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-value">{len(result.asset_impacts)}</div>'
        f'<div class="metric-label">Affected Assets</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-value">{len(result.process_impacts)}</div>'
        f'<div class="metric-label">Affected Business Processes</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with c4:
    n_locs = len(result.geo_impacts) if not result.geo_impacts.empty else 0
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-value">{n_locs}</div>'
        f'<div class="metric-label">Affected Locations</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Two-column layout: process impact + geo map
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Business Process Impact")
    if not result.process_impacts.empty:
        st.plotly_chart(plot_process_bar(result.process_impacts), use_container_width=True)

        disp_cols = ["process", "impact_score", "severity", "asset_count"]
        styled = result.process_impacts[disp_cols].rename(columns={
            "process": "Process",
            "impact_score": "Score",
            "severity": "Severity",
            "asset_count": "Assets",
        })
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.warning("No business processes identified. Check that `related_assets` is populated.")

with col_right:
    st.subheader("Geographic Impact")
    if not result.geo_impacts.empty:
        st.plotly_chart(plot_geo_map(result.geo_impacts), use_container_width=True)

        geo_disp = result.geo_impacts[["location", "country", "max_impact", "asset_count", "severity"]].rename(
            columns={"max_impact": "Max Impact", "asset_count": "Assets"}
        )
        st.dataframe(geo_disp.head(15), use_container_width=True, hide_index=True)
    else:
        st.info("No location data available for affected assets.")

st.divider()

# ---------------------------------------------------------------------------
# Affected assets + propagation graph
# ---------------------------------------------------------------------------
col_a, col_b = st.columns([1, 1])

with col_a:
    st.subheader("Affected Assets")
    if not result.asset_impacts.empty:
        disp = result.asset_impacts[
            ["asset_id", "name", "type", "criticality", "impact", "hop", "location"]
        ].rename(columns={
            "asset_id": "ID",
            "name": "Name",
            "type": "Type",
            "criticality": "Criticality",
            "impact": "Impact Score",
            "hop": "Hop",
            "location": "Location",
        })
        st.dataframe(disp.head(50), use_container_width=True, hide_index=True)
    else:
        st.warning("No assets found.")

with col_b:
    st.subheader("Propagation Graph")
    if result.propagation_paths:
        fig_graph = plot_propagation_graph(
            result.propagation_paths,
            {row["asset_id"]: row["impact"] / 100.0 for _, row in result.asset_impacts.iterrows()},
            data["asset_index"],
        )
        st.plotly_chart(fig_graph, use_container_width=True)
    else:
        st.info("No propagation paths computed.")

st.divider()

# ---------------------------------------------------------------------------
# Prioritised action list
# ---------------------------------------------------------------------------
st.subheader("Prioritised Response Actions")
if result.actions:
    for action in result.actions:
        badge_html = severity_badge_html(action["severity"])
        with st.expander(
            f"#{action['priority']}  {action['process']}  —  Score {action['impact_score']:.1f}",
            expanded=action["priority"] <= 3,
        ):
            st.markdown(f"**Severity:** {badge_html}", unsafe_allow_html=True)
            st.markdown(f"**Impact Score:** {action['impact_score']:.1f} / 100")
            if action["top_assets"]:
                st.markdown(f"**Priority assets to isolate:** `{action['top_assets']}`")
            st.markdown(f"**Recommended action:** {action['mitigation']}")
else:
    st.info("No actions generated.")

st.divider()

# ---------------------------------------------------------------------------
# Explanation panel
# ---------------------------------------------------------------------------
st.subheader("Score Explanation")
bd = result.score_breakdown
col_e1, col_e2 = st.columns(2)

with col_e1:
    st.markdown("**Event analysis**")
    st.markdown(f"- Event type: `{bd.get('event_type', '—')}`")
    st.markdown(f"- Severity: `{bd.get('event_severity', '—')}`")
    st.markdown(f"- Description: *{bd.get('description', '—')}*")
    st.markdown(f"- Max CVSS (linked attacks): **{bd.get('max_cvss', 5.0):.1f}**")
    st.markdown(f"- **Event base score: {bd.get('event_base_score', 0.0):.1f} / 100**")

with col_e2:
    st.markdown("**Propagation summary**")
    st.markdown(f"- Directly affected assets: **{bd.get('direct_asset_count', 0)}**")
    st.markdown(f"- Total assets after propagation: **{bd.get('total_asset_count', 0)}**")
    st.markdown(f"- Linked attack IDs: `{', '.join(bd.get('linked_attacks', [])) or 'none'}`")
    st.markdown(f"- **Global operational impact: {result.global_impact:.1f} / 100**")
    st.markdown(
        f"- Formula: `global = max_process × 0.6 + mean_process × 0.4`"
    )

if not result.process_impacts.empty:
    st.markdown("**Process score breakdown** (top 5)")
    top5 = result.process_impacts.head(5)[
        ["process", "process_criticality", "exposure_score", "impact_score", "severity"]
    ].rename(columns={
        "process": "Process",
        "process_criticality": "Expert Criticality",
        "exposure_score": "Asset Exposure",
        "impact_score": "Final Score",
        "severity": "Severity",
    })
    st.dataframe(top5, use_container_width=True, hide_index=True)
    st.caption(
        "Final Score = 0.7 × Expert Criticality + 0.3 × Asset Exposure  "
        "| Asset Exposure = normalised sum of (asset impact × criticality weight)"
    )
