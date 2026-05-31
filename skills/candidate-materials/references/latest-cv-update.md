# Latest CV Update Pattern

Use this reference when the user uploads a newer `Lebenslauf.pdf` and asks to replace the saved CV in `docs/`.

## Concrete pattern

1. Resolve the active job-hunting workspace before editing.
   - Prefer the live tool working directory if it already contains `docs/Lebenslauf.pdf` and `docs/profile.md`.
   - Do not blindly use contradictory startup paths; verify with `pwd`/file existence.
2. Compare source and current canonical PDF before overwriting.
   - Source is usually under `~/.hermes/profiles/job-hunter/cache/documents/`.
   - Canonical target is `docs/Lebenslauf.pdf` in the job-hunting workspace.
   - Record size and SHA256 for both.
3. Extract text from both PDFs with the workspace venv and `pypdf`.
4. Produce a short unified diff of extracted text to spot factual/profile changes.
   - In the 2026-05-25 update, the meaningful changes were removal of `(FoV)` in one thesis sentence and addition of `Führerschein: Klasse B`.
5. Copy the uploaded PDF over `docs/Lebenslauf.pdf` only after the user clearly says it is the latest version.
6. Update `docs/profile.md` only for durable factual changes visible in the new CV.
   - Example: add `Driver's license: Class B` under Personal Information.
7. Write a dated note under `memory/YYYY-MM-DD.md` with source path, new canonical SHA256, verification, and profile edits.
8. Verify after replacement:
   - source and canonical SHA256 match;
   - PDF text extraction succeeds and page count is expected;
   - newly added facts are present in the canonical PDF and profile.

## Minimal verification snippets

```sh
sha256sum /path/to/uploaded.pdf docs/Lebenslauf.pdf
```

```sh
.venv/bin/python - <<'PY'
from pypdf import PdfReader
reader = PdfReader('docs/Lebenslauf.pdf')
text = '\n'.join(page.extract_text() or '' for page in reader.pages)
print('pages', len(reader.pages))
print('has_driver_license', 'Führerschein: Klasse B' in text)
PY
```
