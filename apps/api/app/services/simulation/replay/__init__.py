"""Spec-038 Phase 5 — replay package.

* :mod:`ndjson_writer` — canonical-NDJSON writer with mandatory
  ``.sha256`` sidecar (T076, T077).
* :mod:`ndjson_reader` — line-by-line parser (T075).
* :mod:`digest` — sidecar verification (fail-loud on mismatch — T077).
* :mod:`engine` — replay-into-:class:`EventHubPublisher` (T071).

This sub-package is isolated from production code by the import-linter
contract ``simulator_not_imported_by_production`` (Phase 1 / T004).
"""
