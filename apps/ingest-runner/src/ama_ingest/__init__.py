"""ama_ingest — corpus ingest Container Apps Job (Spec 036, FR-RAG-IDX-01..05; R-08).

Scaffolded by T002. Implementation lands incrementally in T040–T058:

- ``chunker``        — H2-page chunker with 1024-token cap + 10% overlap (T041).
- ``embedder``       — text-embedding-3-large @ 3072 dims via LiveFoundryChatClient (T042).
- ``licence_filter`` — three-mode gating: full-text / metadata-only / excluded (T043).
- ``indexer``        — blue-green write to ``corpus-v{N+1}`` + alias flip helper (T044).
- ``manifest``       — ``corpus_build_sha`` + cosign keyless signature (T045).
- ``parity_gate``    — 4-signal gate per ingest-pipeline.md §3.3 (T046).
- ``offline_bundle`` — ≤500 MB cache bundle + dual signature (T047).

Entrypoint: ``python -m ama_ingest [--full | --incremental | --dry-run]`` (T040).
"""

__version__ = "0.1.0"
