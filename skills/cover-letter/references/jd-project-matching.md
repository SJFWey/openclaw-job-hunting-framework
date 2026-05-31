# JD–Project Matching (Cover Letter Prep)

Use this reference during cover-letter drafting **before** writing prose. Analysis can be technical and specific; the final letter stays general (domains, no tool laundry lists) per `SKILL.md` Generation Rules.

## Phase 1 — Decompose the JD

Read `JD.md` once, then produce a structured JD brief:

| Field | What to extract |
|-------|-----------------|
| Role title & level | Junior / graduate / Wissenschaftliche*r Mitarbeiter*in (not Postdoc) |
| Core mission | 1–2 sentences: what the team actually builds or validates |
| Must-have requirements | Hard skills, degrees, languages, location, work mode |
| Nice-to-have | Secondary stack, domain knowledge |
| Task verbs | e.g. calibrate, deploy, evaluate, integrate, prototype, test |
| Domain signals | automotive, aerospace, industrial inspection, medical, robotics, control, plasma, … |
| Stack signals | Python, C++, OpenCV, PyTorch, ONNX, PLC, SQL, point clouds, 3D, anomaly detection, … |
| Soft / process | documentation, teamwork, customer-facing, validation, safety |

Tag each requirement:

- **P0** — explicit must-have or repeated in JD  
- **P1** — clearly desired  
- **P2** — peripheral mention  

Note **anti-signals** from `docs/profile.md` (pure PLC-only, Postdoc, C++-only roles) and flag if the JD conflicts.

## Phase 2 — Route to project documents

Scan **all** eight experiences below. For each, assign relevance: **high / medium / low / skip** against the JD brief. Read `docs/profile.md` categories (A–E) as a hint, not a substitute for reading docs.

| Doc pair | Primary domains (routing hints) |
|----------|--------------------------------|
| `Masterarbeit` + `-Hintergrund` | FPP, endoscopic/ confined-space calibration, Z-axis workflow, bundle adjustment, phase unwrapping, analytical Jacobian, 3D reconstruction, µm-level lab metrics |
| `Studienarbeit` + `-Hintergrund` | Multi-camera calibration, ChArUco, PnP, extrinsics, BA, AR registration, error propagation, RealSense, Unity simulation |
| `Bachelorarbeit` + `-Hintergrund` | PID tuning, genetic algorithm, MATLAB/Simulink, control simulation, multi-objective cost function, offline optimization |
| `Praktikum` + `-Hintergrund` | Experimental setup, OES/plasma, PVD context, Python signal analysis, SQL/Grafana, sensor pipeline, lab troubleshooting |
| `HiWi` + `-Hintergrund` | PLC + Python supervisory control, Snap7, industrial test bench, high-rate logging, piezo/vibration, MRO/disassembly context |
| `Projekt-01` + `-Hintergrund` | 2D detection, KITTI, Faster R-CNN, ONNX export, C++ ORT inference, SORT tracking, deployment consistency |
| `Projekt-02` + `-Hintergrund` | LiDAR point clouds, geometric 3D proposals, RANSAC ground, clustering, OBB, SemanticKITTI eval |
| `Projekt-03` + `-Hintergrund` | AOI, anomaly detection, PaDiM/PatchCore, thresholds, industrial inspection pipeline, ONNX deploy |

**Selection rule for deep read:**

- **High** → read **both** `docs/<Name>.md` and `docs/<Name>-Hintergrund.md` in full (or thorough sections).  
- **Medium** → read canonical fully; skim Hintergrund for architecture/evaluation sections.  
- **Low** → canonical Kurzprofil + Risiken only.  
- **Skip** → do not use in letter unless user insists.

Typically **2–4** projects deserve deep read; do not skip deep read on high-relevance items to save tokens.

## Phase 3 — Mine evidence (per shortlisted project)

For each shortlisted project, extract evidence bullets in this shape:

