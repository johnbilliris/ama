# `scripts/disaster_corpus/` — corpus build pipeline

Tools to fetch, render, validate and catalogue Australian disaster-management
publications into `docs/<jurisdiction>/<topic>/`. Output is consumed by RAG
pipelines that may run in life-critical disaster-response contexts, so the
focus is on **provenance, reproducibility and licence-aware indexing**.

## End-to-end usage

```pwsh
# 1. Build (or refresh) every source listed in sources.yaml.
#    Idempotent: ETag/Last-Modified short-circuits unchanged sources.
python scripts/disaster_corpus/build.py --report scripts/disaster_corpus/last_run_report.json

# 2. Re-write docs/MANIFEST.md from every source.json sidecar.
python scripts/disaster_corpus/manifest.py

# 3. Sanity-check the corpus on disk (PDF magic, sha256 match, image refs).
python scripts/disaster_corpus/validate.py
```

## Files

| File | Role |
|---|---|
| `sources.yaml` | Curated catalogue. Add a YAML block per new source. |
| `fetch.py` | Cache-aware downloader. Allow-list of hosts, conditional GET, polite per-host throttle, browser UA + RFC 9110 `From` header. |
| `pdf_to_md.py` | PyMuPDF-based PDF→Markdown converter. Page-aligned, image-extracting, byte-equivalent to existing AIDR samples. |
| `build.py` | Orchestrator. Reads `sources.yaml`, calls fetch + convert, writes `source.json` + `handbook.md`. Supports `--only`, `--limit`, `--dry-run`, `--report`. |
| `manifest.py` | Generates `docs/MANIFEST.md` from every `source.json`. |
| `validate.py` | Enforces invariants per topic folder (PDF magic, sha256 match, image refs resolve). |
| `aidr_backfill.py` | One-shot to synthesise `source.json` for the pre-pipeline AIDR samples. |
| `sitemap_crawl.py` | Discovery aid — parse a publisher's sitemap, filter by EM keywords, extract PDF anchors from candidate pages. Use to find new sources to curate into `sources.yaml`. |
| `discover.py`, `discover_browser.py`, `sitemap_pdfs.py`, `probe.py`, `wayback_discover.py`, `filter_wayback.py` | Lower-level discovery helpers (plain-HTML scraping, sitemap parsing, range probes, Wayback CDX). Mostly used while expanding the catalogue, not on every build. |

## Adding a new source

1. Find the canonical PDF URL on the publisher's site (sitemap_crawl.py is the
   fastest first pass; for SPA-only publishers use a browser to copy the URL).
2. Verify the licence on the cover. Most AU government docs are CC BY 4.0;
   AFAC/AusVet/Red Cross use practitioner-use grants.
3. If the host isn't already in `DEFAULT_ALLOW_HOSTS` in `fetch.py`, add it
   (the allow-list is a deliberate guardrail).
4. Append a YAML block to `sources.yaml`:

```yaml
  - jurisdiction: <national|aidr|nsw|vic|qld|sa|wa|tas|nt|act>
    topic: <kebab-slug-unique-within-jurisdiction>
    title: <H1 used in the rendered Markdown>
    publisher: <as printed on the cover>
    url: <stable PDF URL on publisher's domain>
    edition: "<year or version>"           # optional
    licence: "CC BY 4.0"                    # or other verified grant
    mode: full-text                         # full-text | metadata-only | excluded
    filename: <override-name>.pdf           # optional
    notes: <one-line context>               # optional
```

5. Run `python scripts/disaster_corpus/build.py --only <jurisdiction>` (the
   filter is jurisdiction-level; cached entries are 304-skipped).
6. Run `python scripts/disaster_corpus/manifest.py` to refresh the manifest.
7. Run `python scripts/disaster_corpus/validate.py` to confirm consistency.
8. Open a PR. Reviewers verify the licence and mode.

## Soft-404 detection

Some Australian government sites return HTTP 200 with `text/html` for
non-existent `.pdf` URLs. `validate.py` catches this by reading the first 5
bytes — if they aren't `%PDF` the entry is flagged. Remove the offending YAML
block and the corresponding empty `docs/.../<topic>/` folder.

## Conventions

- One PDF per topic folder. Multi-volume publications get sibling topics.
- Folder slug = lowercase kebab-case, jurisdiction-prefixed for state/agency
  doctrine (e.g. `nsw-rfs-op-1-2-20-backburning`).
- `handbook.md` H1 = the title from `sources.yaml`. Edition is appended in
  parens if known.
- Front-matter blockquote is the same on every handbook (Source, URL,
  Edition?, Licence?, Retrieved, SHA-256). Don't break this — downstream RAG
  chunkers parse it.
- `## Page N` headers are the chunk boundary. Don't add other H2 headings.
