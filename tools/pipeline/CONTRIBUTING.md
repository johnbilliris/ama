# Contributing — pipeline-tools

## Local install

```pwsh
cd tools/pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # or `source .venv/bin/activate`
pip install -e .[dev]
```

## Run the test suite

```pwsh
pytest ../../tests/pipeline -q
```

## Lint and type-check

```pwsh
ruff check .
mypy --strict src
```

## Dry-run a CLI against a fake backend

Each CLI accepts `--dry-run` and a `--fixture` flag pointing at a JSON file
under `tests/pipeline/integration/fixtures/`. Example:

```pwsh
posture-verifier --dry-run --fixture ..\..\tests\pipeline\integration\fixtures\rg-inventory-good.json
```

The fixture flags short-circuit the Resource Graph / Cosmos / Blob calls and
return canned responses, allowing local development without an Azure tenant.

## Producing a local OPA decision against a sample What-If

```pwsh
conftest test --policy ../../infra/policy/rego --data ../../infra/policy/posture-matrix.yaml \
  ../../tests/pipeline/contract/fixtures/whatif-good.json
```
