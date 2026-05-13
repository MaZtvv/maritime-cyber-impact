"""Maritime Cyber Impact Analyser — Streamlit entry point."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd

from data_loader import load_all_data
from event_classifier import classify_event
from impact_engine import run_analysis
from geo_analyzer import aggregate_geo_impact
from batch_analyzer import (
    parse_uploaded_csv_events,
    parse_uploaded_stix_events,
    analyze_batch_events,
    rank_events_by_priority,
)
from visualizer import (
    plot_process_bar,
    plot_propagation_graph,
    plot_geo_map,
    plot_batch_priority,
    severity_badge_html,
    SEVERITY_COLORS,
    SEVERITY_BG_COLORS,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MICA — Analyse d'Impact Cyber Maritime",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Naval CSS theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
:root {
    --mica-ink: #111827;
    --mica-navy: #002654;
    --mica-navy-2: #08335F;
    --mica-red: #C6002B;
    --mica-red-dark: #9F0024;
    --mica-bg: #F1F3F7;
    --mica-panel: #FFFFFF;
    --mica-border: #D8DEE8;
    --mica-border-strong: #B8C2D2;
    --mica-muted: #667085;
    --mica-shadow: 0 16px 38px rgba(0, 38, 84, 0.08);
    --mica-shadow-soft: 0 8px 22px rgba(15, 23, 42, 0.06);
}

html, body, [class*="css"] {
    font-family: Inter, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    color: var(--mica-ink);
}

.stApp {
    background:
        linear-gradient(180deg, rgba(0,38,84,0.045) 0%, rgba(241,243,247,0.96) 240px),
        radial-gradient(circle at top right, rgba(198,0,43,0.045), transparent 28rem),
        linear-gradient(rgba(0,38,84,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,38,84,0.018) 1px, transparent 1px),
        var(--mica-bg);
    background-size: auto, auto, 36px 36px, 36px 36px, auto;
}

.main .block-container {
    padding: 0 1.75rem 2.6rem;
    max-width: 1540px;
}

#MainMenu, footer, header { visibility: hidden; }
hr {
    border: none;
    border-top: 1px solid var(--mica-border);
    margin: 1.05rem 0;
}
p, li, .stMarkdown {
    color: #344054;
    font-size: 0.86rem;
}
h1, h2, h3 {
    color: var(--mica-navy) !important;
    letter-spacing: 0;
}

/* Sidebar as operational control rail */
[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #001D42 0%, #002654 48%, #06172B 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.14);
    box-shadow: 10px 0 30px rgba(0, 21, 48, 0.20);
}
[data-testid="stSidebar"] > div:first-child { padding: 0; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
    color: rgba(255,255,255,0.78) !important;
    font-size: 0.8rem;
}
[data-testid="stSidebar"] .section-header {
    color: rgba(255,255,255,0.48) !important;
    border-bottom-color: rgba(255,255,255,0.16) !important;
}
[data-testid="stSidebar"] .section-header:after { background: rgba(255,255,255,0.16) !important; }
[data-testid="stSidebar"] hr {
    border-top: 1px solid rgba(255,255,255,0.12) !important;
    margin: 0.8rem 0;
}

[data-testid="stSidebar"] [data-testid="stRadio"] > div { gap: 0.35rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.72) !important;
    padding: 0.55rem 0.65rem;
    transition: background .16s ease, border-color .16s ease, color .16s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
    background: rgba(255,255,255,0.09);
    border-color: rgba(255,255,255,0.22);
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) {
    color: #FFFFFF !important;
    background: rgba(198,0,43,0.22);
    border-color: rgba(198,0,43,0.75);
    font-weight: 650;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
[data-testid="stSidebar"] [data-testid="stTextArea"] label,
[data-testid="stSidebar"] [data-testid="stFileUploader"] label {
    color: rgba(255,255,255,0.50) !important;
    font-size: 0.66rem !important;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 700;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div,
[data-testid="stSidebar"] textarea {
    background: rgba(255,255,255,0.075) !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
    color: #FFFFFF !important;
    border-radius: 3px !important;
    font-size: 0.8rem !important;
}
[data-testid="stSidebar"] textarea::placeholder { color: rgba(255,255,255,0.36) !important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.055) !important;
    border: 1px dashed rgba(255,255,255,0.28) !important;
    border-radius: 3px;
    padding: 0.5rem;
}

/* Buttons */
.stButton > button {
    background: var(--mica-navy);
    border: 1px solid var(--mica-navy);
    border-radius: 3px;
    color: #FFFFFF;
    font-size: 0.72rem;
    font-weight: 750;
    letter-spacing: 0.105em;
    padding: 0.62rem 1.1rem;
    text-transform: uppercase;
    transition: transform .12s ease, background .12s ease, border-color .12s ease, box-shadow .12s ease;
    width: 100%;
}
.stButton > button:hover {
    background: var(--mica-navy-2);
    border-color: var(--mica-navy-2);
    transform: translateY(-1px);
    box-shadow: 0 10px 22px rgba(0,38,84,0.18);
}
[data-testid="baseButton-primary"] {
    background: var(--mica-red) !important;
    border-color: var(--mica-red) !important;
    color: #FFFFFF !important;
}
[data-testid="baseButton-primary"]:hover {
    background: var(--mica-red-dark) !important;
    border-color: var(--mica-red-dark) !important;
    box-shadow: 0 10px 24px rgba(198,0,43,0.26) !important;
}

/* Expanders, tables, alerts */
[data-testid="stExpander"] > details > summary {
    background: linear-gradient(90deg, #FFFFFF, #FBFCFE);
    border: 1px solid var(--mica-border);
    border-left: 3px solid var(--mica-navy);
    border-radius: 4px;
    color: var(--mica-ink);
    font-size: 0.81rem;
    font-weight: 650;
    letter-spacing: 0.015em;
    padding: 0.72rem 0.9rem;
}
[data-testid="stExpander"] > details[open] > summary {
    border-left-color: var(--mica-red);
    color: var(--mica-navy);
}
[data-testid="stExpander"] > details > div {
    background: rgba(255,255,255,0.72);
    border: 1px solid var(--mica-border);
    border-top: none;
    border-radius: 0 0 4px 4px;
    padding: 0.95rem;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--mica-border);
    border-radius: 4px;
    box-shadow: var(--mica-shadow-soft);
}
[data-testid="stAlert"] {
    border-radius: 4px;
    border: 1px solid var(--mica-border);
    font-size: 0.82rem;
}

/* Header */
.mn-topbar {
    background:
        linear-gradient(135deg, #001D42 0%, #002654 58%, #0A3866 100%);
    border: 1px solid rgba(255,255,255,0.10);
    box-shadow: var(--mica-shadow);
    margin: 0 -0.15rem 1.45rem;
    overflow: hidden;
}
.mn-topbar-stripe {
    height: 4px;
    background: linear-gradient(to right, #002654 0 36%, #FFFFFF 36% 67%, #C6002B 67% 100%);
    opacity: 0.96;
}
.mn-topbar-body {
    align-items: center;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding: 1.05rem 1.25rem 1.1rem;
}
.mn-topbar-brand { display: flex; align-items: center; gap: 1rem; min-width: 0; }
.mn-topbar-emblem {
    align-items: center;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.24);
    display: flex;
    flex-shrink: 0;
    height: 48px;
    justify-content: center;
    width: 48px;
}
.mn-topbar-rf {
    color: rgba(255,255,255,0.48);
    font-size: 0.52rem;
    font-weight: 650;
    letter-spacing: 0.24em;
    text-transform: uppercase;
}
.mn-topbar-org {
    color: rgba(255,255,255,0.78);
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    margin-top: 2px;
    text-transform: uppercase;
}
.mn-topbar-title {
    color: #FFFFFF;
    font-size: 1.18rem;
    font-weight: 780;
    letter-spacing: 0.018em;
    line-height: 1.2;
    margin-top: 0.18rem;
}
.mn-topbar-meta { text-align: right; min-width: 220px; }
.mn-topbar-version {
    color: rgba(255,255,255,0.48);
    font-size: 0.58rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}
.mn-topbar-status {
    color: rgba(255,255,255,0.76);
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    margin-top: 0.32rem;
    text-transform: uppercase;
}
.mn-status-dot {
    background: #23C16B;
    border-radius: 50%;
    box-shadow: 0 0 0 4px rgba(35,193,107,0.14);
    display: inline-block;
    height: 7px;
    margin-right: 7px;
    width: 7px;
}

/* Sidebar brand */
.mn-sidebar-brand {
    background: rgba(0,0,0,0.16);
    border-bottom: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 0.3rem;
}
.mn-sidebar-stripe {
    height: 3px;
    background: linear-gradient(to right, #002654 0 36%, #FFFFFF 36% 67%, #C6002B 67% 100%);
}
.mn-sidebar-inner { padding: 1rem 1.18rem 0.95rem; }
.mn-sidebar-rf {
    color: rgba(255,255,255,0.42);
    font-size: 0.5rem;
    font-weight: 650;
    letter-spacing: 0.22em;
    text-transform: uppercase;
}
.mn-sidebar-name {
    color: rgba(255,255,255,0.70);
    font-size: 0.62rem;
    font-weight: 720;
    letter-spacing: 0.17em;
    margin-top: 2px;
    text-transform: uppercase;
}
.mn-sidebar-app {
    color: #FFFFFF;
    font-size: 1.42rem;
    font-weight: 790;
    letter-spacing: 0.12em;
    margin-top: 0.22rem;
}
.mn-sidebar-tagline {
    color: rgba(255,255,255,0.48);
    font-size: 0.61rem;
    letter-spacing: 0.055em;
    margin-top: 1px;
}

/* Operational modules */
.section-header {
    align-items: center;
    color: var(--mica-navy);
    display: flex;
    font-size: 0.68rem;
    font-weight: 800;
    gap: 0.55rem;
    letter-spacing: 0.17em;
    margin: 0.15rem 0 0.82rem;
    text-transform: uppercase;
}
.section-header:before {
    background: var(--mica-red);
    content: "";
    display: inline-block;
    height: 10px;
    width: 3px;
}
.section-header:after {
    background: var(--mica-border);
    content: "";
    flex: 1;
    height: 1px;
}

.op-card {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,253,0.98));
    border: 1px solid var(--mica-border);
    border-top: 3px solid var(--mica-navy);
    box-shadow: var(--mica-shadow-soft);
    min-height: 128px;
    padding: 1.05rem 1rem 0.85rem;
    position: relative;
    text-align: left;
    transition: transform .14s ease, border-color .14s ease, box-shadow .14s ease;
}
.op-card:hover {
    border-color: var(--mica-border-strong);
    box-shadow: var(--mica-shadow);
    transform: translateY(-1px);
}
.op-card:after {
    background: linear-gradient(90deg, rgba(0,38,84,0.09), transparent);
    bottom: 0;
    content: "";
    height: 1px;
    left: 0;
    position: absolute;
    right: 0;
}
.op-card-value {
    color: var(--mica-navy);
    font-size: clamp(2rem, 3vw, 2.85rem);
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1;
}
.op-card-unit {
    color: var(--mica-muted);
    font-size: 0.42em;
    font-weight: 700;
    margin-left: 0.12rem;
}
.op-card-label {
    color: var(--mica-muted);
    font-size: 0.6rem;
    font-weight: 750;
    letter-spacing: 0.15em;
    line-height: 1.45;
    margin-top: 0.58rem;
    min-height: 1.7rem;
    text-transform: uppercase;
}
.op-card-badge { margin-top: 0.58rem; }

.info-row {
    background: rgba(255,255,255,0.62);
    border: 1px solid rgba(216,222,232,0.84);
    color: #3B4758;
    font-size: 0.82rem;
    line-height: 1.75;
    padding: 0.78rem 0.9rem;
}
[data-testid="stSidebar"] .info-row {
    background: rgba(255,255,255,0.055);
    border-color: rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.74);
}
.info-row b {
    color: var(--mica-navy);
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.10em;
    margin-right: 0.35rem;
    text-transform: uppercase;
}
[data-testid="stSidebar"] .info-row b { color: rgba(255,255,255,0.92); }
.info-row code {
    background: #EDF2F7;
    border: 1px solid #D8DEE8;
    color: var(--mica-navy);
    font-size: 0.77rem;
    padding: 1px 5px;
}

.action-item {
    background: linear-gradient(90deg, #FFFFFF, #F8FAFD);
    border: 1px solid var(--mica-border);
    border-left: 3px solid var(--mica-red);
    box-shadow: var(--mica-shadow-soft);
    color: #263447;
    font-size: 0.84rem;
    line-height: 1.62;
    margin-bottom: 0.55rem;
    padding: 0.78rem 0.95rem;
}
.action-number {
    color: var(--mica-red);
    display: block;
    font-size: 0.6rem;
    font-weight: 820;
    letter-spacing: 0.14em;
    margin-bottom: 0.2rem;
    text-transform: uppercase;
}

.mission-brief {
    background: linear-gradient(90deg, rgba(255,255,255,0.94), rgba(247,249,252,0.88));
    border: 1px solid var(--mica-border);
    border-left: 3px solid var(--mica-navy);
    box-shadow: var(--mica-shadow-soft);
    color: #3B4758;
    font-size: 0.9rem;
    line-height: 1.75;
    margin-top: 0.6rem;
    padding: 1.15rem 1.25rem;
}
.mission-brief strong { color: var(--mica-red); letter-spacing: 0.04em; }

.topbar-chip {
    border: 1px solid rgba(255,255,255,0.16);
    color: rgba(255,255,255,0.74);
    display: inline-block;
    font-size: 0.55rem;
    font-weight: 720;
    letter-spacing: 0.12em;
    margin-top: 0.45rem;
    padding: 0.2rem 0.42rem;
    text-transform: uppercase;
}

@media (max-width: 900px) {
    .main .block-container { padding: 0 0.85rem 2rem; }
    .mn-topbar-body { align-items: flex-start; flex-direction: column; }
    .mn-topbar-meta { text-align: left; min-width: 0; }
    .mn-topbar-title { font-size: 1rem; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _section(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def _metric_card(value: str, unit: str, label: str, badge_html: str = "", color: str = "#002654"):
    st.markdown(
        f'<div class="op-card">'
        f'<div class="op-card-value" style="color:{color}">{value}'
        f'<span class="op-card-unit">{unit}</span></div>'
        f'<div class="op-card-label">{label}</div>'
        f'<div class="op-card-badge">{badge_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _geo_impact_from_result(result):
    return aggregate_geo_impact(
        {row["asset_id"]: row["impact"] / 100.0 for _, row in result.asset_impacts.iterrows()},
        data["asset_index"],
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Chargement des données opérationnelles…")
def get_data():
    return load_all_data()


data = get_data()
events_df: pd.DataFrame = data["events"]


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div class="mn-sidebar-brand">
        <div class="mn-sidebar-stripe"></div>
        <div class="mn-sidebar-inner">
            <div class="mn-sidebar-rf">République Française</div>
            <div class="mn-sidebar-name">Marine Nationale</div>
            <div class="mn-sidebar-app">MICA</div>
            <div class="mn-sidebar-tagline">Analyse d'Impact Cyber Maritime</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding: 0.9rem 1.2rem 0;">', unsafe_allow_html=True)

    st.markdown('<div class="section-header">MODE DE SAISIE</div>', unsafe_allow_html=True)

    input_mode = st.radio(
        label="Mode de saisie",
        options=[
            "Sélectionner un événement",
            "Événement libre (texte)",
            "Importer un fichier",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")

    selected_event_row = None
    batch_records = []
    upload_errors = []

    # ── Mode 1: existing event ──────────────────────────────────────────────
    if input_mode == "Sélectionner un événement":
        st.markdown('<div class="section-header">ÉVÉNEMENT</div>', unsafe_allow_html=True)
        event_options = (
            events_df["id"] + "  |  " + events_df["type"] + "  —  " + events_df["description"]
        ).tolist()
        chosen = st.selectbox("Événement à analyser", event_options, label_visibility="collapsed")
        event_id = chosen.split("  |  ")[0].strip()
        selected_event_row = events_df[events_df["id"] == event_id].iloc[0]

        st.markdown(
            f'<div class="info-row" style="margin-top:0.6rem;">'
            f'<b>TYPE</b> {selected_event_row["type"]}<br>'
            f'<b>SÉVÉRITÉ</b> {selected_event_row["severity"].upper()}<br>'
            f'<b>SOURCE</b> {selected_event_row["source"]}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Mode 2: free text ───────────────────────────────────────────────────
    elif input_mode == "Événement libre (texte)":
        st.markdown('<div class="section-header">DESCRIPTION DE L\'ÉVÉNEMENT</div>', unsafe_allow_html=True)
        free_text = st.text_area(
            "", height=90,
            placeholder="Ex: réseau indisponible port Marseille…",
            label_visibility="collapsed",
        )
        if free_text.strip():
            cl = classify_event(free_text)
            st.markdown(
                f'<div class="info-row" style="margin-top:0.4rem;">'
                f'<b>CLASSIFIÉ</b> {cl["event_type"]}<br>'
                f'<b>CORRESPOND</b> {cl["matched_description"]}<br>'
                f'<b>CONFIANCE</b> {cl["confidence"]:.0f}%'
                f'</div>',
                unsafe_allow_html=True,
            )
            override_type = st.selectbox(
                "TYPE (optionnel)",
                ["— auto-détecté —", "Panne Système", "Attaque Détectée",
                 "Incident", "Alerte", "Maintenance"],
            )
            override_sev = st.selectbox("SÉVÉRITÉ", ["medium", "low", "high", "critical"])
            etype = cl["event_type"] if override_type.startswith("—") else override_type
            selected_event_row = pd.Series({
                "id": "new-event",
                "name": "Événement libre",
                "type": etype,
                "severity": override_sev,
                "description": cl["matched_description"],
                "source": "manual",
                "related_assets": "",
                "related_attacks": "",
                "cvss_override": "",
            })

    # ── Mode 3: file upload ─────────────────────────────────────────────────
    else:
        st.markdown('<div class="section-header">IMPORT DE FICHIER</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="info-row">CSV ou STIX 2.x JSON<br>'
            'Plusieurs événements simultanés</div>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "",
            type=["csv", "json"],
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            if uploaded_file.name.endswith(".csv"):
                batch_records, upload_errors = parse_uploaded_csv_events(file_bytes)
            else:
                batch_records, upload_errors = parse_uploaded_stix_events(file_bytes)

            if upload_errors:
                for err in upload_errors:
                    st.error(err)
            elif batch_records:
                st.success(f"{len(batch_records)} événement(s) chargé(s)")

    st.markdown("---")

    run_btn = st.button(
        "LANCER L'ANALYSE",
        type="primary",
        use_container_width=True,
    )

    st.markdown(
        '<div style="padding-top:1rem;">'
        '<div class="info-row" style="font-size:0.62rem;">'
        'MICA v1.0 · Hackathon Albert 2026<br>'
        'Usage interne — données synthétiques'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main area header
# ---------------------------------------------------------------------------

st.markdown("""
<div class="mn-topbar">
    <div class="mn-topbar-stripe"></div>
    <div class="mn-topbar-body">
        <div class="mn-topbar-brand">
            <div class="mn-topbar-emblem">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <path d="M14 2.5v19" stroke="white" stroke-width="1.7" stroke-linecap="square"/>
                    <circle cx="14" cy="7.2" r="3.1" stroke="white" stroke-width="1.5"/>
                    <path d="M5.5 12.5h17" stroke="white" stroke-width="1.5" stroke-linecap="square" opacity="0.86"/>
                    <path d="M6.2 16.2c1.3 4.4 4.2 7 7.8 8.6 3.6-1.6 6.5-4.2 7.8-8.6" stroke="white" stroke-width="1.5" stroke-linecap="square"/>
                    <path d="M4.2 18.5l2-2 2 2M19.8 18.5l2-2 2 2" stroke="white" stroke-width="1.3" stroke-linecap="square"/>
                    <circle cx="22.7" cy="5.2" r="1.5" fill="#C6002B"/>
                </svg>
            </div>
            <div>
                <div class="mn-topbar-rf">République Française</div>
                <div class="mn-topbar-org">Marine Nationale &nbsp;·&nbsp; Commandement Cyber</div>
                <div class="mn-topbar-title">MICA OPS — Maritime Impact Cyber Analysis</div>
                <span class="topbar-chip">Operational picture</span>
                <span class="topbar-chip">Business impact</span>
                <span class="topbar-chip">Propagation graph</span>
            </div>
        </div>
        <div class="mn-topbar-meta">
            <div class="mn-topbar-version">v1.0 · Hackathon Albert 2026</div>
            <div class="mn-topbar-status">
                <span class="mn-status-dot"></span>Système opérationnel
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Gate: require button press
# ---------------------------------------------------------------------------

