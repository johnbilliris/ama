"""Tests for parameter file validation and region compliance (FR-009).

Validates that staging and production Bicep parameter files match the
expected schema, contain required parameters, and use Australian regions.

Covers: T014 (parameter validation), T015 (environment isolation)
"""

from __future__ import annotations

# ── T014: Parameter file validation ──────────────────────────────────────────


class TestParameterFileSchema:
    """Validate parameter files match the expected Bicep schema."""

    def test_staging_params_file_exists(self, staging_params_path):
        assert staging_params_path.exists(), f"Staging params not found at {staging_params_path}"

    def test_production_params_file_exists(self, production_params_path):
        assert production_params_path.exists(), f"Production params not found at {production_params_path}"

    def test_staging_params_has_schema(self, staging_params):
        assert "$schema" in staging_params, "Staging params must include $schema"

    def test_production_params_has_schema(self, production_params):
        assert "$schema" in production_params, "Production params must include $schema"

    def test_staging_schema_matches_base(self, staging_params, base_params):
        assert staging_params["$schema"] == base_params["$schema"], (
            "Staging schema must match base parameter file schema"
        )

    def test_production_schema_matches_base(self, production_params, base_params):
        assert production_params["$schema"] == base_params["$schema"], (
            "Production schema must match base parameter file schema"
        )


class TestParameterFileRequiredParams:
    """Validate both parameter files contain all required parameters."""

    REQUIRED_PARAMS = {"environmentName", "location", "principalType", "developerIpAddress"}

    def test_staging_has_required_params(self, staging_params):
        actual = set(staging_params.get("parameters", {}).keys())
        missing = self.REQUIRED_PARAMS - actual
        assert not missing, f"Staging missing required params: {missing}"

    def test_production_has_required_params(self, production_params):
        actual = set(production_params.get("parameters", {}).keys())
        missing = self.REQUIRED_PARAMS - actual
        assert not missing, f"Production missing required params: {missing}"

    def test_staging_principal_type_is_service_principal(self, staging_params):
        pt = staging_params["parameters"]["principalType"]["value"]
        assert pt == "ServicePrincipal", f"Staging principalType must be 'ServicePrincipal', got '{pt}'"

    def test_production_principal_type_is_service_principal(self, production_params):
        pt = production_params["parameters"]["principalType"]["value"]
        assert pt == "ServicePrincipal", f"Production principalType must be 'ServicePrincipal', got '{pt}'"


class TestParameterFileRegionCompliance:
    """Validate FR-009: Australian region compliance."""

    def test_staging_location_is_australian(self, staging_params, allowed_regions):
        loc = staging_params["parameters"]["location"]["value"]
        assert loc in allowed_regions, f"Staging location must be in {allowed_regions}, got '{loc}'"

    def test_production_location_is_australian(self, production_params, allowed_regions):
        loc = production_params["parameters"]["location"]["value"]
        assert loc in allowed_regions, f"Production location must be in {allowed_regions}, got '{loc}'"

    def test_staging_uses_australiaeast(self, staging_params):
        loc = staging_params["parameters"]["location"]["value"]
        assert loc == "australiaeast", f"Staging primary region must be australiaeast, got '{loc}'"

    def test_production_uses_australiaeast(self, production_params):
        loc = production_params["parameters"]["location"]["value"]
        assert loc == "australiaeast", f"Production primary region must be australiaeast, got '{loc}'"


# ── T015: Environment isolation ──────────────────────────────────────────────


class TestEnvironmentIsolation:
    """Validate staging and production environments are isolated."""

    def test_distinct_environment_names(self, staging_params, production_params):
        staging_name = staging_params["parameters"]["environmentName"]["value"]
        prod_name = production_params["parameters"]["environmentName"]["value"]
        assert staging_name != prod_name, (
            f"Staging and production must have different environmentName values, both are '{staging_name}'"
        )

    def test_staging_env_name_contains_staging(self, staging_params):
        name = staging_params["parameters"]["environmentName"]["value"]
        assert "staging" in name.lower(), f"Staging environmentName should contain 'staging', got '{name}'"

    def test_production_env_name_contains_production(self, production_params):
        name = production_params["parameters"]["environmentName"]["value"]
        assert "production" in name.lower(), f"Production environmentName should contain 'production', got '{name}'"

    def test_staging_does_not_reference_production(self, staging_params_path):
        content = staging_params_path.read_text(encoding="utf-8")
        # environmentName should not contain "production"
        assert "drh-production" not in content, "Staging params must not reference production environment name"

    def test_production_does_not_reference_staging(self, production_params_path):
        content = production_params_path.read_text(encoding="utf-8")
        assert "drh-staging" not in content, "Production params must not reference staging environment name"
