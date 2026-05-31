---
name: cover-letter
description: Generates a tailored German or English cover letter for a tracked job application. Use when the user asks to draft, refine, render, or save a cover letter, Anschreiben, Motivationsschreiben, or application letter. Runs structured JD-to-project matching (canonical + Hintergrund docs), then writes a complete four-block letter per Motivationsschreiben_Vorlage.md.
---

# Cover Letter

## What This Skill Does

Generates a **complete** tailored German cover letter (Motivationsschreiben / Anschreiben) for a specific tracked application.

**Core principle:** Deep JD–project analysis first (Fit Matrix), then a **full letter** with all mandatory sections—not a shortened stub. Claims come from **canonical** `docs/<Name>.md`; match discovery uses **canonical +** `docs/<Name>-Hintergrund.md` (see `references/jd-project-matching.md`). Letter shape comes from `docs/Satzbaukaesten/Motivationsschreiben_Vorlage.md`.

## Mandatory letter structure (do not omit blocks)

Every German draft must include, in order:

1. **Anrede** (portal/JD contact person if known, else „Sehr geehrte Damen und Herren,“)
2. **`[OPENING]`** — position + strongest JD hook (1–2 sentences)
3. **`[MOTIVATION & FIT]`** — developed middle (typically **2–3 paragraphs**), JD bridges woven from Fit Matrix
4. **`[FORMALITÄTEN]`** — fixed residence / availability paragraph (standard wording below)
5. **`[CLOSING]`** — polite close without new technical arguments (1–2 sentences)
6. **Sign-off** — „Mit freundlichen Grüßen“ + name

Standard **Formalitäten** text (German, unless user asks to change):

`Mein Aufenthaltstitel wird derzeit von einem Studientitel auf einen Titel zur Arbeitsplatzsuche umgestellt. Nach aktuellem Stand kann ich ab September 2026 eine Vollzeitbeschäftigung aufnehmen; die weitere Umwandlung in einen Arbeitstitel kann nach Vorliegen eines Arbeitsvertrags erfolgen.`

Read slot rules in `docs/Satzbaukaesten/Motivationsschreiben_Vorlage.md` before drafting.

## Workflow

### A. Application & JD

1. Locate target application by APP-ID, company name, or position.
2. Read `JD.md` from the OneDrive folder (tracker `jd_path`).
3. **JD decomposition** per `references/jd-project-matching.md` Phase 1 (P0/P1/P2, domain, stack, avoid-list conflicts).

### B. Company & profile context

4. **Company research:** verifiable hooks for motivation (products, domain, news); do not invent.
5. Read `docs/profile.md` / CV only for gaps not covered by project docs.

### C. Project matching (before prose)

6. **Route all eight projects** (Phase 2 in matching reference).
7. **Deep-read** high/medium relevance: canonical + `-Hintergrund` as specified in reference.
8. **Mine evidence** (Phase 3): JD req → activity → source → match type → bridge → claim strength.
9. **Fit Matrix** (Phase 4): show table + synthesis before or with first draft; wait for user unless they asked for one-shot.

### D. Formulation assets

10. Read `docs/Satzbaukaesten/Motivationsschreiben_Vorlage.md` (four blocks).
11. Read Satzbaukästen: `Opening_`, `Motivation_`, `Ending_`; project modules for matrix-selected items only.

### E. Draft complete letter

12. Write the **full Motivationsschreiben** using Fit Matrix rows with `Letter? = yes`:
    - **Opening:** per Vorlage (no company name in first sentence).
    - **Middle:** 2–3 paragraphs; weave **all** strong matrix matches (often 2–4 experience threads), each with explicit JD bridge; not a CV list; no institution names; domain-level tech wording unless user wants more detail.
    - Treat small personal side projects as supplementary evidence, not as the main experience thread. Prefer formal experience such as Masterarbeit, HiWi, Praktikum, and thesis work as the backbone; if side-project evidence is useful, describe the capability directly rather than naming the project as a headline.
    - **Formalitäten:** always include standard residence paragraph (separate paragraph).
    - **Closing:** from `Ending_Satzbaukasten.md`.
    - DE default; EN if JD is English.
    - Target **one A4 page** via normal prose length, not by deleting blocks or collapsing the middle to one short paragraph.
    - No em dashes (— or –) in body; no marketing fluff.
    - If page 2 is only signature/closing spill: adjust PDF layout (`--font-size 10`) before cutting substantive content.

13. Tone pass: sincere junior engineer; simple German.

14. Fact-check every cited project against **canonical** docs (Phase 6 in matching reference).

15. Deliver **Fit Matrix + complete letter text**; iterate until approved.

### F. PDF & tracker

16. Render via `scripts/pdf_ops.py render`.
17. Save OneDrive job folder as `Motivationsschreiben.pdf`.
18. Verify layout and page count.
19. Update `cover_letter_path`; run `tracker_ops.py validate`.

## Inputs

- APP-ID or identifying info (required)
- Language: DE (default) or EN
- Optional: emphasize specific projects or Satzbaukästen
- Optional: user waives Fit Matrix preview (still run matching internally)

## Outputs

- JD brief + Fit Matrix + evidence notes
- **Complete draft** (all four content blocks + Anrede + Grußformel)
- After approval: PDF + tracker update

## Key paths

- Matching: `skills/cover-letter/references/jd-project-matching.md`
- Letter template: `docs/Satzbaukaesten/Motivationsschreiben_Vorlage.md`
- JD: OneDrive `jd_path` → `JD.md`
- Evidence: `docs/<Name>.md` + `docs/<Name>-Hintergrund.md`

## Generation Rules

- **Never substitute a “short cover letter” for the full four-block letter.**
- Matching depth ≠ letter brevity; use matrix to write a developed middle section.
- Template controls structure; canonical controls claim strength; Hintergrund controls what to connect to the JD.
- Satzbaukästen: adapt, do not paste entire modules blindly.
- Explicit JD bridges in the middle; avoid empty “passt zu Ihren Anforderungen” without substance.
- Do not omit Formalitäten unless the user explicitly requests it for that application.
- Never packet/send without approval; require existing tracker application.

## Anti-patterns (avoid)

- One-paragraph middle or only one project example when the matrix has several `Letter? = yes` rows.
- Skipping Formalitäten or merging it into Closing.
- Drafting without Hintergrund mining.
- Stronger claims than canonical allows.
