# Spec-038 — Measurable Success-Criteria Evidence Harness (T-Z03)

Six pillar sub-modules, each fronted by a single FastAPI router included
under `/api/v1/evidence/*`.

| Pillar | Module path                                                 | Endpoint                                          | FR / SC anchor              |
| ------ | ----------------------------------------------------------- | ------------------------------------------------- | --------------------------- |
| A      | `kpi_ladder/`                                               | `GET  /kpi-ladder`                                | FR-001..FR-006, SC-001/012  |
| B      | `measurement/`                                              | `GET  /measurement-method`                        | FR-007..FR-010, SC-002      |
| C      | `simulation/`                                               | `POST /scenarios/{id}/replay`                     | FR-011..FR-016, SC-003/004  |
| D      | `impact/`                                                   | `GET  /causal-chains/{capability_id}`             | FR-017..FR-019, SC-006      |
| E      | `benchmarks/`                                               | `GET  /benchmarks/{kpi_id}?jurisdiction=…`        | FR-020..FR-022, SC-007      |
| F      | `instrumentation/`                                          | `GET  /audit/{value_id}`                          | FR-023..FR-029, SC-005..010 |
| -      | `health.py`                                                 | `GET  /healthz/evidence`                          | Research D13                |

Cross-cutting:
- `_clients.py` — in-memory registry standing in for the 7 Cosmos containers.
- `_guards.py` — AU-region guard (FR-029).
- `_problem_details.py` — RFC-7807 + advisory-only banner (FR-030).
- `_summariser.py` — deterministic LLM-summarisation adapter (FR-030 / D6).
- `_correlation.py` — `x-ama-correlation-id` echo middleware.
- `kpi_ladder/rank.py` — life-safety primacy ranker (FR-006).
- `measurement/confidence.py` — bootstrap-95 % CI helper (FR-009 / D5).
- `instrumentation/audit_manager.py` — append-only audit Manager (FR-025).

All persistence is AU-region only; audit container is append-only;
every response carries `ama_advisory_only: true`.