if not run_btn:
    st.markdown(
        '<div class="mission-brief">'
        'Sélectionnez ou décrivez un événement dans le panneau latéral,<br>'
        'puis cliquez sur <strong>LANCER L\'ANALYSE</strong>.'
        '</div>',
        unsafe_allow_html=True,
    )
    if input_mode == "Importer un fichier":
        _section("FORMAT CSV ATTENDU")
        st.code(
            "event_id,event_type,severity,description,source,timestamp,affected_asset_id,attack_id,cvss_score\n"
            "evt-001,Panne Système,critical,\"Panne système: Réseau indisponible.\",firewall,2025-01-15T08:00:00Z,IT-00001,CVE-2021-44228,10.0\n"
            "evt-002,Attaque Détectée,high,\"Attaque détectée: Exploitation de Log4Shell.\",suricata,2025-01-15T09:00:00Z,\"IT-00002,IT-00003\",T1059,7.5",
            language="text",
        )
        _section("FORMAT STIX 2.x SUPPORTÉ")
        st.markdown(
            '<div class="info-row">'
            'Types : <code>indicator</code>, <code>malware</code>, <code>intrusion-set</code>, '
            '<code>attack-pattern</code>, <code>observed-data</code>, <code>vulnerability</code>'
            '</div>',
            unsafe_allow_html=True,
        )
    st.stop()


