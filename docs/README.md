# Australian Disaster-Management Corpus

This directory is a citable, reproducible corpus of Australian disaster-management
procedures, plans, handbooks, and doctrine. It exists to ground a Retrieval-Augmented
Generation (RAG) system whose answers may be acted on during a live disaster
response — so accuracy, currency, and provenance are first-class concerns.

> **Purpose**: every entry is preserved both as the original artifact (PDF) and
> as a faithful page-by-page Markdown rendering with extracted images, alongside
> a `source.json` sidecar that records the upstream URL, SHA-256, retrieval
> timestamp, publisher, edition, and licence. The same shape used by AIDR
> handbooks is followed for every other source so downstream chunkers, embedders,
> and citation generators behave identically across jurisdictions.

## Layout

```
docs/
  MANIFEST.md                    # Auto-generated table of every entry
  README.md                      # This file
  aidr/                          # AIDR handbooks (the gold-standard exemplar)
    <topic>/
      <source>.pdf
      handbook.md
      images/
      source.json
  national/                      # Federal / Commonwealth doctrine
  nsw/  vic/  qld/  sa/  wa/  tas/  nt/  act/   # State + territory doctrine
```

Per-topic folders contain:

| File | Purpose |
|---|---|
| `<source>.pdf` | The original artifact, byte-identical to the publisher's copy. |
| `handbook.md` | High-fidelity Markdown render. One `## Page N` heading per page. Every embedded raster image is extracted to `./images/page_<N>_img_<M>.<ext>` and referenced inline. The leading blockquote captures title, publisher, source URL, retrieved date, SHA-256, and (where known) edition + licence. |
| `images/` | Extracted images, named to mirror the page they came from. |
| `source.json` | Machine-readable provenance record. SHA-256 + retrieved timestamp make every record reproducible; `etag` / `last_modified` fields support polite conditional GET on re-runs. |

## Coverage

The corpus is curated bottom-up across four tiers:

1. **National / Commonwealth** — NEMA, Department of Home Affairs, BOM, AFAC,
   Department of Health & Aged Care, Red Cross, NTC.
   Includes the National Disaster Risk Reduction Framework, Australian Disaster
   Recovery Framework, Australia's National Action Plans + Sendai Mid-Term Review,
   the Disaster Recovery Funding Arrangements 2018 + every published guideline +
   every 2025 national advisory, the CASP (Crisis Appreciation and Strategic
   Planning) Guidebook, AHMPPI, the ANZ Emergency Response Guide for hazmat
   transport incidents, REDiPlan (Comprehensive + Lite), and AUSVETPLAN response
   strategies for animal-disease emergencies.
2. **State / Territory peak plans** — e.g. Victorian SEMP, NSW Recovery Plan,
   Tasmanian DPFEM Future Focus, Ministerial Charter for the State Fire Commission.
3. **Agency-level operational doctrine** — NSW Rural Fire Service Service
   Standards (Powers of Officers, Media, Lessons Management, Breathing
   Apparatus) + Operational Protocols (Remote Area Firefighting, Prescribed
   Burning, Backburning, Rapid Aerial Fire Fighting Teams, Photovoltaic
   Arrays, Working in the Rail Corridor, Working on Roofs, Trail Bikes,
   Helicopter Search and Rescue, Fatigue Management); NSW Bush Fire
   Management Committee Handbook + Charter + BFCC Policy Register; NSW SES
   household-preparedness suite (storm, flash flood, tsunami x4, rural
   properties, caravan park template, household plan, kit checklist, pets);
   Tasmania Fire Service operational publications.
4. **Hazard-specific specialty** — AUSVETPLAN; ANZ-ERG2021 transport-incident
   guide; future additions for tsunami, marine SAR, radiation emergency.

> Pre-existing `docs/aidr/` AIDR Handbook Collection material is left untouched
> and is registered in this manifest via auto-generated `source.json` sidecars.

The source-of-truth list (with full URLs and licences) is
[`MANIFEST.md`](./MANIFEST.md).

## How content is fetched and rendered

The pipeline lives at `scripts/disaster_corpus/`:

