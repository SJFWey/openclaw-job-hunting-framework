---
name: application-packet
description: Build a single combined PDF for job application supporting documents when the user explicitly asks to merge, combine, concatenate, or prepare an application packet/Bewerbungsunterlagen PDF for a tracked application. Use for combining an approved motivation letter PDF with degree and internship certificates, and optionally other PDFs, using docs/attachments and tracker paths.
---

# Application Packet

## Scope

Build a combined PDF only when the user explicitly asks for a merged packet. Many job sites require separate uploads, so do not merge by default during intake or cover-letter drafting.

Default packet content is **supporting application materials**, not the CV. In normal German application portals the CV/Lebenslauf is uploaded as a separate file, so do not merge it into `Weitere_Unterlagen.pdf` or other supporting-material packets unless the user explicitly asks for one single complete PDF.

1. approved motivation letter PDF,
2. degree documents,
3. internship certificate,
4. optional other documents if requested.

Include the CV only if the user explicitly asks for a full single-file application PDF or the portal clearly requires all documents in one PDF.

## Preconditions

- Target application must be identifiable by APP-ID, company, or position.
- Cover letter must already be approved.
- Prefer an existing `cover_letter_path` in `data/applications.xlsx`; otherwise ask before rendering or using an untracked draft.
- Confirm OneDrive is mounted before writing under `/mnt/onedrive`.
- Do not send the PDF externally.

## Default Inputs

- Tracker: `data/applications.xlsx`
- Motivation letter: tracker `cover_letter_path` or job folder `Motivationsschreiben.pdf`
- Degree: prefer `/mnt/onedrive/Jobsuche/Lebenslauf & Zeugnisse/Urkunde_Master.pdf`; fallback `docs/attachments/degree/Urkunde-Master.pdf` if present
- Internship: prefer `/mnt/onedrive/Jobsuche/Lebenslauf & Zeugnisse/Praktikumszeugnis.pdf`; fallback `docs/attachments/internship/Praktikumszeugnis.pdf` if present
- Optional other document: use `/mnt/onedrive/Jobsuche/Lebenslauf & Zeugnisse/Notenspiegel.pdf` only when the user explicitly requests transcripts/grades or the JD/portal explicitly requires them; fallback `docs/attachments/other/Notenspiegel.pdf` if present
- Output name:
  - use `Bewerbungsunterlagen_komplett.pdf` only for a true complete one-file application packet that intentionally includes the CV,
  - use `Weitere_Unterlagen.pdf` by default when the CV is uploaded separately and the merged PDF contains only the cover letter plus supporting documents.

## Workflow

1. Locate the application and read tracker fields.
2. Confirm this site should receive a combined packet, not separate uploads, unless the user already stated that clearly.
3. Build the input list in order:
   - `Motivationsschreiben.pdf`,
   - Master degree document,
   - Praktikum certificate,
   - optional other PDFs requested by the user.
   - Do **not** include `Lebenslauf.pdf` by default; CV/Lebenslauf is normally uploaded separately.
   - If the user says “transcript/grades not needed” or says nothing about transcripts, do **not** use broad bundle files like `Zeugnisse.pdf`; instead merge only the specific safe PDFs (`Urkunde_Master.pdf`, `Praktikumszeugnis.pdf`) so the transcript is not accidentally included.
4. Before merging, verify the motivation-letter PDF is the final approved/rendered version and has acceptable page count/layout; if the user just requested layout changes, complete those first.
5. Verify every input PDF exists before merging.
6. Merge with `scripts/pdf_ops.py merge`:

```sh
uv run python scripts/pdf_ops.py merge "<out_pdf>" "<cover_pdf>" \
  docs/attachments/degree/Urkunde-Master.pdf \
  docs/attachments/internship/Praktikumszeugnis.pdf
```

6. Update tracker path:

```sh
uv run python scripts/tracker_ops.py update-paths APP-YYYY-NNN --packet-pdf-path "<out_pdf>"
```

7. Run validation:

```sh
uv run python scripts/tracker_ops.py validate
```

8. Report output path and included files.

## Rules

- Never create a packet before cover-letter approval.
- Never include `Notenspiegel.pdf` by default unless the site asks for transcripts/grades or the user asks for all documents.
- Never include CV by default; CV is usually uploaded separately. This remains true even if the user says “Bewerbungsunterlagen” unless they clearly ask for a complete single-PDF application.
- Do not use broad files like `Zeugnisse.pdf` by default, because they may contain transcripts or other documents the user did not ask to include.
- Keep merge order stable unless the user asks for a different order.
- If a required file is missing, stop and report the missing path rather than creating a partial packet.
