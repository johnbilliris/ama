#!/usr/bin/env sh

set -eu

container_name="${EVIDENCE_IMMUTABILITY_CONTAINER_NAME:-evidence-audit-cold}"

get_azd_value() {
    name="$1"
    value=$(printenv "$name" 2>/dev/null || true)
    if [ -n "$value" ]; then
        printf '%s' "$value"
        return
    fi

    azd env get-value "$name"
}

is_absent_error() {
    printf '%s' "$1" | grep -Eqi 'ContainerImmutabilityPolicyNotFound|ContainerNotFound|ResourceGroupNotFound|ResourceNotFound|could not be found|was not found'
}

command -v az >/dev/null 2>&1 || {
    echo 'Azure CLI is required to remove the evidence immutability policy before teardown.' >&2
    exit 1
}
command -v azd >/dev/null 2>&1 || {
    echo 'Azure Developer CLI is required to resolve the active teardown environment.' >&2
    exit 1
}

resource_group=$(get_azd_value AZURE_RESOURCE_GROUP)
storage_account=$(get_azd_value AZURE_STORAGE_ACCOUNT_NAME)

echo "Checking immutability policy '$container_name' in storage account '$storage_account'."
set +e
policy_state=$(az storage container immutability-policy show \
    --resource-group "$resource_group" \
    --account-name "$storage_account" \
    --container-name "$container_name" \
    --query state \
    --output tsv \
    --only-show-errors 2>&1)
show_status=$?
set -e

if [ "$show_status" -ne 0 ]; then
    if is_absent_error "$policy_state"; then
        echo 'No evidence immutability policy exists; teardown can continue.'
        exit 0
    fi
    echo "Unable to inspect the evidence immutability policy. $policy_state" >&2
    exit 1
fi

if [ -z "$policy_state" ]; then
    echo 'No evidence immutability policy exists; teardown can continue.'
    exit 0
fi

case "$policy_state" in
    Locked)
        echo "The evidence immutability policy is Locked and Azure will not permit its removal. Move storage account '$storage_account' to a retained resource group or wait for all retained blobs to expire before running azd down." >&2
        exit 1
        ;;
    Unlocked)
        ;;
    *)
        echo "Unsupported evidence immutability policy state '$policy_state'; teardown stopped to protect retained evidence." >&2
        exit 1
        ;;
esac

etag=$(az storage container immutability-policy show \
    --resource-group "$resource_group" \
    --account-name "$storage_account" \
    --container-name "$container_name" \
    --query etag \
    --output tsv \
    --only-show-errors)

if [ -z "$etag" ]; then
    echo 'The evidence immutability policy response did not include the ETag required for safe deletion.' >&2
    exit 1
fi

az storage container immutability-policy delete \
    --resource-group "$resource_group" \
    --account-name "$storage_account" \
    --container-name "$container_name" \
    --if-match "$etag" \
    --only-show-errors \
    --output none

echo 'Removed the evidence immutability policy before infrastructure deletion.'