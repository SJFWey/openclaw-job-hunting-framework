---
name: candidate-materials
description: "Maintain the candidate master materials used by the job-hunting workspace: latest CV/Lebenslauf PDF, docs/profile.md, reusable project facts, and daily notes. Use when the user sends a new resume/CV, says a document is the latest version, asks to update the profile/materials database, or wants canonical application facts refreshed."
---

# Candidate Materials

## Purpose

Keep the job-hunting workspace's canonical candidate materials current and internally consistent. This skill covers updates to:

- `docs/Lebenslauf.pdf` — current master CV PDF used for applications and packets.
- `docs/profile.md` — structured candidate profile used by scouting, fit scoring, cover letters, and application summaries.
- `memory/YYYY-MM-DD.md` — short execution notes for temporary/session-specific material updates.
- Related reusable project or skill facts in `docs/*.md` when the user explicitly provides a newer source.

This skill is for maintaining source-of-truth materials, not for tailoring a cover letter or creating a job application entry.

## Standard Workflow

1. Identify the incoming source document path from the user message or uploaded attachment.
2. Locate the workspace canonical materials, normally:
   - workspace: `/home/xjwei/hermes-workspaces/job-hunting-helper`
   - CV: `docs/Lebenslauf.pdf`
   - profile: `docs/profile.md`
3. Compare the incoming file with the current canonical file before overwriting:
   - first resolve the actual workspace root from the live tool context (`pwd`/relative `docs/Lebenslauf.pdf`) instead of trusting conflicting startup-path hints;
   - compute file size and SHA256 for both PDFs;
   - if possible, extract text from both PDFs with `pypdf` or another available PDF extractor;
   - run a small unified text diff between old and incoming CV text to identify exact surface changes;
   - note major factual differences that may need profile updates.
4. Replace the canonical file only when the user clearly says the incoming document is the latest version.
5. Update `docs/profile.md` narrowly for durable factual changes visible in the latest source, such as:
   - current CV address/location wording;
   - contact details;
   - newly added skill categories;
   - licences/certifications;
   - materially changed education, experience, projects, or quantified results.
6. Write or append a short dated note in `memory/YYYY-MM-DD.md` with:
   - what was updated;
   - source filename/path if useful;
   - checksum of the new canonical file;
   - any profile fields changed.
   - For repeated CV revisions on the same day, append a new subsection instead of replacing earlier notes, so the sequence of canonical-file changes remains auditable.
7. Verify the result:
   - canonical PDF checksum equals the uploaded/source PDF checksum;
   - PDF opens/extracts and has the expected page count;
   - key new facts from the source are present in the canonical file and profile note;
   - when the change is a correction (e.g. a date or wording fix), explicitly check that the old incorrect text is no longer present in both `docs/Lebenslauf.pdf` extraction and any synced `docs/profile.md` fields.
8. Final response should be brief and factual: files updated, profile fields changed, verification status.

## PDF Extraction Pattern

Prefer lightweight extraction first. In the job-hunting workspace, `.venv` usually includes `pypdf`:

```sh
cd /home/xjwei/hermes-workspaces/job-hunting-helper
.venv/bin/python - <<'PY'
from pypdf import PdfReader
for path in ['docs/Lebenslauf.pdf']:
    reader = PdfReader(path)
    text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    print('pages:', len(reader.pages))
    print(text[:4000])
PY
```

Use the broader `ocr-and-documents` skill when the PDF is scanned, extraction is poor, or advanced layout/OCR is needed.

## Safety and Scope

- If the user explicitly says the uploaded CV is the latest version, replacing `docs/Lebenslauf.pdf` is in scope; do not ask for redundant confirmation.
- Do not write to OneDrive or build an application packet unless the user asks. Updating canonical workspace materials is separate from final application delivery.
- Do not make broad rewrites to `docs/profile.md` from one CV update. Keep edits minimal and evidence-backed.
- Do not update long-term agent memory for ordinary CV version changes; use workspace `memory/YYYY-MM-DD.md` for execution notes. Only durable career preferences or stable identity facts belong in agent memory.
- If a conflict appears between the latest CV and existing profile facts, prefer the latest CV for surface facts (address, displayed skills) and explicitly mention unresolved strategic conflicts in the final response.

## Related Skills

- `cover-letter`: drafting or refining Anschreiben/Motivationsschreiben for a specific application.
- `application-packet`: merging approved cover letters and attachments into PDF packets.
- `job-intake`: creating tracked application entries from job postings.
- `ocr-and-documents`: extracting text from difficult PDFs or scanned documents.

## References

- `references/latest-cv-update.md` records the concrete pattern from a successful latest-CV update session.
