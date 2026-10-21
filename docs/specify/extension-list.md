# Extension List CLI

`ama-specify` is an independently packaged, read-only Spec Kit-compatible CLI for inspecting AMA-local extensions. It exposes:

```text
ama-specify extension list
python -m specify_cli extension list
```

It does not expose or replace a `specify` command, import an upstream `specify` package, modify another checkout, or install, activate, repair, enable, disable, or remove extensions.

## Views

The thin client routes each request to the mode-bound, peer-authenticated package daemon.

- The default view lists installed registry and physical-manifest observations.
- `--available` lists schema-valid entries from configured catalogs.
- `--all` reconciles installed and available records by exact stable extension identifier.

Installed inventory remains available when catalog collection fails. A catalog failure discards all catalog rows for that invocation, retains the complete installed result, and emits one catalog-unavailable warning. A fallback display identity may identify a malformed local row, but it is display data and never an installed-to-catalog join key.

Local development defaults to `local-synthetic`. It accepts only marker-bound synthetic fixtures beneath owner-only session temporary storage and can use the configured HTTPS package proxy or existing package cache during bootstrap. It rejects repository live extension roots, production remote catalogs, qualifying evidence production, and real external modes.

Normal non-synthetic use is sovereign-only. It requires the signed sovereign preflight and a verified daemon on an eligible standalone AU Azure VM. Sovereign package sync, build, and installation are offline and use only an authorized, pre-seeded Australian mirror cache.

## Audit And Evidence

Every mode-bound runtime action uses the shared two-phase audit contract: an intent record is appended before work and its linked result record is appended after the same action and target complete. Local synthetic records use the ephemeral local journal and are non-evidentiary. Sovereign records use the immutable AU audit sink.

Output source evidence is deliberately restricted to:

- `kind`
- `source_sha256`
- `source_ordinal`
- `record_sha256`

Raw source identities, absolute paths, canonical input records, alternate descriptions, and author values are not emitted as evidence.

## Streams And Text Contract

Human rows and empty states use stdout. Human warnings and runtime errors use stderr. Human usage errors emit Typer usage to stderr and exit 2. JSON usage errors leave stdout empty, emit one compact JSON error plus a newline to stderr, and exit 2. Explicit help remains human-readable on stdout and exits 0.

The text renderer is the accessibility oracle. At 80x24 and 40x12, with color disabled or output redirected, each record appears once and retains the literal labels `Installed`, `Activation`, `Health`, `Commands`, and `Hooks`. Disabled, invalid, and conflict states remain textual. The command never starts a pager or requests input.

## Validation Ownership

Package coverage and root application coverage are independent gates. Package pytest owns branch-aware coverage for `specify_cli`; root validation retains its own configuration and externalized coverage output. Guarded pytest disables the cache provider, and guarded mypy uses an owner-only cache outside the repository.

A local green package gate proves only synthetic implementation behavior. It does not establish sovereign readiness, external-platform completion, human-study outcomes, release readiness, or pull-request gate success.
