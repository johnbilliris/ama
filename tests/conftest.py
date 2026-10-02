import gc
import os
import shutil
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
AGENTS_ROOT = ROOT / "apps" / "agents"
INGEST_RUNNER_ROOT = ROOT / "apps" / "ingest-runner" / "src"
DOMAIN_PKG_ROOT = ROOT / "packages" / "domain" / "src"

for path in (ROOT, API_ROOT, AGENTS_ROOT, INGEST_RUNNER_ROOT, DOMAIN_PKG_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

# Spec 036 / F-A10 / T218 — force UTF-8 stdio on every test process so Windows
# runners don't trip on CRLF + cp1252 codepoint surprises (closes F-DEL-08).
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("AMA_TEST_SUPPORT", "1")


@pytest.fixture(autouse=True)
def _evidence_test_mode(monkeypatch):
    monkeypatch.delenv("AMA_TEST_SUPPORT", raising=False)
    monkeypatch.setenv("AMA_TEST_MODE", "1")


@pytest.fixture(autouse=True)
def _reset_simulation_capacity_ledger():
    """Keep the process-wide simulation concurrency ledger per-test deterministic.

    The ledger is shared by every in-memory ``SimulationRepository`` so two
    instances enforce one cap (AUD-024). Resetting it between tests stops one
    module's active exercises from consuming another module's slots. Only resets
    when the module is already imported so non-API tests keep their import graph.
    """
    module = sys.modules.get("app.repositories.simulation_repository")
    if module is not None:
        module.get_shared_capacity_ledger().reset()
    yield
    module = sys.modules.get("app.repositories.simulation_repository")
    if module is not None:
        module.get_shared_capacity_ledger().reset()


@pytest.fixture
def clean_tmp_path(tmp_path: Path) -> Path:
    """Yield a temp directory that survives Windows file-handle lag.

    Closes F-DEL-01 — pytest's default ``tmp_path`` cleanup races
    against Windows release of mmap'd files. We force a GC sweep,
    pause briefly, then retry the rmtree if the first attempt fails.
    Linux runners get the same fixture but the retry is a no-op.
    """
    yield tmp_path
    # Best-effort cleanup; never raise from teardown.
    for attempt in range(3):
        try:
            gc.collect()
            time.sleep(0.05)
            shutil.rmtree(tmp_path, ignore_errors=True)
            if not tmp_path.exists():
                return
        except OSError:
            if attempt == 2:
                return
