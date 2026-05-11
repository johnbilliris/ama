# Contract: Diagram Hash Manifest Format

**File**: `docs/architecture/.diagram-hashes`  
**Consumed by**: `docs-arch` CI job (step: `hash-manifest-check`); contributor quickstart  
**Spec refs**: FR-021(d), spec clarification Q3, research RQ-02

---

## Purpose

The `.diagram-hashes` manifest is the single source of truth for verifying that every PNG diagram
export is current with respect to its Draw.io source. It records the SHA256 digest of each
`.drawio` file at the time its sibling PNG was exported. A mismatch between the manifest entry and
the current file hash fails the `docs-arch` CI job, preventing stale PNG exports from reaching
`main`.

---

## Format Specification

```
{sha256_hex}  {relative_path}
```

- **Two spaces** between the hex digest and the path (standard `sha256sum` output format)
- `{sha256_hex}`: 64 lowercase hexadecimal characters (SHA-256 digest)
- `{relative_path}`: path relative to `docs/architecture/`, using forward slashes, no leading `./`
- **One entry per `.drawio` file**; one entry per line; no blank lines
- Lines sorted **lexicographically** by `{relative_path}`
- File encoding: UTF-8; line endings: LF (Unix)

### Example

```
a3f2c1d4e5b6789012345678901234567890123456789012345678901234567890  c4/component-agents.drawio
b1c2d3e4f5a6789012345678901234567890123456789012345678901234567891  c4/component-api.drawio
c2d3e4f5a6b7890123456789012345678901234567890123456789012345678902  c4/component-ingest.drawio
d3e4f5a6b7c8901234567890123456789012345678901234567890123456789013  c4/component-web.drawio
e4f5a6b7c8d9012345678901234567890123456789012345678901234567890124  c4/container.drawio
f5a6b7c8d9e0123456789012345678901234567890123456789012345678901235  c4/system.drawio
```

---

## Generation Procedure

### Linux / macOS (sha256sum)

```bash
# Run from the docs/architecture/ directory
cd docs/architecture
find . -name '*.drawio' | sort | xargs sha256sum \
  | sed 's|  \./|  |' \
  > .diagram-hashes
```

### Windows (PowerShell)

```powershell
Set-Location docs/architecture
Get-ChildItem -Recurse -Filter '*.drawio' |
  Sort-Object FullName |
  ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    $rel  = $_.FullName.Replace($PWD.Path + '\', '').Replace('\', '/')
    "$hash  $rel"
  } | Set-Content .diagram-hashes -Encoding UTF8
```

---

## CI Validation Step

```yaml
- name: hash-manifest-check
  working-directory: docs/architecture
  run: |
    sha256sum --check .diagram-hashes
    echo "Hash manifest: all $(wc -l < .diagram-hashes) entries matched."
```

**Exit conditions**:
- `0` — all hashes match; PNG exports are current
- `1` — one or more `.drawio` files differ from their manifest entry; PNG export is stale

---

## Invariants

1. Every `.drawio` file under `docs/architecture/` has exactly one entry.
2. No entry exists for a path that does not have a corresponding `.drawio` file.
3. Entries are sorted; a contributor running the generation procedure and committing the output
   produces an identical file on any platform.
4. The manifest is updated as the **last step** after PNG export (see quickstart.md).

---

## Failure Message

When `sha256sum --check` fails, the output is:

```
c4/system.drawio: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
```

The contributor must re-export the PNG for `c4/system.drawio`, then re-run the generation
procedure to update `.diagram-hashes`, and commit both files.