# ---------------------------------------------------------------------------
# ── SINGLE EVENT ANALYSIS ──────────────────────────────────────────────────
# ---------------------------------------------------------------------------

if input_mode != "Importer un fichier":

    if selected_event_row is None:
        st.warning("Aucun événement sélectionné.")
        st.stop()

    with st.spinner("Calcul de l'impact opérationnel…"):
        result = run_analysis(selected_event_row, data)
        result.geo_impacts = _geo_impact_from_result(result)

    sev_color = SEVERITY_COLORS.get(result.severity_label, "#556677")

    # ── Summary cards ───────────────────────────────────────────────────────
    _section("TABLEAU DE BORD OPÉRATIONNEL")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_card(
            f"{result.global_impact:.0f}", "/100",
            "IMPACT OPÉRATIONNEL GLOBAL",
            severity_badge_html(result.severity_label),
            color=sev_color,
        )
    with c2:
        _metric_card(str(len(result.asset_impacts)), "", "ACTIFS IMPACTÉS")
    with c3:
        _metric_card(str(len(result.process_impacts)), "", "PROCESSUS MÉTIER")
    with c4:
        n_locs = len(result.geo_impacts) if not result.geo_impacts.empty else 0
        _metric_card(str(n_locs), "", "ZONES GÉOGRAPHIQUES")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Process impact + Geo map ─────────────────────────────────────────────
    col_l, col_r = st.columns([1, 1], gap="medium")

    with col_l:
        _section("IMPACT PAR PROCESSUS MÉTIER")
        if not result.process_impacts.empty:
            st.plotly_chart(plot_process_bar(result.process_impacts), use_container_width=True)
            disp = result.process_impacts[
                ["process", "impact_score", "severity", "asset_count"]
            ].rename(columns={
                "process": "Processus",
                "impact_score": "Score",
                "severity": "Sévérité",
                "asset_count": "Actifs",
            })
            st.dataframe(disp, use_container_width=True, hide_index=True, height=220)
        else:
            st.info("Aucun processus métier identifié.")

    with col_r:
        _section("IMPACT GÉOGRAPHIQUE")
        if not result.geo_impacts.empty:
            st.plotly_chart(plot_geo_map(result.geo_impacts), use_container_width=True)
            geo_disp = result.geo_impacts[
                ["location", "country", "max_impact", "asset_count", "severity"]
            ].rename(columns={
                "max_impact": "Impact max",
                "asset_count": "Actifs",
                "location": "Localisation",
                "country": "Pays",
                "severity": "Sévérité",
            })
            st.dataframe(geo_disp.head(12), use_container_width=True, hide_index=True, height=200)
        else:
            st.info("Aucune donnée géographique disponible.")

    st.markdown("---")

    # ── Assets + Propagation graph ───────────────────────────────────────────
    col_a, col_b = st.columns([1, 1], gap="medium")

    with col_a:
        _section("ACTIFS IMPACTÉS")
        if not result.asset_impacts.empty:
            disp_a = result.asset_impacts[
                ["asset_id", "name", "type", "criticality", "impact", "hop", "location"]
            ].rename(columns={
                "asset_id": "ID",
                "name": "Nom",
                "type": "Type",
                "criticality": "Criticité",
                "impact": "Score",
                "hop": "Saut",
                "location": "Localisation",
            })
            st.dataframe(disp_a.head(50), use_container_width=True, hide_index=True, height=380)
        else:
            st.warning("Aucun actif identifié.")

    with col_b:
        _section("GRAPHE DE PROPAGATION")
        if result.propagation_paths:
            fig_graph = plot_propagation_graph(
                result.propagation_paths,
                {r["asset_id"]: r["impact"] / 100.0 for _, r in result.asset_impacts.iterrows()},
                data["asset_index"],
            )
            st.plotly_chart(fig_graph, use_container_width=True)
        else:
            st.info("Aucun chemin de propagation calculé.")

    st.markdown("---")

    # ── Priority actions ─────────────────────────────────────────────────────
    _section("PLAN D'ACTION PRIORITAIRE")
    if result.actions:
        for action in result.actions:
            badge = severity_badge_html(action["severity"])
            with st.expander(
                f"N°{action['priority']:02d}  ·  {action['process']}  ·  Score {action['impact_score']:.0f}/100",
                expanded=action["priority"] <= 3,
            ):
                st.markdown(
                    f'<div class="info-row">'
                    f'Sévérité : {badge}&nbsp;&nbsp;'
                    f'<b>Score :</b> {action["impact_score"]:.1f} / 100'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if action["top_assets"]:
                    st.markdown(
                        f'<div class="info-row"><b>Actifs prioritaires :</b>'
                        f' <code>{action["top_assets"]}</code></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div class="action-item">'
                    f'<span class="action-number">ACTION RECOMMANDÉE</span><br>'
                    f'{action["mitigation"]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("Aucune action générée.")

    st.markdown("---")

    # ── Explanation panel ────────────────────────────────────────────────────
    _section("DÉTAIL DU CALCUL DE SCORE")
    bd = result.score_breakdown
    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown(
            f'<div class="info-row">'
            f'<b>TYPE</b> {bd.get("event_type", "—")}<br>'
            f'<b>SÉVÉRITÉ</b> {bd.get("event_severity", "—").upper()}<br>'
            f'<b>DESCRIPTION</b> {bd.get("description", "—")}<br>'
            f'<b>CVSS MAX</b> {bd.get("max_cvss", 5.0):.1f}<br>'
            f'<b>SCORE DE BASE ÉVÉNEMENT</b> {bd.get("event_base_score", 0.0):.1f} / 100'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_e2:
        attacks_str = ", ".join(bd.get("linked_attacks", [])) or "aucune"
        st.markdown(
            f'<div class="info-row">'
            f'<b>ACTIFS DIRECTS</b> {bd.get("direct_asset_count", 0)}<br>'
            f'<b>ACTIFS APRÈS PROPAGATION</b> {bd.get("total_asset_count", 0)}<br>'
            f'<b>ATTAQUES LIÉES</b> {attacks_str}<br>'
            f'<b>IMPACT GLOBAL FINAL</b> {result.global_impact:.1f} / 100<br>'
            f'<span style="font-size:0.72rem;color:#6b7f95;">'
            f'global = max × 0.6 + moyenne × 0.4</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if not result.process_impacts.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        _section("DÉCOMPOSITION PAR PROCESSUS (TOP 5)")
        top5 = result.process_impacts.head(5)[
            ["process", "process_criticality", "exposure_score", "impact_score", "severity"]
        ].rename(columns={
            "process": "Processus",
            "process_criticality": "Criticité expert",
            "exposure_score": "Exposition actifs",
            "impact_score": "Score final",
            "severity": "Sévérité",
        })
        st.dataframe(top5, use_container_width=True, hide_index=True)
        st.markdown(
            '<div class="info-row" style="font-size:0.68rem;">'
            'Score final = 0.7 × Criticité expert + 0.3 × Exposition actifs normalisée'
            '</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# ── BATCH ANALYSIS ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

else:
    if not batch_records:
        st.markdown(
            '<div style="padding:1.5rem 0; color:#6b7f95; font-size:0.82rem; font-family:monospace;">'
            '&gt; Importez un fichier CSV ou STIX JSON dans le panneau latéral.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    # Preview table
    _section(f"APERÇU — {len(batch_records)} ÉVÉNEMENT(S) IMPORTÉ(S)")
    preview_data = pd.DataFrame([{
        "ID": r["id"],
        "Type": r["type"],
        "Sévérité": r["severity"],
        "Description": r["description"][:70] + ("…" if len(r["description"]) > 70 else ""),
    } for r in batch_records])
    st.dataframe(preview_data, use_container_width=True, hide_index=True, height=180)

    st.markdown("---")

    with st.spinner(f"Analyse de {len(batch_records)} événement(s)…"):
        batch_results = analyze_batch_events(batch_records, data)
        ranked_df = rank_events_by_priority(batch_results)

    # ── Summary cards ────────────────────────────────────────────────────────
    _section("RÉSUMÉ DE L'ANALYSE BATCH")
    critical_count = len(ranked_df[ranked_df["severity_label"] == "Critical"])
    high_count = len(ranked_df[ranked_df["severity_label"] == "High"])
    max_impact = ranked_df["global_impact"].max() if not ranked_df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_card(str(len(batch_records)), "", "ÉVÉNEMENTS ANALYSÉS")
    with c2:
        _metric_card(str(critical_count), "", "NIVEAU CRITIQUE",
                     color=SEVERITY_COLORS["Critical"])
    with c3:
        _metric_card(str(high_count), "", "NIVEAU ÉLEVÉ",
                     color=SEVERITY_COLORS["High"])
    with c4:
        top_label = ranked_df.iloc[0]["severity_label"] if not ranked_df.empty else "—"
        _metric_card(f"{max_impact:.0f}", "/100", "IMPACT MAX DÉTECTÉ",
                     severity_badge_html(top_label),
                     color=SEVERITY_COLORS.get(top_label, "#d4dde8"))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Ranked threat chart + table ──────────────────────────────────────────
    col_chart, col_table = st.columns([1, 1], gap="medium")

    with col_chart:
        _section("CLASSEMENT DES MENACES PAR IMPACT OPÉRATIONNEL")
        st.plotly_chart(plot_batch_priority(ranked_df), use_container_width=True)

    with col_table:
        _section("MATRICE DE PRIORITÉ")
        if not ranked_df.empty:
            display_cols = [
                "rank", "event_id", "event_type", "severity_label",
                "global_impact", "asset_count", "top_process",
            ]
            display_df = ranked_df[display_cols].rename(columns={
                "rank": "#",
                "event_id": "ID",
                "event_type": "Type",
                "severity_label": "Sévérité",
                "global_impact": "Impact",
                "asset_count": "Actifs",
                "top_process": "Processus critique",
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=420)

    st.markdown("---")

    # ── Per-event drilldown ──────────────────────────────────────────────────
    _section("DÉTAIL PAR ÉVÉNEMENT")
    for batch_res in batch_results:
        sev_label = batch_res["severity_label"]
        badge = severity_badge_html(sev_label, small=True)
        with st.expander(
            f"{batch_res['event_id']}  ·  {batch_res['event_type']}  ·  Impact {batch_res['global_impact']:.0f}/100",
            expanded=False,
        ):
            if batch_res.get("error"):
                st.error(f"Erreur : {batch_res['error']}")
                continue

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f'<div class="info-row">'
                    f'<b>TYPE</b> {batch_res["event_type"]}<br>'
                    f'<b>SÉVÉRITÉ</b> {sev_label} {badge}<br>'
                    f'<b>IMPACT BASE</b> {batch_res["event_base_score"]:.1f} / 100<br>'
                    f'<b>IMPACT GLOBAL</b> {batch_res["global_impact"]:.1f} / 100<br>'
                    f'<b>ACTIFS IMPACTÉS</b> {batch_res["asset_count"]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col2:
                attacks_str = ", ".join(batch_res["linked_attacks"]) or "aucune"
                st.markdown(
                    f'<div class="info-row">'
                    f'<b>PROCESSUS CRITIQUE</b> {batch_res["top_process"]}<br>'
                    f'<b>SCORE PROCESSUS</b> {batch_res["top_process_score"]:.1f} / 100<br>'
                    f'<b>PROCESSUS AFFECTÉS</b> {batch_res["process_count"]}<br>'
                    f'<b>ATTAQUES LIÉES</b> {attacks_str}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            if batch_res["top_actions"]:
                st.markdown("<br>", unsafe_allow_html=True)
                for action in batch_res["top_actions"]:
                    st.markdown(
                        f'<div class="action-item">'
                        f'<span class="action-number">ACTION N°{action["priority"]}</span><br>'
                        f'{action["mitigation"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
