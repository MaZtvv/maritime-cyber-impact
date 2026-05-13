# Claude Prompt - Cyber Operational Impact Algorithm Roadmap

<role>
You are a senior cyber risk product architect, graph algorithm designer, and Streamlit engineering lead.

You are helping a hackathon team build a product for maritime/logistics cyber impact analysis. The product must estimate the operational business impact of a user-entered cyber/IT event by combining event severity, expert rankings, impacted IT/OT assets, business processes, geographic locations, dependency paths, and probability of propagation.
</role>

<context>
You have access to the current project files and the active notebook:

- `SujetsHackathon2026/Sujet2/Généralisation/frst_part.ipynb`
- `SujetsHackathon2026/Sujet2/Généralisation/nodes_events_final.csv`
- `SujetsHackathon2026/Sujet2/Généralisation/nodes_assets_it_maritime_10000.csv`
- `SujetsHackathon2026/Sujet2/Généralisation/nodes_attacks_final.csv`
- `SujetsHackathon2026/Sujet2/Généralisation/processes_final.csv`
- `SujetsHackathon2026/Sujet2/Généralisation/rels_dependencies_final.csv`
- `SujetsHackathon2026/Sujet2/Généralisation/rels_targets_final.csv`
- `SujetsHackathon2026/Sujet2/Généralisation/rels_generated_final.csv`

The project goal is to create a Streamlit application where a user enters or selects an event, and the system outputs:

1. The estimated operational impact.
2. The business processes affected.
3. The severity level by affected business process.
4. The path of propagation through assets and business processes.
5. The probability that each business process is actually affected.
6. The geographic zones/countries/cities likely impacted, based on the affected assets in `nodes_assets_it_maritime_10000.csv`.
7. A prioritized action list: which problems to handle first, based on operational impact.
</context>

<available_data_model>
The dataset contains the following entities and relations:

1. Events: `nodes_events_final.csv`
   - Important columns: `id`, `name`, `type`, `severity`, `description`, `source`, `related_assets`, `related_attacks`.
   - Event types include:
     - `Panne Système`
     - `Attaque Détectée`
     - `Incident`
     - `Alerte`
     - `Maintenance`

2. Assets: `nodes_assets_it_maritime_10000.csv`
   - Important columns: `id`, `name`, `type`, `location`, `criticality`, `owner`, `description`, `ip_address`, `os`, `software`, `processes`, `dependencies`.
   - This file should be used to infer which geographic locations and business processes are affected by an event.

3. Attacks: `nodes_attacks_final.csv`
   - Important columns: `id`, `name`, `type`, `tactics`, `description`, `severity`, `cvss_score`, `cvss_vector`.
   - CVSS score and vector should be used to increase the impact score when a related attack has strong technical severity.

4. Business processes: `processes_final.csv`
   - Contains the list of business processes / métiers.

5. Dependencies: `rels_dependencies_final.csv`
   - Important columns: `source`, `target`, `weight`.
   - Represents dependencies between assets.
   - Use this to simulate cascade propagation.

6. Attack-to-asset relation: `rels_targets_final.csv`
   - Important columns: `source`, `target`, `impact_score`.
   - Represents which attacks target which assets.

7. Attack-to-event relation: `rels_generated_final.csv`
   - Important columns: `source`, `target`, `probability`.
   - Represents which attacks generate which events.
</available_data_model>

<expert_rankings>
The cyber experts gave the following event type danger ranking, from most dangerous to least dangerous:

1. `Panne Système`
2. `Attaque Détectée`
3. `Incident`
4. `Alerte`
5. `Maintenance`

Use this expert ranking as a core prior in the impact model.

The event description ranking currently proposed in the notebook is:

1. `Panne système: Réseau indisponible.`
2. `Panne système: Base de données inaccessible.`
3. `Panne système: Serveur hors ligne.`
4. `Attaque détectée: Tentative de ZeroLogon.`
5. `Attaque détectée: Exploitation de Log4Shell.`
6. `Attaque détectée: Attaque par force brute.`
7. `Incident détecté: Exécution de commande suspecte.`
8. `Incident détecté: Accès non autorisé.`
9. `Incident détecté: Trafic réseau anormal.`
10. `Alerte générée: Requête SQL suspecte.`
11. `Alerte générée: Tentative de brute-force.`
12. `Alerte générée: Scan de port.`
13. `Maintenance planifiée: Redémarrage du réseau.`
14. `Maintenance planifiée: Mise à jour du serveur.`
15. `Maintenance planifiée: Sauvegarde des données.`

The business process ranking currently proposed in the notebook is:

1. `Gestion des Flottes`
2. `Planification des Itinéraires`
3. `Suivi des Cargaisons`
4. `Sécurité et Conformité`
5. `Douanes et Réglementations`
6. `Gestion des Équipages`
7. `Maintenance des Navires`
8. `Gestion des Stocks`
9. `Approvisionnement`
10. `Gestion des Réservations`
11. `Gestion des Clients`
12. `Finance et Comptabilité`
13. `Analyse des Risques`
14. `Communication Interne`
15. `Ressources Humaines`

