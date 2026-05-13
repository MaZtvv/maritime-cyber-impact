"""Core impact scoring, BFS propagation, and process/action aggregation."""

from collections import deque
from dataclasses import dataclass, field

import pandas as pd

from event_classifier import (
    ASSET_CRIT_WEIGHT,
    PROCESS_CRITICALITY,
    compute_event_base_score,
)

MAX_HOPS = 3
DECAY = 0.85
PRUNE_THRESHOLD = 0.03


def _parse_ids(raw) -> list[str]:
    """Parse comma-separated IDs, handling NaN / empty."""
    if not raw or pd.isna(raw):
        return []
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def _crit_weight(criticality: str) -> float:
    return ASSET_CRIT_WEIGHT.get(str(criticality).strip().lower(), 1.0)


@dataclass
class AnalysisResult:
    event_base_score: float
    global_impact: float
    severity_label: str
    process_impacts: pd.DataFrame         # columns: process, impact_score, severity, asset_count
    asset_impacts: pd.DataFrame           # columns: asset_id, name, type, criticality, impact, hop, location, processes
    propagation_paths: dict               # asset_id -> list[asset_id] (path from root)
    geo_impacts: pd.DataFrame             # columns: location, country, max_impact, asset_count, severity
    actions: list[dict]                   # prioritised action list
    score_breakdown: dict = field(default_factory=dict)


def score_to_label(score: float) -> str:
    if score <= 20:
        return "Low"
    if score <= 40:
        return "Moderate"
    if score <= 60:
        return "Significant"
    if score <= 80:
        return "High"
    return "Critical"


