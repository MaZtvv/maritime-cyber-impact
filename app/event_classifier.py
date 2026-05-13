"""Expert scoring tables and event classification via fuzzy matching."""

from rapidfuzz import process as fuzz_process, fuzz

# ---------------------------------------------------------------------------
# Expert rankings (from notebook + domain knowledge)
# ---------------------------------------------------------------------------

TYPE_SCORES: dict[str, float] = {
    "panne système": 100.0,
    "attaque détectée": 80.0,
    "incident": 60.0,
    "alerte": 40.0,
    "maintenance": 20.0,
}

DESCRIPTION_SCORES: dict[str, float] = {
    "panne système: réseau indisponible.": 100.0,
    "panne système: base de données inaccessible.": 93.0,
    "panne système: serveur hors ligne.": 87.0,
    "attaque détectée: tentative de zerologon.": 80.0,
    "attaque détectée: exploitation de log4shell.": 73.0,
    "attaque détectée: attaque par force brute.": 67.0,
    "incident détecté: exécution de commande suspecte.": 60.0,
    "incident détecté: accès non autorisé.": 53.0,
    "incident détecté: trafic réseau anormal.": 47.0,
    "alerte générée: requête sql suspecte.": 40.0,
    "alerte générée: tentative de brute-force.": 33.0,
    "alerte générée: scan de port.": 27.0,
    "maintenance planifiée: redémarrage du réseau.": 20.0,
    "maintenance planifiée: mise à jour du serveur.": 13.0,
    "maintenance planifiée: sauvegarde des données.": 10.0,
}

SEVERITY_MAP: dict[str, float] = {
    "critical": 100.0,
    "high": 70.0,
    "medium": 40.0,
    "low": 20.0,
}

PROCESS_CRITICALITY: dict[str, float] = {
    "Gestion des Flottes": 100.0,
    "Planification des Itinéraires": 93.0,
    "Suivi des Cargaisons": 87.0,
    "Sécurité et Conformité": 80.0,
    "Douanes et Réglementations": 73.0,
    "Gestion des Équipages": 67.0,
    "Maintenance des Navires": 60.0,
    "Gestion des Stocks": 53.0,
    "Approvisionnement": 47.0,
    "Gestion des Réservations": 40.0,
    "Gestion des Clients": 35.0,
    "Finance et Comptabilité": 30.0,
    "Analyse des Risques": 28.0,
    "Communication Interne": 26.0,
    "Ressources Humaines": 25.0,
}

ASSET_CRIT_WEIGHT: dict[str, float] = {
    "critical": 5.0,
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

_KNOWN_DESCRIPTIONS = list(DESCRIPTION_SCORES.keys())

# Description → inferred event type
_DESC_TO_TYPE: dict[str, str] = {
    "panne système: réseau indisponible.": "Panne Système",
    "panne système: base de données inaccessible.": "Panne Système",
    "panne système: serveur hors ligne.": "Panne Système",
    "attaque détectée: tentative de zerologon.": "Attaque Détectée",
    "attaque détectée: exploitation de log4shell.": "Attaque Détectée",
    "attaque détectée: attaque par force brute.": "Attaque Détectée",
    "incident détecté: exécution de commande suspecte.": "Incident",
    "incident détecté: accès non autorisé.": "Incident",
    "incident détecté: trafic réseau anormal.": "Incident",
    "alerte générée: requête sql suspecte.": "Alerte",
    "alerte générée: tentative de brute-force.": "Alerte",
    "alerte générée: scan de port.": "Alerte",
    "maintenance planifiée: redémarrage du réseau.": "Maintenance",
    "maintenance planifiée: mise à jour du serveur.": "Maintenance",
    "maintenance planifiée: sauvegarde des données.": "Maintenance",
}


def classify_event(user_text: str) -> dict:
    """Match free-text to the nearest known description.

    Returns a dict with keys: matched_description, event_type, desc_score, confidence.
    """
    normalised = user_text.strip().lower()
    result = fuzz_process.extractOne(
        normalised,
        _KNOWN_DESCRIPTIONS,
        scorer=fuzz.WRatio,
    )
    if result is None:
        return {
            "matched_description": _KNOWN_DESCRIPTIONS[0],
            "event_type": "Panne Système",
            "desc_score": DESCRIPTION_SCORES[_KNOWN_DESCRIPTIONS[0]],
            "confidence": 0.0,
        }
    matched, confidence, _ = result
    return {
        "matched_description": matched,
        "event_type": _DESC_TO_TYPE.get(matched, "Incident"),
        "desc_score": DESCRIPTION_SCORES[matched],
        "confidence": confidence,
    }


def compute_event_base_score(
    event_type: str,
    description: str,
    severity: str,
    max_cvss: float = 5.0,
) -> float:
    """Combine type rank, description rank, severity, and CVSS into a 0-100 base score."""
    type_score = TYPE_SCORES.get(event_type.strip().lower(), 40.0)
    desc_score = DESCRIPTION_SCORES.get(description.strip().lower(), 40.0)
    sev_score = SEVERITY_MAP.get(str(severity).strip().lower(), 40.0)
    attack_factor = min(1.0, max_cvss / 10.0)

    base = (
        0.35 * type_score
        + 0.25 * desc_score
        + 0.25 * sev_score
        + 0.15 * (attack_factor * 100.0)
    )
    return round(min(100.0, max(0.0, base)), 2)
