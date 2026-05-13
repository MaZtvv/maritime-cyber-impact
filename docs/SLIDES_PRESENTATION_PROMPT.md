# Claude Prompt - MICA Presentation Slides

<role>
You are a senior strategic product storyteller, cyber defense consultant, and presentation designer.

You are helping a hackathon team prepare a high-impact slide deck for a jury presentation about MICA: Maritime Impact Cyber Analysis.

Your audience includes:
- cyber experts,
- maritime/logistics decision-makers,
- technical jury members,
- non-technical stakeholders who need to understand operational value quickly.
</role>

<objective>
Create a complete presentation slide deck outline and slide-by-slide content for MICA.

The goal of the presentation is to clearly explain:
1. the operational problem,
2. why the problem matters in cyber defense,
3. how MICA solves it,
4. what data and algorithmic logic are used,
5. what the Streamlit prototype demonstrates,
6. what the business and operational value is,
7. what limitations exist today,
8. what improvements and future roadmap should be proposed.
</objective>

<project_context>
MICA stands for Maritime Impact Cyber Analysis.

It is a Streamlit-based cyber impact analysis dashboard designed for a maritime/logistics environment inspired by the French Navy / Marine Nationale context.

The product helps an analyst or operational decision-maker understand where to allocate time and resources after a cyber or IT event.

The core value proposition:

MICA reduces the time needed to understand and prioritize the operational impact of cyber events. Instead of manually investigating every asset, business process, and dependency, the tool estimates which business processes, assets, geographic zones, and operational functions are most at risk.

The system helps answer:
- What happened?
- Which assets are directly affected?
- Which assets may be affected through dependency propagation?
- Which business processes are impacted?
- Which geographic zones may be affected?
- What should be handled first?
- Why is this priority higher than another one?
</project_context>

<problem_statement>
The problem solved by MICA:

In a maritime/logistics cyber incident, analysts and decision-makers lose critical time identifying where to focus their effort. A single event can affect multiple assets, locations, business processes, and operational responsibilities.

Without a structured impact model, teams may:
- waste time investigating low-priority assets,
- miss propagation paths,
- underestimate operational consequences,
- allocate response resources poorly,
- fail to notify the correct operational owners quickly,
- react technically without understanding business impact.

MICA helps reduce research time and decision latency by showing an ordered list of what to investigate and treat first.

It can also help prevent propagation by identifying the chain of affected assets and dependent processes before the incident expands further.
</problem_statement>

<solution_summary>
MICA provides:

1. Event intake:
   - select an existing event,
   - write a free-text event description,
   - import multiple events through CSV,
   - import STIX-like cyber event data.

2. Event classification:
   - maps human-written descriptions to known cyber/IT event categories,
   - uses expert ranking of event types and descriptions,
   - supports severity levels and cyber attack indicators.

3. Operational impact scoring:
   - combines event severity,
   - expert ranking,
   - asset criticality,
   - process criticality,
   - dependency propagation,
   - attack severity and CVSS when available.

4. Propagation analysis:
   - uses asset dependencies to estimate cascade impact,
   - shows paths from the initial event to downstream affected assets and processes,
   - estimates probability / likelihood of real impact.

5. Business process prioritization:
   - ranks impacted business processes,
   - shows where teams should focus first,
   - explains why a process is considered critical.

6. Geographic impact:
   - uses asset location data to show which cities/countries/zones may be affected.

7. Action plan:
   - generates a prioritized response plan,
   - suggests which assets/processes to handle first.
</solution_summary>

<current_features>
The current Streamlit prototype includes:

- single-event analysis,
- free-text event classification,
- CSV event import,
- STIX-like JSON import,
- batch event analysis,
- global operational impact score,
- impacted assets table,
- impacted business process table,
- geographic impact visualization,
- dependency propagation graph,
- prioritized action recommendations,
- explanation panel showing score breakdown.
</current_features>

<expert_logic>
Cyber experts gave the following event type danger ranking, from most dangerous to least dangerous:

1. System outage / `Panne Système`
2. Detected attack / `Attaque Détectée`
3. Incident / `Incident`
4. Alert / `Alerte`
5. Maintenance / `Maintenance`

The reasoning:
- A system outage means operational disruption is already happening.
- A detected attack may become severe and propagate, but the operational impact still needs confirmation.
- An incident indicates suspicious or abnormal behavior that may be localized or still under investigation.
- An alert is an early warning signal, not always confirmed impact.
- Maintenance is usually planned and controlled, even if it can create temporary disruption.

Business process ranking should prioritize operational continuity, maritime/logistics mission impact, safety, compliance, and propagation risk.

Highest-priority processes include:
- Fleet Management,
- Route Planning,
- Cargo Tracking,
- Security and Compliance,
- Customs and Regulations,
- Crew Management,
- Ship Maintenance.
</expert_logic>

<data_limitations>
Mention current limitations honestly:

1. The dataset is synthetic.
2. There are only 5 event types and around 15 unique event descriptions.
3. Event descriptions are not precise enough to fully represent real-world cyber incidents.
4. Business process descriptions are too generic.
5. Asset ownership exists but operational contact emails are missing.
6. The model is deterministic and expert-driven, not validated against real incident post-mortems.
7. STIX support is a prototype-level parser, not a fully compliant enterprise CTI pipeline.
</data_limitations>