| File | Role |
|---|---|
| `sources.yaml` | Hand-curated catalogue: `{jurisdiction, topic, title, publisher, url, edition, licence, mode, filename}` per source. Adding a new source = adding a YAML entry. |
| `fetch.py` | Polite cache-aware downloader. Conditional GET via ETag/Last-Modified, exponential backoff, ≤1 request per host every 2 s, browser-class User-Agent + RFC 9110 `From` header for transparency, allow-list of permitted hosts as a deliberate guardrail. SHA-256 captured per fetch. |
| `pdf_to_md.py` | PyMuPDF-based renderer. Emits one `## Page N` heading per page, extracts every embedded raster image to `./images/page_<N>_img_<M>.<ext>`, preserves text in reading order, and writes a front-matter blockquote with full provenance. Format is byte-equivalent to the existing AIDR samples. |
| `build.py` | Orchestrator. Reads `sources.yaml`, fetches + converts each entry, writes `source.json` and `handbook.md`, idempotent on re-run (304 Not Modified short-circuits). Supports `--only`, `--limit`, `--dry-run`, `--report`. |
| `manifest.py` | Walks `docs/` and (re)generates `docs/MANIFEST.md` from `source.json` sidecars + `handbook.md` front matter. |
| `aidr_backfill.py` | One-shot: synthesises `source.json` for the pre-existing AIDR handbooks so the manifest treats them uniformly. |

### Adding a new source

1. Find the canonical PDF URL on the publisher's site.
2. Add a block to `scripts/disaster_corpus/sources.yaml`.
3. If the host isn't already in `DEFAULT_ALLOW_HOSTS` in `fetch.py`, add it.
4. Run `python scripts/disaster_corpus/build.py --only <jurisdiction>/<topic>` to
   ingest only the new entry; the rest of the corpus is left undisturbed
   thanks to ETag-driven conditional GET.
5. Run `python scripts/disaster_corpus/manifest.py` to refresh `MANIFEST.md`.
6. Open a PR. The reviewer's responsibilities include verifying the licence
   block and (for human-or-life-critical doctrine) sanity-checking the
   rendered Markdown against the PDF.

### Refreshing the corpus

Re-running `python scripts/disaster_corpus/build.py` is safe: the fetcher
issues `If-None-Match` / `If-Modified-Since` against the publisher's server,
so unchanged sources are O(1). Sources with new editions are re-downloaded,
re-hashed, and the Markdown is re-rendered atomically.

## Licence and indexing model

| Mode | Meaning |
|---|---|
| `full-text` | The publisher has either explicitly licensed the work for redistribution (e.g. CC BY 4.0) or has issued a public-information / practitioner-use grant on the cover. The Markdown is chunked + embedded. |
| `metadata-only` | Title + URL + summary are indexed; the full body is not embedded. Default for any source whose redistribution rights are unverified. |
| `excluded` | The publisher has revoked permission. Must not be indexed. |

Most Australian Government publications are released under
[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
Each entry's `licence` field captures the verbatim grant; `MANIFEST.md` shows
the per-entry mode. Where a per-publisher grant is more restrictive (e.g.
Crown copyright with practitioner-use grant only), the entry is annotated
accordingly.

## Reproducibility

Every entry's `source.json` carries:

```json
{
  "url":           "https://...",
  "filename":      "....pdf",
  "sha256":        "<hex>",
  "bytes":         12345,
  "etag":          "...",
  "last_modified": "...",
  "content_type":  "application/pdf",
  "retrieved_at":  "2026-05-07T11:24:00Z"
}
```

Combined with the SHA-256 in the `handbook.md` front-matter, you can prove
that the rendered Markdown corresponds to a specific upstream byte sequence
fetched at a specific instant in time. This is the audit chain a RAG response
will eventually cite.

## Attribution

Each rendered handbook reproduces the publisher and source URL in its leading
blockquote. RAG responses grounded on this corpus must surface that citation.
The corpus does not modify, summarise, or paraphrase upstream content during
ingestion: the Markdown is a structural conversion of the PDF, page-aligned and
image-preserving, suitable for downstream chunking + retrieval.
