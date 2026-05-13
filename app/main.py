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
/*
 * ═══════════════════════════════════════════════════════════════════════
 *  MICA — Marine Nationale Institutional Design System
 *  Tokens: --mn-navy:#002654  --mn-red:#C6002B  --mn-white:#FFFFFF
 *          --mn-bg:#EEF0F4    --mn-border:#D4D9E1  --mn-text:#1A1F2E
 * ═══════════════════════════════════════════════════════════════════════
 */

/* ── Global reset ─────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', system-ui, sans-serif;
}
.stApp { background: #EEF0F4; }
.main .block-container { padding: 0 1.8rem 2.5rem; max-width: 100%; }

/* ── Sidebar — deep navy ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #002654 !important;
    border-right: none;
}
[data-testid="stSidebar"] > div:first-child { padding: 0; }

/* Sidebar text cascade */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
    color: rgba(255,255,255,0.82) !important;
    font-size: 0.82rem;
}
/* Sidebar radio */
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
    color: rgba(255,255,255,0.65) !important;
    font-size: 0.8rem; letter-spacing: 0.02em;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) {
    color: #FFFFFF !important; font-weight: 600;
}
/* Sidebar selectbox */
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.09) !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    color: #FFFFFF !important; border-radius: 0;
}
/* Sidebar labels */
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
[data-testid="stSidebar"] [data-testid="stTextArea"] label {
    color: rgba(255,255,255,0.5) !important;
    font-size: 0.68rem !important; letter-spacing: 0.1em; text-transform: uppercase;
}
/* Sidebar textarea */
[data-testid="stSidebar"] textarea {
    background: rgba(255,255,255,0.09) !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    color: #FFFFFF !important; border-radius: 0 !important; font-size: 0.82rem !important;
}
[data-testid="stSidebar"] textarea::placeholder { color: rgba(255,255,255,0.35) !important; }
/* Sidebar file uploader */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px dashed rgba(255,255,255,0.28) !important; border-radius: 0;
}
/* Sidebar dividers */
[data-testid="stSidebar"] hr {
    border: none; border-top: 1px solid rgba(255,255,255,0.12) !important; margin: 0.65rem 0;
}
/* Sidebar alerts */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: rgba(198,0,43,0.18) !important;
    border-color: #C6002B !important; color: #FFFFFF !important; border-radius: 0;
}
/* Sidebar section-header overrides dark bg */
[data-testid="stSidebar"] .section-header {
    color: rgba(255,255,255,0.42) !important;
    border-bottom-color: rgba(255,255,255,0.14) !important;
}

