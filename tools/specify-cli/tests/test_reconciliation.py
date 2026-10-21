from __future__ import annotations

import json

from specify_cli.extensions.catalogs import CatalogSourceRecord
from specify_cli.extensions.models import ExtensionListEntry


def _installed(identifier: str = "shared-extension") -> ExtensionListEntry:
    from specify_cli.extensions.models import project_entry

    return project_entry(
        {
            "id": identifier,
            "fallback_identity": None,
            "source_locations": [f".specify/extensions/{identifier}"],
            "name": "Installed Name",
            "description": "Installed description.",
            "version": "1.0.0",
            "priority": 10,
            "enabled": True,
            "source": {"kind": "local"},
            "evidence": [
                {
                    "kind": "local",
                    "source_sha256": "1" * 64,
                    "source_ordinal": 0,
                    "record_sha256": "2" * 64,
                }
            ],
            "provides": {"commands": 1, "templates": 0, "scripts": 0, "hooks": 1},
            "install_allowed": None,
            "installed": True,
            "installed_version": "1.0.0",
            "available_versions": [],
            "activation_state": "active",
            "activation_diagnostic": None,
            "health": {"state": "healthy", "diagnostics": []},
            "conflict": False,
            "conflict_reasons": [],
            "catalog_sources": [],
        }
    )


def _catalog(
    *,
    identifier: str = "shared-extension",
    name: str = "Catalog Name",
    version: str | None = "2.0.0",
    description: str | None = "Catalog description.",
    author: str | None = "Private Author",
    catalog_name: str = "primary",
    priority: int = 1,
    ordinal: int = 0,
    record_digest: str = "3" * 64,
    install_allowed: bool = True,
    commands: int = 2,
    hooks: int = 0,
) -> CatalogSourceRecord:
    from specify_cli.extensions.catalogs import CatalogSourceRecord

    return CatalogSourceRecord(
        stable_id=identifier,
        name=name,
        available_version=version,
        description=description,
        author=author,
        catalog_name=catalog_name,
        catalog_priority=priority,
        source_ordinal=ordinal,
        source_sha256="4" * 64,
        record_sha256=record_digest,
        install_allowed=install_allowed,
        commands=commands,
        templates=0,
        scripts=0,
        hooks=hooks,
    )


def test_catalog_reconciliation_joins_only_exact_stable_ids() -> None:
    from specify_cli.extensions.inventory import reconcile_entries

    rows = reconcile_entries((_installed(),), (_catalog(), _catalog(identifier="other-extension")))

    assert [row.id for row in rows] == ["other-extension", "shared-extension"]
    assert {row.id: row.source.kind for row in rows} == {
        "other-extension": "catalog",
        "shared-extension": "combined",
    }


def test_catalog_reconciliation_record_hash_precedes_ordinal_for_preferred_fields() -> None:
    from specify_cli.extensions.inventory import reconcile_entries

    rows = reconcile_entries(
        (),
        (
            _catalog(name="Ordinal First", ordinal=0, record_digest="f" * 64),
            _catalog(name="Digest First", ordinal=99, record_digest="0" * 64),
        ),
    )

    assert rows[0].name == "Digest First"
    assert rows[0].conflict is True


def test_catalog_reconciliation_evidence_has_exact_privacy_allowlist() -> None:
    from specify_cli.extensions.inventory import reconcile_entries
    from specify_cli.extensions.models import serialize_entries

    rows = reconcile_entries((_installed(),), (_catalog(author="Sensitive Person"),))
    payload = json.loads(serialize_entries(rows))

    assert {item["kind"] for item in payload[0]["evidence"]} == {"local", "catalog"}
    assert all(
        set(item) == {"kind", "source_sha256", "source_ordinal", "record_sha256"} for item in payload[0]["evidence"]
    )
    encoded = serialize_entries(rows)
    assert "Sensitive Person" not in encoded
    assert "author" not in encoded
    assert "canonical" not in encoded
    assert "Catalog description." not in encoded


def test_catalog_reconciliation_conflicts_name_differing_fields_and_retains_versions() -> None:
    from specify_cli.extensions.inventory import reconcile_entries

    (row,) = reconcile_entries(
        (),
        (
            _catalog(name="Preferred", version="3.0.0", install_allowed=True, commands=2),
            _catalog(
                name="Alternate",
                version="2.0.0",
                description="Alternate private text.",
                install_allowed=False,
                commands=7,
                record_digest="5" * 64,
            ),
        ),
    )

    assert row.available_versions == ("2.0.0", "3.0.0")
    assert row.conflict is True
    assert row.health.state == "invalid"
    assert row.conflict_reasons == (
        "catalog-field-diff:description",
        "catalog-field-diff:install_allowed",
        "catalog-field-diff:name",
        "catalog-field-diff:provides",
        "duplicate-catalog-id",
    )
    assert row.install_allowed is False


def test_catalog_reconciliation_defaults_unknown_version_and_zero_capabilities() -> None:
    from specify_cli.extensions.inventory import reconcile_entries

    (row,) = reconcile_entries((), (_catalog(version=None, commands=0, hooks=0),))

    assert row.version == "unknown"
    assert row.available_versions == ("unknown",)
    assert row.provides.commands == 0
    assert row.provides.templates == 0
    assert row.provides.scripts == 0
    assert row.provides.hooks == 0
    assert row.activation_state is None
    assert row.enabled is None
    assert row.priority is None


def test_catalog_reconciliation_combined_version_mismatch_is_explicit() -> None:
    from specify_cli.extensions.inventory import reconcile_entries

    (row,) = reconcile_entries((_installed(),), (_catalog(version="2.0.0"),))

    assert row.version == "1.0.0"
    assert row.installed_version == "1.0.0"
    assert row.available_versions == ("2.0.0",)
    assert "installed-version-mismatch" in row.conflict_reasons
    assert row.health.state == "invalid"


def test_catalog_reconciliation_install_permission_fails_closed_across_candidates() -> None:
    from specify_cli.extensions.inventory import reconcile_entries

    (row,) = reconcile_entries(
        (),
        (
            _catalog(install_allowed=True),
            _catalog(install_allowed=False, ordinal=1, record_digest="6" * 64),
        ),
    )

    assert row.install_allowed is False