<recommended_improvements>
Include these recommendations:

1. Add more event descriptions and richer incident taxonomy.
   - The current dataset has too few unique descriptions.
   - More precise descriptions would improve classification and impact analysis.

2. Improve business process metadata.
   - Add process owners,
   - operational dependencies,
   - acceptable downtime,
   - recovery priority,
   - financial/mission criticality,
   - escalation contacts.

3. Add cost prediction.
   - Estimate financial and operational cost of each incident.
   - Use this to improve resource allocation.

4. Add responsible-person notification.
   - Add emails/contact details to assets/processes.
   - Automatically notify responsible people when their assets/processes are affected.

5. Add task orchestration.
   - Generate tasks for each responsible person.
   - Use a free/open-source task board instead of a proprietary paid Trello dependency.
   - Each task should include the MICA event summary, impacted assets, severity, and recommended actions.

6. Add AI-assisted textual analysis.
   - Use AI to analyze free-text incident descriptions.
   - Identify the likely breach or vulnerability.
   - Map the event to MITRE ATT&CK tactics/techniques.
   - Suggest possible attack paths and mitigations.

7. Add stronger STIX/TAXII integration.
   - Convert human-readable incidents into structured CTI format where possible.
   - Import structured threat intelligence from STIX/TAXII feeds.
   - Connect events to known TTPs, CVEs, and indicators of compromise.
</recommended_improvements>

<slide_deck_requirements>
Create a presentation with approximately 10 to 14 slides.

For each slide, provide:
- slide title,
- key message,
- bullet content,
- suggested visual,
- speaker notes,
- optional one-sentence pitch line.

The slides must be concise enough for a 5-8 minute hackathon presentation.

The tone should be:
- professional,
- strategic,
- operational,
- cyber-defense oriented,
- credible for a maritime / defense context,
- not exaggerated,
- not startup buzzword-heavy.
</slide_deck_requirements>

<suggested_slide_structure>
Use or improve this structure:

1. Title slide
   - MICA: Maritime Impact Cyber Analysis
   - Cyber operational impact prioritization for maritime/logistics environments.

2. The operational problem
   - Cyber incidents create uncertainty.
   - Teams lose time deciding what to investigate first.

3. Why it matters
   - Maritime/logistics systems are highly interdependent.
   - One event can cascade across assets, processes, and locations.

4. Our solution
   - MICA transforms an event into an operational impact picture.

5. How the system works
   - Event intake → classification → scoring → propagation → business impact → action plan.

6. Data model
   - Events, attacks, assets, dependencies, business processes, locations.

7. Expert-driven prioritization
   - Event type ranking.
   - Business process criticality ranking.
   - Explainable scoring.

8. Demo workflow
   - User selects/imports event.
   - MICA outputs impacted assets, processes, zones, graph, actions.

9. Value for analysts and decision-makers
   - Faster triage.
   - Better resource allocation.
   - Earlier propagation control.
   - Clearer operational communication.

10. Current prototype
   - Streamlit dashboard.
   - CSV/STIX-like import.
   - Batch analysis.
   - Propagation graph and geographic view.

11. Limitations
   - Synthetic data.
   - Limited event taxonomy.
   - Missing owner emails.
   - Need richer business process metadata.

12. Roadmap
   - More data.
   - AI-assisted breach analysis.
   - MITRE ATT&CK mapping.
   - Notifications.
   - Open-source task orchestration.
   - Cost prediction.

13. Future vision
   - From cyber event to operational decision in minutes.

14. Closing slide
   - MICA helps answer: what is impacted, where, why, and what should be handled first?
</suggested_slide_structure>

<visual_style>
The slide style should feel institutional, defense-oriented, and premium.

Visual direction:
- deep navy,
- off-white,
- restrained red accent,
- tactical tables,
- thin borders,
- command-center layout,
- no childish icons,
- no startup gradients,
- no crypto/dashboard clichés.

Suggested visual elements:
- maritime network graph,
- incident-to-impact chain,
- asset dependency diagram,
- operational priority matrix,
- map with affected zones,
- simplified Streamlit dashboard screenshot placeholder,
- MITRE ATT&CK mapping placeholder,
- before/after analyst workflow.
</visual_style>

<output_format>
Return the answer in this format:

1. Executive narrative:
   - 5-7 sentence story of the project.

2. Slide-by-slide deck:
   For each slide:
   - Title
   - Key message
   - Content bullets
   - Suggested visual
   - Speaker notes

3. Final 30-second pitch:
   - A short spoken script for the final slide.

4. Jury Q&A preparation:
   - 8 likely jury questions,
   - suggested answers.

5. Design recommendations:
   - visual style,
   - layout,
   - colors,
   - icons,
   - diagrams to include.
</output_format>

<quality_bar>
Make the deck sound credible to cyber experts.

Avoid overclaiming.

Be honest about limitations while making the product vision strong.

Do not say the system “predicts attacks perfectly”.
Say it helps prioritize likely operational impact using available data, expert scoring, and dependency propagation.

The presentation must make the jury understand that MICA is not just a dashboard: it is a decision-support tool for cyber-operational prioritization.
</quality_bar>

