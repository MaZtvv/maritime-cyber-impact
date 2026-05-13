# Maritime Cyber Impact Analyser

A Streamlit dashboard that estimates the **operational business impact** of a cyber/IT event on maritime logistics infrastructure.

Given a security event (selected from a catalog or entered as free text), the app computes:
- Global operational impact score (0–100, labelled Low → Critical)
- Which business processes are affected and how severely
- Which IT assets are directly hit or cascade-impacted through dependency chains
- Which geographic locations (ports, cities) are at risk
- A prioritised remediation action list
- A full explanation of every score

---

## Demo

```
Event: Panne système — réseau indisponible (critical)
→ Global impact: 81 / 100  [Critical]
→ 44 assets affected across 3 propagation hops
→ Top process: Gestion des Flottes (100/100)
→ 21 locations impacted (Singapore, Rotterdam, Le Havre …)
```

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# 2. Install dependencies (Python 3.9+)
pip install -r requirements.txt

# 3. Launch
streamlit run app/main.py
```

Open `http://localhost:8501` in your browser.

---

## Project structure

```
.
├── app/
│   ├── main.py              # Streamlit entry point
│   ├── data_loader.py       # CSV loading + NetworkX dependency graph
│   ├── event_classifier.py  # Expert scoring tables + rapidfuzz event matcher
│   ├── impact_engine.py     # BFS propagation algorithm + process aggregation
│   ├── geo_analyzer.py      # Geographic impact aggregation
│   └── visualizer.py        # Plotly charts (network graph, geo map, bar chart)
├── nodes_events_final.csv              # 2 000 security events
├── nodes_assets_it_maritime_10000.csv  # 10 000 IT/OT maritime assets
├── nodes_attacks_final.csv             # 1 000 CVEs and MITRE ATT&CK TTPs
├── processes_final.csv                 # 15 maritime business processes
├── rels_dependencies_final.csv         # 20 000 asset dependency edges
├── rels_targets_final.csv              # 3 000 attack → asset relations
├── rels_generated_final.csv            # 2 000 attack → event relations
├── frst_part.ipynb                     # Exploratory data analysis notebook
└── requirements.txt
```

---

## How the algorithm works

### 1 — Event base score (0–100)

```
event_base = 0.35 × type_rank + 0.25 × description_rank
           + 0.25 × severity_rank + 0.15 × (CVSS / 10 × 100)
```

Expert type ranks: `Panne Système` (100) > `Attaque Détectée` (80) > `Incident` (60) > `Alerte` (40) > `Maintenance` (20).

### 2 — Asset impact propagation (BFS, max 3 hops)

```
propagated_impact = direct_impact × ∏(edge_weights) × 0.85^hop
```

The dependency graph is traversed in reverse: when an asset fails, every asset that depends on it is hit with a decayed impact score.

### 3 — Process impact score (0–100)

```
process_impact = 0.7 × expert_process_rank + 0.3 × normalised_asset_exposure
```

Expert process ranks from maritime domain knowledge: `Gestion des Flottes` (100) … `Ressources Humaines` (25).

### 4 — Global impact

```
global = max(process_impacts) × 0.6 + mean(process_impacts) × 0.4
```

### Severity labels

| Score | Label |
|---|---|
| 0–20 | Low |
| 21–40 | Moderate |
| 41–60 | Significant |
| 61–80 | High |
| 81–100 | Critical |

---

## Dependencies

| Library | Use |
|---|---|
| `streamlit` | Web UI |
| `pandas` | Data loading and manipulation |
| `networkx` | Dependency graph + BFS propagation |
| `plotly` | Network graph, geo map, bar charts |
| `rapidfuzz` | Fuzzy matching for free-text event input |

---

## Data model

```
Attack ──GENERATES──► Event (probability)
Attack ──TARGETS───► Asset (impact_score)
Asset  ──DEPENDS_ON► Asset (weight: 0.5 / 0.8 / 1.0)
Asset  ──supports──► Business Process (via processes column)
```

All data is synthetic and representative of maritime port IT/OT infrastructure.

---

## Built for

Hackathon Albert 2026 — Sujet 2: Cyber Impact Cartography for the Maritime Industry.
