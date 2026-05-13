"""Batch event parsing (CSV + STIX 2.x JSON) and operational priority ranking."""

import io
import json
import re
from collections import defaultdict

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_CSV_COLS = {"event_type", "severity", "description"}

EVENT_TYPE_MAP = {
    "panne": "Panne Système",
    "panne système": "Panne Système",
    "panne systeme": "Panne Système",
    "system failure": "Panne Système",
    "outage": "Panne Système",
    "attaque": "Attaque Détectée",
    "attaque détectée": "Attaque Détectée",
    "attaque detectee": "Attaque Détectée",
    "attack": "Attaque Détectée",
    "attack detected": "Attaque Détectée",
    "incident": "Incident",
    "alerte": "Alerte",
    "alert": "Alerte",
    "maintenance": "Maintenance",
}

STIX_SUPPORTED_TYPES = {
    "indicator",
    "malware",
    "intrusion-set",
    "attack-pattern",
    "observed-data",
    "vulnerability",
}

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

def parse_uploaded_csv_events(file_bytes: bytes) -> tuple[list, list[str]]:
    """Parse a CSV upload into a list of normalized pd.Series event records.

    Returns (records, errors). errors is empty on full success.
    """
    errors = []
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    except Exception as exc:
        return [], [f"CSV lecture impossible : {exc}"]

    missing = REQUIRED_CSV_COLS - set(df.columns)
    if missing:
        errors.append(
            f"Colonnes requises manquantes : {', '.join(sorted(missing))}. "
            f"Colonnes trouvées : {', '.join(df.columns.tolist())}."
        )
        return [], errors

    records = []
    for i, row in df.iterrows():
        records.append(normalize_event_record({
            "event_id": row.get("event_id", f"upload-{i + 1}"),
            "event_type": row.get("event_type", "Incident"),
            "severity": row.get("severity", "medium"),
            "description": row.get("description", ""),
            "source": row.get("source", "upload"),
            "timestamp": row.get("timestamp", ""),
            "related_assets": row.get("affected_asset_id", ""),
            "related_attacks": row.get("attack_id", ""),
            "cvss_score": row.get("cvss_score", ""),
        }))

    return records, errors


# ---------------------------------------------------------------------------
# STIX 2.x parsing
# ---------------------------------------------------------------------------

def parse_uploaded_stix_events(file_bytes: bytes) -> tuple[list, list[str]]:
    """Parse a STIX 2.x JSON bundle into normalized event records.

    Supports: indicator, malware, intrusion-set, attack-pattern, observed-data, vulnerability.
    """
    errors = []
    try:
        payload = json.loads(file_bytes.decode("utf-8"))
    except Exception as exc:
        return [], [f"JSON invalide : {exc}"]

    if not isinstance(payload, dict):
        return [], ["Format STIX invalide : la racine doit être un objet JSON."]

    # Accept both a bare object and a bundle with objects[]
    if payload.get("type") == "bundle":
        objects = payload.get("objects", [])
    elif payload.get("type") in STIX_SUPPORTED_TYPES:
        objects = [payload]
    else:
        objects = payload.get("objects", [payload])

    records = []
    skipped = 0
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") not in STIX_SUPPORTED_TYPES:
            skipped += 1
            continue
        raw = _stix_object_to_raw(obj)
        if raw:
            records.append(normalize_event_record(raw))

    if not records:
        errors.append(
            f"Aucun objet STIX exploitable trouvé "
            f"(types supportés : {', '.join(sorted(STIX_SUPPORTED_TYPES))}). "
            f"{skipped} objet(s) ignoré(s)."
        )

    return records, errors


def _stix_object_to_raw(obj: dict) -> dict | None:
    obj_type = obj.get("type", "")
    name = obj.get("name", obj.get("id", "unknown"))
    description_raw = obj.get("description", name)

    # Extract external references (MITRE ID, CVE, CVSS)
    attack_id = ""
    cvss_score = ""
    for ref in obj.get("external_references", []):
        src = ref.get("source_name", "")
        if src in ("mitre-attack", "mitre-mobile-attack", "mitre-ics-attack"):
            attack_id = ref.get("external_id", attack_id)
        if src == "cve":
            attack_id = ref.get("external_id", attack_id)
        desc_ref = str(ref.get("description", ""))
        if "cvss" in desc_ref.lower():
            m = re.search(r"(\d+\.\d+)", desc_ref)
            if m:
                cvss_score = m.group(1)

    # Also check common CVSS extension fields
    for key in ("x_cvss_v3_score", "cvss_v3_score", "base_score"):
        if obj.get(key):
            cvss_score = str(obj[key])
            break

    if obj_type == "vulnerability":
        event_type = "Attaque Détectée"
        severity = _cvss_to_severity(cvss_score)
        description = f"Vulnérabilité : {name}. {description_raw}"
    elif obj_type == "attack-pattern":
        event_type = "Attaque Détectée"
        severity = "high"
        description = f"Technique d'attaque : {name}. {description_raw}"
    elif obj_type == "malware":
        event_type = "Attaque Détectée"
        severity = "high"
        description = f"Malware détecté : {name}. {description_raw}"
    elif obj_type == "intrusion-set":
        event_type = "Attaque Détectée"
        severity = "critical"
        description = f"Groupe d'intrusion : {name}. {description_raw}"
    elif obj_type == "indicator":
        event_type = "Alerte"
        severity = "medium"
        description = f"Indicateur : {name}. Motif : {obj.get('pattern', 'N/A')}."
    elif obj_type == "observed-data":
        event_type = "Incident"
        severity = "medium"
        description = f"Données observées : {name}. {description_raw}"
    else:
        return None

    return {
        "event_id": obj.get("id", "stix-unknown"),
        "event_type": event_type,
        "severity": severity,
        "description": description,
        "source": "stix",
        "timestamp": obj.get("created", ""),
        "related_assets": "",
        "related_attacks": attack_id,
        "cvss_score": cvss_score,
    }