def run_analysis(event_row: pd.Series, data: dict) -> AnalysisResult:
    # ------------------------------------------------------------------ #
    # 1. Resolve linked attacks + compute event base score
    # ------------------------------------------------------------------ #
    attack_ids_from_event = _parse_ids(event_row.get("related_attacks", ""))
    event_attack_map = data.get("event_attack_map", {})
    attacks_from_graph = [atk for atk, _ in event_attack_map.get(str(event_row["id"]).strip(), [])]
    all_attack_ids = list(set(attack_ids_from_event + attacks_from_graph))

    attacks_df: pd.DataFrame = data["attacks"]
    linked_attacks = attacks_df[attacks_df["id"].isin(all_attack_ids)]
    max_cvss = float(linked_attacks["cvss_score"].max()) if len(linked_attacks) else 5.0

    event_base = compute_event_base_score(
        event_type=str(event_row.get("type", "Incident")),
        description=str(event_row.get("description", "")),
        severity=str(event_row.get("severity", "medium")),
        max_cvss=max_cvss,
    )

    # ------------------------------------------------------------------ #
    # 2. Directly affected assets
    # ------------------------------------------------------------------ #
    asset_index: dict = data["asset_index"]
    attack_asset_map: dict = data["attack_asset_map"]

    direct_from_event = _parse_ids(event_row.get("related_assets", ""))
    direct_from_attacks: list[tuple[str, float]] = []
    for atk_id in all_attack_ids:
        for asset_id, impact_score in attack_asset_map.get(atk_id, []):
            direct_from_attacks.append((asset_id, impact_score))

    # Raw asset impact is kept in 0-1 range; criticality weight is only applied
    # during process aggregation so that geo/asset scores remain bounded.
    direct_assets: dict[str, float] = {}
    for asset_id in direct_from_event:
        if asset_id in asset_index:
            direct_assets[asset_id] = max(
                direct_assets.get(asset_id, 0.0),
                event_base / 100.0,
            )
    for asset_id, impact_score in direct_from_attacks:
        if asset_id in asset_index:
            direct_assets[asset_id] = max(
                direct_assets.get(asset_id, 0.0),
                (event_base / 100.0) * float(impact_score),
            )

    # ------------------------------------------------------------------ #
    # 3. BFS propagation through the dependency graph
    # ------------------------------------------------------------------ #
    graph = data["graph"]
    all_impacts, all_paths, all_hops = _propagate(direct_assets, graph, asset_index)

    # ------------------------------------------------------------------ #
    # 4. Build asset impacts DataFrame
    # ------------------------------------------------------------------ #
    asset_rows = []
    for a_id, impact in all_impacts.items():
        info = asset_index.get(a_id, {})
        asset_rows.append({
            "asset_id": a_id,
            "name": info.get("name", a_id),
            "type": info.get("type", ""),
            "criticality": info.get("criticality", ""),
            "impact": round(impact * 100.0, 2),  # scale to 0-100
            "hop": all_hops.get(a_id, 0),
            "location": info.get("location", ""),
            "processes": info.get("processes", ""),
        })
    assets_df_out = pd.DataFrame(asset_rows).sort_values("impact", ascending=False)

    # ------------------------------------------------------------------ #
    # 5. Process impact aggregation
    # ------------------------------------------------------------------ #
    process_rows = _compute_process_impacts(all_impacts, asset_index)
    process_df = pd.DataFrame(process_rows).sort_values("impact_score", ascending=False)

    # ------------------------------------------------------------------ #
    # 6. Global score
    # ------------------------------------------------------------------ #
    if len(process_df):
        global_impact = round(
            process_df["impact_score"].max() * 0.6 + process_df["impact_score"].mean() * 0.4, 2
        )
    else:
        global_impact = round(event_base, 2)
    global_label = score_to_label(global_impact)

    # ------------------------------------------------------------------ #
    # 7. Actions
    # ------------------------------------------------------------------ #
    actions = _build_actions(process_df, assets_df_out, data.get("targets_df"))

    # ------------------------------------------------------------------ #
    # 8. Score breakdown for explanation panel
    # ------------------------------------------------------------------ #
    breakdown = {
        "event_type": str(event_row.get("type", "")),
        "event_severity": str(event_row.get("severity", "")),
        "description": str(event_row.get("description", "")),
        "max_cvss": max_cvss,
        "linked_attacks": list(all_attack_ids),
        "event_base_score": event_base,
        "direct_asset_count": len(direct_assets),
        "total_asset_count": len(all_impacts),
    }

    return AnalysisResult(
        event_base_score=event_base,
        global_impact=global_impact,
        severity_label=global_label,
        process_impacts=process_df,
        asset_impacts=assets_df_out,
        propagation_paths=all_paths,
        geo_impacts=pd.DataFrame(),  # filled by geo_analyzer
        actions=actions,
        score_breakdown=breakdown,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _propagate(
    direct_assets: dict[str, float],
    graph,
    asset_index: dict,
    max_hops: int = MAX_HOPS,
    decay: float = DECAY,
) -> tuple[dict, dict, dict]:
    """BFS over reversed edges: assets that DEPEND ON the failed asset are hit next."""
    visited: dict[str, float] = {}
    paths: dict[str, list] = {}
    hops: dict[str, int] = {}

    queue: deque = deque()
    for asset_id, impact in direct_assets.items():
        queue.append((asset_id, impact, [asset_id], 0))

    while queue:
        node, impact, path, hop = queue.popleft()

        if node in visited and visited[node] >= impact:
            continue
        visited[node] = impact
        paths[node] = path
        hops[node] = hop

        if hop >= max_hops:
            continue

        # predecessors = assets that depend on `node`
        if node not in graph:
            continue
        for neighbor in graph.predecessors(node):
            edge_data = graph[neighbor][node]
            edge_weight = float(edge_data.get("weight", 0.5))
            new_impact = impact * edge_weight * decay
            if new_impact < PRUNE_THRESHOLD:
                continue
            if neighbor not in visited or visited[neighbor] < new_impact:
                queue.append((neighbor, new_impact, path + [neighbor], hop + 1))

    return visited, paths, hops


def _compute_process_impacts(
    all_impacts: dict[str, float],
    asset_index: dict,
) -> list[dict]:
    from collections import defaultdict

    process_totals: dict[str, float] = defaultdict(float)
    process_asset_count: dict[str, int] = defaultdict(int)

    for asset_id, impact in all_impacts.items():
        info = asset_index.get(asset_id, {})
        raw_procs = info.get("processes", "")
        if not raw_procs or pd.isna(raw_procs):
            continue
        procs = [p.strip() for p in str(raw_procs).split(",") if p.strip()]
        cw = _crit_weight(info.get("criticality", "medium"))
        for proc in procs:
            process_totals[proc] += impact * cw
            process_asset_count[proc] += 1

    if not process_totals:
        return []

    max_raw = max(process_totals.values()) if process_totals else 1.0

    rows = []
    for proc, raw_total in process_totals.items():
        proc_crit = PROCESS_CRITICALITY.get(proc, 25.0)
        norm = min(100.0, (raw_total / max_raw) * 100.0)
        score = round(0.7 * proc_crit + 0.3 * norm, 2)
        rows.append({
            "process": proc,
            "impact_score": score,
            "severity": score_to_label(score),
            "asset_count": process_asset_count[proc],
            "process_criticality": proc_crit,
            "exposure_score": round(norm, 2),
        })

    return rows


def _build_actions(
    process_df: pd.DataFrame,
    assets_df: pd.DataFrame,
    targets_df,
) -> list[dict]:
    actions = []
    for _, proc_row in process_df.iterrows():
        proc_name = proc_row["process"]
        proc_assets = assets_df[
            assets_df["processes"].str.contains(proc_name, na=False, regex=False)
        ].head(3)

        mitigation = "Isoler les actifs concernés et appliquer les correctifs disponibles."
        if targets_df is not None and len(proc_assets):
            top_asset_id = proc_assets.iloc[0]["asset_id"]
            mask = targets_df["target"].str.strip() == top_asset_id
            if mask.any():
                mit_val = targets_df[mask].iloc[0].get("mitigation", "")
                if mit_val and not pd.isna(mit_val):
                    mitigation = str(mit_val)

        actions.append({
            "priority": len(actions) + 1,
            "process": proc_name,
            "impact_score": proc_row["impact_score"],
            "severity": proc_row["severity"],
            "top_assets": ", ".join(proc_assets["asset_id"].tolist()),
            "mitigation": mitigation,
        })

    return actions
