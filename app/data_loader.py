"""Load all CSV data and build the NetworkX dependency graph."""

from pathlib import Path
from collections import defaultdict

import pandas as pd
import networkx as nx

DATA_DIR = Path(__file__).parent.parent


def _load_csvs() -> dict:
    files = {
        "events": "nodes_events_final.csv",
        "assets": "nodes_assets_it_maritime_10000.csv",
        "attacks": "nodes_attacks_final.csv",
        "processes": "processes_final.csv",
        "dependencies": "rels_dependencies_final.csv",
        "targets": "rels_targets_final.csv",
        "generated": "rels_generated_final.csv",
    }
    data = {}
    for key, fname in files.items():
        path = DATA_DIR / fname
        df = pd.read_csv(path, dtype=str)
        df.columns = df.columns.str.strip()
        data[key] = df
    return data


def _build_graph(deps_df: pd.DataFrame) -> nx.DiGraph:
    """Directed graph: source DEPENDS_ON target (edge weight = dependency strength)."""
    G = nx.DiGraph()
    for _, row in deps_df.iterrows():
        src = str(row["source"]).strip()
        tgt = str(row["target"]).strip()
        try:
            w = float(row["weight"])
        except (ValueError, KeyError):
            w = 0.5
        G.add_edge(src, tgt, weight=w)
    return G


def _build_attack_asset_map(targets_df: pd.DataFrame) -> dict:
    """attack_id -> list of (asset_id, impact_score)"""
    mapping = defaultdict(list)
    for _, row in targets_df.iterrows():
        atk = str(row["source"]).strip()
        asset = str(row["target"]).strip()
        try:
            score = float(row["impact_score"])
        except (ValueError, KeyError):
            score = 0.7
        mapping[atk].append((asset, score))
    return dict(mapping)


def _build_event_attack_map(generated_df: pd.DataFrame) -> dict:
    """event_id -> list of (attack_id, probability)"""
    mapping = defaultdict(list)
    for _, row in generated_df.iterrows():
        atk = str(row["source"]).strip()
        evt = str(row["target"]).strip()
        try:
            prob = float(row["probability"])
        except (ValueError, KeyError):
            prob = 0.6
        mapping[evt].append((atk, prob))
    return dict(mapping)


def _build_asset_index(assets_df: pd.DataFrame) -> dict:
    """asset_id -> row as dict for fast lookup."""
    return {str(row["id"]).strip(): row.to_dict() for _, row in assets_df.iterrows()}


def load_all_data() -> dict:
    raw = _load_csvs()

    assets_df = raw["assets"].copy()
    assets_df["criticality"] = assets_df["criticality"].str.strip().str.lower()
    assets_df["id"] = assets_df["id"].str.strip()

    attacks_df = raw["attacks"].copy()
    attacks_df["cvss_score"] = pd.to_numeric(attacks_df["cvss_score"], errors="coerce").fillna(5.0)

    return {
        "events": raw["events"],
        "assets": assets_df,
        "attacks": attacks_df,
        "processes": raw["processes"],
        "graph": _build_graph(raw["dependencies"]),
        "attack_asset_map": _build_attack_asset_map(raw["targets"]),
        "event_attack_map": _build_event_attack_map(raw["generated"]),
        "asset_index": _build_asset_index(assets_df),
        "targets_df": raw["targets"],
    }