```text
- JD ref: [P0/P1] <short requirement quote or paraphrase>
  Evidence: <what was done — from canonical + Hintergrund>
  Source: <Name>.md §… ; <Name>-Hintergrund.md §…
  Match type: direct | adjacent | weak
  Bridge: <one sentence: why this matters for THIS role's tasks>
  Claim strength: strong | medium | cautious
  Safe wording hint: <verb boundary from canonical Risiken, e.g. "im Prototyp", "unterstützt">
  Use in letter: yes | maybe | no (analysis only)
```

**Match types**

- **direct** — same task domain and similar methods (e.g. JD asks calibration → Masterarbeit calibration workflow).  
- **adjacent** — transferable engineering skill (e.g. JD asks test automation → Projekt-03 eval pipeline + metrics discipline).  
- **weak** — same broad field only; mention only if nothing stronger exists, with cautious wording.

**Mining checklist (Hintergrund sections)**

When reading `-Hintergrund.md`, deliberately look for:

- End-to-end pipelines (input → processing → artifact)  
- Integration boundaries (Python/C++, host/PLC, train/deploy)  
- Evaluation discipline (metrics, consistency checks, benchmarks)  
- Failure modes and limits (shows honest fit for validation/test roles)  
- Quantified results **only if** canonical allows the same claim  

Do **not** promote Hintergrund-only facts into the letter unless corroborated or compatible with canonical.

## Phase 4 — Fit matrix (deliverable before draft)

Present a table to the user (required before first draft):

| JD requirement (P0/P1) | Best evidence | Project | Match | Strength | Letter? |
|------------------------|---------------|---------|-------|----------|---------|
| … | … | Masterarbeit | direct | strong | yes |

Add a short **synthesis** (3–5 bullets):

- Top 2 requirements the candidate covers well  
- 1 requirement with partial/adjacent coverage (honest gap)  
- Which matrix rows to **`Letter? = yes`** for the middle section (often 2–4, covering distinct P0 themes)  
- Suggested **opening hook** (one JD phrase + one fit signal)  

## Phase 5 — Map to complete letter (after matrix approval)

Map to all four blocks in `Motivationsschreiben_Vorlage.md`:

| Block | Source |
|-------|--------|
| `[OPENING]` | Position title + top P0 hook from synthesis |
| `[MOTIVATION & FIT]` | **All** rows with `Letter? = yes`, woven into 2–3 paragraphs (not a CV list) |
| `[FORMALITÄTEN]` | Fixed residence/availability text from cover-letter skill (unless user opts out) |
| `[CLOSING]` | `Ending_Satzbaukasten.md`, no new technical claims |

- Do **not** limit the middle to one primary + one secondary project only to keep the letter short.  
- Each substantive sentence in `[MOTIVATION & FIT]` should trace to a matrix row.  
- Prose: general domains in the letter (tools/metrics only if JD-specific or user asks).  
- Bridge pattern: `In meiner <Thesis/Praktikum/Projekt> … habe ich <domain activity>. Für <JD task> ist das relevant, weil …`

## Phase 6 — Fact-check loop

Re-read canonical `Risiken, Grenzen` for every project cited in the draft. Downgrade any sentence that violates safe formulations.

## Quick domain → project map (JD keyword triggers)

| JD keywords (examples) | First projects to deep-read |
|------------------------|----------------------------|
| calibration, 3D, reconstruction, camera, projector, metrology | Masterarbeit, Studienarbeit |
| multi-camera, AR, registration, extrinsic | Studienarbeit |
| anomaly, inspection, AOI, quality, defect | Projekt-03 |
| detection, tracking, ONNX, deployment, C++ inference | Projekt-01 |
| LiDAR, point cloud, 3D detection, clustering | Projekt-02 |
| PLC, automation, test bench, acquisition | HiWi |
| experiment, spectroscopy, plasma, data pipeline | Praktikum |
| control, simulation, PID, optimization | Bachelorarbeit |
| validation, test, metrics, benchmark, prototype | Projekt-03, Projekt-01, Masterarbeit (eval sections) |

When multiple rows match, prefer projects with **direct** match and **strong** canonical evidence over profile headline numbers alone.
