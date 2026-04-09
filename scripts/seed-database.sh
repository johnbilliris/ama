#!/usr/bin/env bash
# postprovision hook: Seeds Cosmos DB and Blob Storage with reference data
# Called by: azd provision (via azure.yaml postprovision hook)
set -euo pipefail

echo "=== Post-Provision: Seeding databases ==="
echo ""

# ── Load azd environment variables ──
echo "Loading azd environment variables..."
while IFS='=' read -r key value; do
    value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')
    export "$key=$value"
done <<EOF
$(azd env get-values 2>/dev/null || true)
EOF

COSMOS_ENDPOINT="${AZURE_COSMOS_ENDPOINT:-}"
COSMOS_DATABASE="${AZURE_COSMOS_DATABASE:-disaster-hub}"
STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT_NAME:-}"

if [ -z "$COSMOS_ENDPOINT" ]; then
    echo "WARNING: AZURE_COSMOS_ENDPOINT not set — skipping Cosmos seeding"
else
    echo "Cosmos endpoint: $COSMOS_ENDPOINT"
    echo "Cosmos database: $COSMOS_DATABASE"
fi

if [ -z "$STORAGE_ACCOUNT" ]; then
    echo "WARNING: AZURE_STORAGE_ACCOUNT_NAME not set — skipping Blob seeding"
else
    echo "Storage account: $STORAGE_ACCOUNT"
fi

# ── Activate Python venv if available ──
VENV_PATH="$(dirname "$0")/../.venv/bin/activate"
if [ -f "$VENV_PATH" ]; then
    echo "Activating Python virtual environment..."
    source "$VENV_PATH"
fi

# ── Run Python seed script ──
echo ""
echo "Running Python seed loader..."
SEED_SCRIPT="$(dirname "$0")/seed_loader.py"
if [ -f "$SEED_SCRIPT" ]; then
    python "$SEED_SCRIPT" \
        --cosmos-endpoint "$COSMOS_ENDPOINT" \
        --cosmos-database "$COSMOS_DATABASE" \
        --storage-account "$STORAGE_ACCOUNT"
else
    echo "Running inline seed from bootstrap..."
    python -c "
import json, sys
from pathlib import Path

seed_root = Path('packages/domain/src/domain/seed')
from packages.domain.src.domain.seed.bootstrap import bootstrap_seed_data
data = bootstrap_seed_data(seed_root)
for kind, items in data.items():
    print(f'  {kind}: {len(items)} records')
print('Seed data validated successfully (dry run — no Azure connection)')
"
fi

echo ""
echo "=== Post-Provision: Seeding complete ==="