def _cvss_to_severity(cvss_str: str) -> str:
    try:
        score = float(cvss_str)
        if score >= 9.0:
            return "critical"
        if score >= 7.0:
            return "high"
        if score >= 4.0:
            return "medium"
        return "low"
    except (TypeError, ValueError):
        return "medium"


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_event_record(raw: dict) -> pd.Series:
    """Normalize any raw event dict into the pd.Series format expected by run_analysis."""
    from event_classifier import classify_event

    desc_input = str(raw.get("description", "") or raw.get("event_type", ""))
    classification = classify_event(desc_input)

    return pd.Series({
        "id": str(raw.get("event_id", "upload-unknown")).strip(),
        "name": str(raw.get("event_id", "Uploaded event")).strip(),
        "type": _normalize_event_type(str(raw.get("event_type", "Incident"))),
        "severity": str(raw.get("severity", "medium")).strip().lower(),
        "description": classification["matched_description"],
        "source": str(raw.get("source", "upload")).strip(),
        "related_assets": str(raw.get("related_assets", "") or ""),
        "related_attacks": str(raw.get("related_attacks", "") or ""),
        "cvss_override": str(raw.get("cvss_score", "") or "").strip(),
    })


def _normalize_event_type(raw: str) -> str:
    key = raw.strip().lower()
    for k, v in EVENT_TYPE_MAP.items():
        if k in key:
            return v
    return "Incident"


# ---------------------------------------------------------------------------
# Batch analysis
# ---------------------------------------------------------------------------

def analyze_batch_events(event_records: list, data: dict) -> list[dict]:
    """Run run_analysis on each event record and collect structured results."""
    from impact_engine import run_analysis

    results = []
    for record in event_records:
        try:
            result = run_analysis(record, data)
            top_proc = (
                result.process_impacts.iloc[0]["process"]
                if not result.process_impacts.empty else "—"
            )
            top_proc_score = (
                float(result.process_impacts.iloc[0]["impact_score"])
                if not result.process_impacts.empty else 0.0
            )
            results.append({
                "event_id": record["id"],
                "event_type": record["type"],
                "severity": record["severity"],
                "description": record["description"],
                "event_base_score": result.event_base_score,
                "global_impact": result.global_impact,
                "severity_label": result.severity_label,
                "asset_count": len(result.asset_impacts),
                "process_count": len(result.process_impacts),
                "top_process": top_proc,
                "top_process_score": top_proc_score,
                "linked_attacks": result.score_breakdown.get("linked_attacks", []),
                "top_actions": result.actions[:2],
                "_result": result,
                "error": None,
            })
        except Exception as exc:
            results.append({
                "event_id": record["id"],
                "event_type": record["type"],
                "severity": record["severity"],
                "description": record["description"],
                "event_base_score": 0.0,
                "global_impact": 0.0,
                "severity_label": "Unknown",
                "asset_count": 0,
                "process_count": 0,
                "top_process": "—",
                "top_process_score": 0.0,
                "linked_attacks": [],
                "top_actions": [],
                "_result": None,
                "error": str(exc),
            })

    return results


def rank_events_by_priority(results: list[dict]) -> pd.DataFrame:
    """Rank analyzed events by combined operational priority score."""
    df = pd.DataFrame([
        {k: v for k, v in r.items() if k != "_result"}
        for r in results
    ])
    if df.empty:
        return df

    df["_sev_rank"] = df["severity"].str.lower().map(SEVERITY_RANK).fillna(0)
    df["priority_score"] = (
        df["global_impact"] * 0.50
        + df["_sev_rank"] * 5.0
        + df["asset_count"].clip(upper=100) * 0.25
        + df["top_process_score"] * 0.20
    ).round(2)

    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    df = df.drop(columns=["_sev_rank"])

    return df