You may refine these rankings if the data clearly suggests it, but you must explain every change and preserve the expert logic unless there is a strong reason not to.
</expert_rankings>

<task>
Create a complete technical roadmap and implementation plan to develop the product algorithm and Streamlit app.

The roadmap must be practical enough that a developer can implement it directly in the current repository.

Think through the problem step by step before proposing the final architecture.
</task>

<algorithm_requirements>
Design an algorithm that supports the following flow:

1. User input:
   - The user selects an existing event from `nodes_events_final.csv`, or enters a new event manually.
   - If the event is new, the system should classify it into the closest known event type and description category.

2. Initial severity:
   - Map the event type and description to an expert severity score.
   - Include event `severity` if available.
   - Include attack severity, `cvss_score`, and `cvss_vector` when the event is linked to an attack.

3. Directly affected assets:
   - Use `related_assets` from the event when available.
   - Use `rels_generated_final.csv` and `rels_targets_final.csv` when the event is linked to an attack.
   - Use asset criticality from `nodes_assets_it_maritime_10000.csv`.

4. Propagation:
   - Use `rels_dependencies_final.csv` and/or the `dependencies` column in the assets CSV.
   - Build a graph of assets.
   - Propagate impact from directly affected assets to dependent assets.
   - Each dependency should have a probability/weight decay.
   - The algorithm should keep track of propagation paths, not only final scores.

5. Business process impact:
   - Map affected assets to business processes using the `processes` column.
   - Aggregate asset-level impact into process-level impact.
   - Combine:
     - expert process criticality,
     - number of affected assets,
     - asset criticality,
     - event severity,
     - propagation probability,
     - attack/CVSS severity if relevant.

6. Geographic impact:
   - Use the `location` column from affected assets.
   - Output impacted cities/countries/regions.
   - Aggregate severity by location.

7. Prioritized response:
   - Output an ordered list of business processes and assets to handle first.
   - The ordering should be based on operational impact, not only technical severity.

8. Explainability:
   - For each impacted business process, show:
     - why it is impacted,
     - which assets caused the impact,
     - the propagation path,
     - the probability of real impact,
     - the severity level,
     - recommended mitigation priority.
</algorithm_requirements>

<expected_outputs>
Your final answer must include:

1. Product vision in one paragraph.
2. Data model overview.
3. Proposed scoring formula.
4. Propagation algorithm design.
5. Business process impact algorithm.
6. Geographic impact algorithm.
7. Streamlit UI structure.
8. File-by-file implementation roadmap.
9. Pseudocode for the core algorithm.
10. Recommended Python libraries.
11. Validation strategy.
12. Risks and assumptions.
13. A first implementation plan split into milestones.
</expected_outputs>

<streamlit_requirements>
The final Streamlit app should contain:

1. Event selection/input panel.
2. Event classification and severity panel.
3. Impact summary cards:
   - global operational severity,
   - number of affected assets,
   - number of affected business processes,
   - number of affected locations.
4. Prioritized business process impact table.
5. Affected asset table.
6. Propagation path viewer.
7. Impact map or location summary table.
8. Recommendations / action priority list.
9. Explanation panel for why the algorithm produced each score.
</streamlit_requirements>

<scoring_guidance>
Propose a scoring model that is simple enough for a hackathon but credible enough for cyber experts.

A possible structure:

`operational_impact_score = event_score * asset_criticality_factor * process_criticality_factor * propagation_probability * attack_factor`

But refine it if needed.

The score should be normalized to a readable scale, for example:

- `0-20`: Low
- `21-40`: Moderate
- `41-60`: Significant
- `61-80`: High
- `81-100`: Critical

Make sure the model can explain why a process is classified as `Critical`, `High`, etc.
</scoring_guidance>

<implementation_constraints>
Use Python and Streamlit.

Prefer simple, readable, hackathon-friendly implementation.

Suggested libraries:

- `pandas` for data handling.
- `networkx` for graph propagation.
- `streamlit` for the app.
- `plotly` for charts/maps if needed.
- `rapidfuzz` or `sklearn` TF-IDF for matching a new event to known descriptions.

Do not propose a heavy machine learning system unless it clearly improves the product within a hackathon timeframe.

The first version should work deterministically with transparent scoring.
</implementation_constraints>

<reasoning_instructions>
Think through the solution step by step.

First analyze the data relationships.
Then design the algorithm.
Then design the Streamlit user experience.
Then produce the implementation roadmap.

Be explicit about assumptions.
When a data relationship is ambiguous, propose a pragmatic fallback.
</reasoning_instructions>

<answer_style>
Write the answer in English.

Be structured and implementation-oriented.

Use headings, tables, formulas, and pseudocode where useful.

Avoid vague strategy. Give concrete steps a developer can follow.
</answer_style>

