import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
AGENTS_ROOT = ROOT / "apps" / "agents"
INGEST_RUNNER_ROOT = ROOT / "apps" / "ingest-runner" / "src"

for path in (ROOT, API_ROOT, AGENTS_ROOT, INGEST_RUNNER_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
