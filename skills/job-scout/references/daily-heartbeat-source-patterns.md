# Daily Heartbeat Source Patterns

Use this reference when running the job-scouting heartbeat in the current mass-application phase.

## Access-limited sources

- LinkedIn guest search can expose useful title/company/location/date/link metadata after dismissing sign-in and cookie modals.
- Treat LinkedIn guest results as `Manual-check links` by default. Save them only when the public page or another original source exposes enough body text to validate role content, seniority, location, and risk flags.
- StepStone category pages often provide strong discovery and sometimes extractable individual JobPosting metadata. If an individual page is accessible and body text matches the role, it can be saved as a validated recommendation.
- If StepStone/LinkedIn/search results point to stale, blocked, login-gated, or page-not-found postings, do not discard promising titles; report them separately as manual-check links with source and caveat.

## Useful validation fallbacks

- WeAreDevelopers individual external-host pages may expose full job descriptions for roles first seen via LinkedIn/Indeed/search snippets.
- FERCHAU `touch.ferchau.com` pages, SIKORA job PDFs, E-Experts/AllatNet recruiter pages, DEVjobs individual pages, JOIN company pages, and some XING individual job pages can expose enough role body, seniority, location, and risk detail to save mid-tier mass-application recommendations when the fit is >= 0.5.
- JOIN individual company pages can be especially useful for direct ATS-style validation of startup/SME computer-vision and industrial-AI roles; queries like `site:join.com/companies "computer vision" Germany Engineer` can surface roles missed by mainstream boards.
- DEVjobs aggregate pages are good discovery surfaces for hidden adjacent roles in broader C++/C#/junior searches, but save only when an individual job hash/page exposes enough detail. Useful patterns include C++/C# pages surfacing embedded image-processing, application-engineering, ML, and test-automation roles.
- Indeed pages can sometimes expose enough summarized job content to validate technical fit, but prefer direct company pages if available.
- Search-engine snippets are discovery only unless corroborated by a direct company/ATS/job-board page with full metadata.

## Common noise patterns

- LinkedIn `computer vision engineer` searches are often polluted by repeated Mindrift freelance AI-training listings and senior-only postings.
- LinkedIn `computer vision` / `Bildverarbeitung` web searches can also surface spam-indexed Chinese-title URLs with only a real-looking job snippet embedded; do not count these as manual-check candidates unless the title/company/location metadata are clearly trustworthy.
- LinkedIn `machine vision` mixes real CV/perception leads with robotics/control-heavy roles, internships/working-student posts, and senior/expert roles.
- Broad `validierung` queries often return pharma/process validation rather than vision/perception validation.
- AcademicPositions CV/image-processing pages often skew professor/postdoc/PhD and may be outside junior/entry industry targets.
- Workday-backed direct pages for large companies such as ZEISS/TRUMPF may extract only cookie/privacy shells even when search snippets show strong fit. Keep as manual-check unless another source exposes the job body; do not save from cookie-shell extraction alone.
- Direct company search/listing pages can expose promising titles without duties/requirements (e.g. `Image Engineering` roles). Treat these as manual-check unless the detail page validates responsibilities, seniority, and risks.
- Direct company search results can point to stale localized career URLs (e.g. a relevant Allied Vision title that extracts as page-not-found); keep these as manual-check links, not validated saves, unless the canonical English/German career page validates.

## Reporting rule

For heartbeat reports, keep validated saved recommendations separate from `Manual-check links`. In the mass-application phase, target about 20 plausible manual-check links when enough candidates exist, and state why if fewer are available.