/* ── Global divider ───────────────────────────────────────────────────── */
hr { border: none; border-top: 1px solid #D4D9E1; margin: 0.7rem 0; }

/* ── Buttons ──────────────────────────────────────────────────────────── */
.stButton > button {
    background: #002654; color: #FFFFFF;
    border: 1px solid #002654; border-radius: 0;
    text-transform: uppercase; letter-spacing: 0.09em;
    font-size: 0.72rem; font-weight: 700; padding: 0.55rem 1.2rem;
    width: 100%; transition: background 0.12s;
}
.stButton > button:hover { background: #003580; border-color: #003580; }
/* Primary button — French red */
[data-testid="baseButton-primary"] {
    background: #C6002B !important; border-color: #C6002B !important; color: #FFFFFF !important;
}
[data-testid="baseButton-primary"]:hover {
    background: #A0002B !important; border-color: #A0002B !important;
}

/* ── Typography ───────────────────────────────────────────────────────── */
h1 { color: #002654 !important; font-size: 1rem !important;
     text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; }
h2 { color: #002654 !important; font-size: 0.75rem !important;
     text-transform: uppercase; letter-spacing: 0.12em; font-weight: 700;
     border-bottom: 1px solid #D4D9E1; padding-bottom: 0.35rem; }
p, li, .stMarkdown { color: #374151; font-size: 0.85rem; }

/* ── Expanders ────────────────────────────────────────────────────────── */
[data-testid="stExpander"] > details > summary {
    background: #FFFFFF; border: 1px solid #D4D9E1; border-left: 3px solid #002654;
    border-radius: 0; padding: 0.55rem 0.9rem;
    font-size: 0.8rem; letter-spacing: 0.03em; color: #1A1F2E; font-weight: 500;
}
[data-testid="stExpander"] > details[open] > summary {
    border-left-color: #C6002B; color: #002654; font-weight: 600;
}
[data-testid="stExpander"] > details > div {
    background: #F8F9FB; border: 1px solid #D4D9E1;
    border-top: none; border-radius: 0; padding: 0.8rem;
}

/* ── Dataframes ───────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border: 1px solid #D4D9E1; border-radius: 0; }

/* ── Alerts ───────────────────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 0; font-size: 0.82rem; }

/* ── Tabs ─────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
    font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: #6B7280; border-radius: 0; padding: 0.4rem 1.1rem;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #002654; border-bottom: 2px solid #C6002B; font-weight: 700;
}

/* ── Custom components ────────────────────────────────────────────────── */

/* Topbar: full-width navy header with tricolor stripe */
.mn-topbar {
    background: #002654;
    margin: 0 -1.8rem 1.6rem;
    padding: 0;
}
.mn-topbar-stripe {
    height: 5px;
    background: linear-gradient(to right, #002654 33.3%, #FFFFFF 33.3% 66.6%, #C6002B 66.6%);
}
.mn-topbar-body {
    padding: 0.9rem 1.8rem;
    display: flex; align-items: center; justify-content: space-between;
}
.mn-topbar-brand { display: flex; align-items: center; gap: 1.1rem; }
.mn-topbar-emblem {
    width: 44px; height: 44px; flex-shrink: 0;
    border: 1px solid rgba(255,255,255,0.3);
    display: flex; align-items: center; justify-content: center;
}
.mn-topbar-rf {
    font-size: 0.5rem; letter-spacing: 0.25em;
    color: rgba(255,255,255,0.45); text-transform: uppercase; font-weight: 500;
}
.mn-topbar-org {
    font-size: 0.62rem; letter-spacing: 0.14em;
    color: rgba(255,255,255,0.75); text-transform: uppercase; font-weight: 600;
    margin-top: 2px;
}
.mn-topbar-title {
    font-size: 1.05rem; color: #FFFFFF;
    font-weight: 700; letter-spacing: 0.03em; margin-top: 3px;
}
.mn-topbar-meta { text-align: right; }
.mn-topbar-version {
    font-size: 0.58rem; color: rgba(255,255,255,0.4);
    letter-spacing: 0.12em; text-transform: uppercase;
}
.mn-topbar-status {
    font-size: 0.62rem; color: rgba(255,255,255,0.65);
    letter-spacing: 0.1em; text-transform: uppercase; margin-top: 3px;
}
.mn-status-dot {
    display: inline-block; width: 7px; height: 7px;
    background: #22C55E; border-radius: 50%; margin-right: 5px;
}

/* Sidebar brand block */
.mn-sidebar-brand {
    background: rgba(0,0,0,0.18);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding: 0;
    margin-bottom: 0.2rem;
}
.mn-sidebar-stripe {
    height: 3px;
    background: linear-gradient(to right, #002654 33.3%, #FFFFFF 33.3% 66.6%, #C6002B 66.6%);
}
.mn-sidebar-inner { padding: 0.9rem 1.2rem 0.8rem; }
.mn-sidebar-rf {
    font-size: 0.5rem; letter-spacing: 0.22em;
    color: rgba(255,255,255,0.38); text-transform: uppercase; font-weight: 500;
}
.mn-sidebar-name {
    font-size: 0.62rem; letter-spacing: 0.18em;
    color: rgba(255,255,255,0.65); text-transform: uppercase; font-weight: 600;
    margin-top: 2px;
}
.mn-sidebar-app {
    font-size: 1.35rem; color: #FFFFFF;
    font-weight: 700; letter-spacing: 0.1em; margin-top: 2px;
}
.mn-sidebar-tagline {
    font-size: 0.6rem; color: rgba(255,255,255,0.4);
    letter-spacing: 0.06em; margin-top: 1px;
}

/* Metric cards */
.op-card {
    background: #FFFFFF;
    border: 1px solid #D4D9E1;
    border-top: 3px solid #002654;
    padding: 1.1rem 1rem 0.85rem;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,38,84,0.07);
}
.op-card-value {
    font-size: 2.4rem; font-weight: 700;
    color: #002654; line-height: 1.1;
}
.op-card-unit { font-size: 0.65em; color: #6B7280; }
.op-card-label {
    font-size: 0.58rem; letter-spacing: 0.16em; text-transform: uppercase;
    color: #6B7280; margin-top: 0.38rem; font-weight: 500;
}
.op-card-badge { margin-top: 0.45rem; }

/* Section headers */
.section-header {
    font-size: 0.65rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: #002654; font-weight: 700;
    border-bottom: 2px solid #002654;
    padding-bottom: 0.32rem; margin-bottom: 0.75rem;
}

/* Info rows */
.info-row { font-size: 0.82rem; color: #4B5563; line-height: 1.8; }
.info-row b { color: #002654; font-weight: 600; }
.info-row code {
    font-size: 0.78rem; background: #EEF0F4; color: #002654;
    padding: 1px 5px; border-radius: 2px;
}

/* Action items */
.action-item {
    background: #F5F7FA;
    border-left: 3px solid #002654;
    padding: 0.55rem 0.85rem;
    margin-bottom: 0.4rem;
    font-size: 0.82rem; color: #1A1F2E; line-height: 1.6;
}
.action-number {
    font-size: 0.6rem; color: #6B7280;
    letter-spacing: 0.12em; text-transform: uppercase;
    font-weight: 600; display: block; margin-bottom: 2px;
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
        label="",
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
        chosen = st.selectbox("", event_options, label_visibility="collapsed")
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
                <svg width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="11" y="0" width="4" height="4" fill="white" opacity="0.85"/>
                    <rect x="0" y="11" width="26" height="4" fill="white" opacity="0.55"/>
                    <rect x="11" y="4" width="4" height="18" fill="white" opacity="0.85"/>
                    <circle cx="13" cy="8" r="3.5" fill="none" stroke="white" stroke-width="1.4" opacity="0.7"/>
                    <circle cx="3" cy="15" r="2.5" fill="none" stroke="white" stroke-width="1.2" opacity="0.6"/>
                    <circle cx="23" cy="15" r="2.5" fill="none" stroke="white" stroke-width="1.2" opacity="0.6"/>
                </svg>
            </div>
            <div>
                <div class="mn-topbar-rf">République Française</div>
                <div class="mn-topbar-org">Marine Nationale &nbsp;·&nbsp; Commandement Cyber</div>
                <div class="mn-topbar-title">MICA — Analyse d'Impact Cyber Maritime</div>
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
        '<div style="padding:2rem 0; color:#6B7280; font-size:0.85rem; '
        'border-left:3px solid #D4D9E1; padding-left:1rem; margin-top:0.5rem;">'
        'Sélectionnez ou décrivez un événement dans le panneau latéral,<br>'
        'puis cliquez sur <strong style="color:#C6002B;">LANCER L\'ANALYSE</strong>.'
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
