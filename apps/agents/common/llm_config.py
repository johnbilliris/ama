"""Shared LLM configuration — Microsoft Foundry only (post-cutover).

ADR-20 §Q-P6-03 cleanup: the per-agent canary cutover (FR-RAG-FM-06) is
complete; the legacy ``LEGACY_AZURE_OPENAI=1`` rollback flag has been
removed and the configuration now reads exclusively from the
``AZURE_AI_PROJECT_*`` env vars. The legacy ``AZURE_OPENAI_*`` env vars
remain readable as a hermetic-test seam (unit tests inject ad-hoc
endpoints without provisioning Foundry) but are NEVER set in production
Bicep — the API and Agents container apps only see ``AZURE_AI_PROJECT_*``.

All configurable parameters are consolidated per data-model.md §LLMClientConfig.
Values are read once at construction and frozen for the lifetime of the process.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import InitVar, dataclass, field, replace
from enum import StrEnum
from urllib.parse import unquote, urlsplit


class FoundryConfigurationError(RuntimeError):
    """Hard misconfiguration, never a transport retry or a silent empty response.

    Callers retain their existing marked template/error boundary.
    """


def normalize_foundry_endpoint(endpoint: str) -> str:
    """Keep account identity independent of a legacy AOAI deployment-qualified URL."""
    value = endpoint.strip()
    diagnostic = (
        "AZURE_AI_PROJECT_ENDPOINT must be an HTTPS account/project endpoint "
        "without credentials, query or fragment; AOAI may include /openai/deployments/<name>"
    )
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise FoundryConfigurationError(diagnostic) from exc
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or any(character.isspace() for character in value)
        or port == 0
    ):
        raise FoundryConfigurationError(diagnostic)
    if host.endswith((".cognitiveservices.azure.com", ".openai.azure.com")):
        path = parsed.path.rstrip("/")
        if path:
            parts = path.split("/")
            if (
                len(parts) != 4
                or parts[:3] != ["", "openai", "deployments"]
                or not parts[3]
                or unquote(parts[3]) in (".", "..")
                or any(character in unquote(parts[3]) for character in "/?#")
            ):
                raise FoundryConfigurationError(diagnostic)
            return parsed._replace(path="").geturl()
    return value


class OperationalTier(StrEnum):
    """Chat purpose, independent of model identity and embedding lookup."""

    REASONING = "reasoning"
    DRAFTING = "drafting"
    SIMULATION = "simulation"


class MetadataSource(StrEnum):
    CONFIGURED = "configured"
    LEGACY_COORDINATE = "legacy_coordinate"
    UNAVAILABLE = "unavailable"


class ResolutionSource(StrEnum):
    EXPLICIT_TIER = "explicit_tier"
    TIER_ALIAS = "tier_alias"
    LEGACY_EXACT = "legacy_exact"
    LEGACY_BASE = "legacy_base"


def _require_non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class ModelIdentity:
    """Configured provider identity; versions remain opaque and unmodified."""

    model_id: str
    model_version: str

    def __post_init__(self) -> None:
        _require_non_empty(self.model_id, "model_id")
        _require_non_empty(self.model_version, "model_version")

    @property
    def model_key(self) -> str:
        return f"{self.model_id}@{self.model_version}"


@dataclass(frozen=True)
class DeploymentIdentity:
    """Baseline identity supplied by approved evidence, never inferred defaults."""

    account_resource_id: str
    deployment_name: str
    model: ModelIdentity
    region: str
    sku: str
    capacity: int
    rai_policy_name: str
    access_controls: str
    version_upgrade_option: str | None

    def __post_init__(self) -> None:
        _require_non_empty(self.deployment_name, "deployment_name")
        if type(self.capacity) is not int or self.capacity <= 0:
            raise ValueError("capacity must be a positive integer")


@dataclass(frozen=True)
class TierConfiguration:
    """Source-preserving tier settings; legacy identity waits for a destination."""

    tier: OperationalTier
    configuration_revision: str
    deployment_name: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    legacy_model_key: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "tier", OperationalTier(self.tier))
        _require_non_empty(self.configuration_revision, "configuration_revision")
        prefix = f"AZURE_AI_{self.tier.value.upper()}"
        for suffix, value in (
            ("DEPLOYMENT", self.deployment_name),
            ("MODEL_ID", self.model_id),
            ("MODEL_VERSION", self.model_version),
            ("MODEL_KEY", self.legacy_model_key),
        ):
            if value is not None:
                _require_non_empty(value, f"{prefix}_{suffix}")
        if (self.model_id is None) != (self.model_version is None):
            raise ValueError(f"{prefix}_MODEL_ID and {prefix}_MODEL_VERSION must be supplied together")
        if self.model is not None and self.legacy_model_key is not None:
            if self.legacy_model_key != self.model.model_key:
                raise ValueError(f"{prefix}_MODEL_KEY must agree with MODEL_ID@MODEL_VERSION")

    @property
    def model(self) -> ModelIdentity | None:
        if self.model_id is None or self.model_version is None:
            return None
        return ModelIdentity(self.model_id, self.model_version)

    @property
    def metadata_source(self) -> MetadataSource:
        return MetadataSource.CONFIGURED if self.model is not None else MetadataSource.UNAVAILABLE

    @classmethod
    def from_settings(
        cls, tier: OperationalTier, settings: Mapping[str, str], *, configuration_revision: str
    ) -> TierConfiguration:
        """Read one tier's source-preserving fields from an already captured environment."""
        prefix = f"AZURE_AI_{tier.value.upper()}"
        return cls(
            tier=tier,
            configuration_revision=configuration_revision,
            deployment_name=settings.get(f"{prefix}_DEPLOYMENT"),
            model_id=settings.get(f"{prefix}_MODEL_ID"),
            model_version=settings.get(f"{prefix}_MODEL_VERSION"),
            legacy_model_key=settings.get(f"{prefix}_MODEL_KEY"),
        )


@dataclass(frozen=True)
class LegacyRoutingEntry:
    """A validated routing pair, retaining its one-based source position."""

    routing_key: str
    deployment_name: str
    source_position: int

    def __post_init__(self) -> None:
        _require_non_empty(self.routing_key, "routing_key")
        _require_non_empty(self.deployment_name, "deployment_name")
        if self.routing_key != self.routing_key.strip() or self.deployment_name != self.deployment_name.strip():
            raise ValueError("Legacy routing keys and destinations must be trimmed")


def _validated_entries(pairs: Iterable[tuple[str, str]], *, source: str) -> tuple[LegacyRoutingEntry, ...]:
    entries: list[LegacyRoutingEntry] = []
    for position, (key, destination) in enumerate(pairs, start=1):
        if not isinstance(key, str) or not key.strip() or not isinstance(destination, str) or not destination.strip():
            raise FoundryConfigurationError(f"{source} entry {position}: routing key and destination must be non-empty")
        key, destination = key.strip(), destination.strip()
        previous = next((entry for entry in entries if entry.routing_key == key), None)
        if previous is not None:
            if previous.deployment_name != destination:
                raise FoundryConfigurationError(
                    f"{source}: conflicting routing key {key!r} designates both "
                    f"{previous.deployment_name!r} and {destination!r}; configure one destination per key "
                    "and use explicit AZURE_AI_<TIER>_DEPLOYMENT settings for shared model coordinates"
                )
            continue
        entries.append(LegacyRoutingEntry(key, destination, position))
    return tuple(entries)


def parse_deployment_entries(raw: str | None) -> tuple[LegacyRoutingEntry, ...]:
    """Validate raw CSV before discarding duplicates or constructing a lookup."""
    source = "AZURE_AI_PROJECT_DEPLOYMENTS"
    if raw is None:
        return ()
    if not isinstance(raw, str):
        raise FoundryConfigurationError(f"{source} must be a CSV string")
    if not raw.strip():
        return ()
    pairs: list[tuple[str, str]] = []
    for position, entry in enumerate(raw.split(","), start=1):
        if entry.count("=") != 1:
            raise FoundryConfigurationError(
                f"{source} entry {position}: expected one non-empty routing-key=deployment-name pair"
            )
        key, destination = entry.split("=")
        pairs.append((key, destination))
    return _validated_entries(pairs, source=source)


def parse_deployment_map(raw: str | None) -> dict[str, str]:
    """Return a compatibility lookup only after raw conflicts and malformed pairs fail."""
    return {entry.routing_key: entry.deployment_name for entry in parse_deployment_entries(raw)}


@dataclass(frozen=True)
class RoutingConfiguration:
    """Opt-in snapshot; legacy consumers do not activate validation by constructing LLMClientConfig."""

    endpoint: str | None
    region: str | None
    raw_deployments: str | None
    tiers: tuple[TierConfiguration, ...]
    configuration_revision: str
    verification_reference: str | None = None
    legacy_entries: tuple[LegacyRoutingEntry, ...] | None = None
    tier_errors: tuple[tuple[OperationalTier, str], ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty(self.configuration_revision, "configuration_revision")
        object.__setattr__(self, "tiers", tuple(self.tiers))
        object.__setattr__(self, "tier_errors", tuple(self.tier_errors))
        if self.legacy_entries is not None:
            object.__setattr__(self, "legacy_entries", tuple(self.legacy_entries))
        if len(self.tiers) != len(OperationalTier) or {item.tier for item in self.tiers} != set(OperationalTier):
            raise ValueError("RoutingConfiguration requires each chat tier exactly once")
        if any(item.configuration_revision != self.configuration_revision for item in self.tiers):
            raise ValueError("Tier configuration revisions must match the routing snapshot")

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
        *,
        configuration_revision: str,
        verification_reference: str | None = None,
    ) -> RoutingConfiguration:
        """Copy sources once, retaining None for absence and raw CSV for later validation."""
        settings = dict(os.environ if environment is None else environment)
        tiers = tuple(
            TierConfiguration.from_settings(tier, settings, configuration_revision=configuration_revision)
            for tier in OperationalTier
        )
        return cls(
            endpoint=settings.get("AZURE_AI_PROJECT_ENDPOINT"),
            region=settings.get("AZURE_AI_PROJECT_REGION"),
            raw_deployments=settings.get("AZURE_AI_PROJECT_DEPLOYMENTS"),
            tiers=tiers,
            configuration_revision=configuration_revision,
            verification_reference=verification_reference,
        )

    def tier_configuration(self, tier: OperationalTier) -> TierConfiguration:
        """Look up a chat tier without rereading the environment or choosing a destination."""
        requested = OperationalTier(tier)
        return next(item for item in self.tiers if item.tier == requested)


@dataclass(frozen=True)
class LegacyMetadataAssociation:
    """Association supplied by a validated same-account map or bound verification evidence.

    Construction does not validate a CSV or perform preflight. The later resolver
    owns that evidence; this type only prevents its reuse for another target/revision.
    """

    endpoint: str
    deployment_name: str
    configuration_revision: str
    model_id: str
    reference: str
    model_version: str | None = None

    def __post_init__(self) -> None:
        for name in ("endpoint", "deployment_name", "configuration_revision", "model_id", "reference"):
            _require_non_empty(getattr(self, name), name)
        if self.model_version is not None:
            _require_non_empty(self.model_version, "model_version")


@dataclass(frozen=True)
class ResolvedDeployment:
    """Request target and available identity, not proof of inference submission."""

    tier: OperationalTier | None
    endpoint: str
    deployment_name: str
    resolution_source: ResolutionSource
    configuration_revision: str
    model_id: str | None = None
    model_version: str | None = None
    metadata_source: MetadataSource = MetadataSource.UNAVAILABLE
    verification_reference: str | None = None
    metadata_association: LegacyMetadataAssociation | None = None

    def __post_init__(self) -> None:
        if self.tier is not None:
            object.__setattr__(self, "tier", OperationalTier(self.tier))
        object.__setattr__(self, "resolution_source", ResolutionSource(self.resolution_source))
        object.__setattr__(self, "metadata_source", MetadataSource(self.metadata_source))
        for name in ("endpoint", "deployment_name", "configuration_revision"):
            _require_non_empty(getattr(self, name), name)
        for name in ("model_id", "model_version"):
            value = getattr(self, name)
            if value is not None:
                _require_non_empty(value, name)
        if self.model_version is not None and self.model_id is None:
            raise ValueError("model_version requires model_id")
        if self.metadata_source is MetadataSource.CONFIGURED:
            if self.model_id is None or self.model_version is None:
                raise ValueError("Configured identity requires model_id and model_version")
        elif self.metadata_source is MetadataSource.UNAVAILABLE:
            if self.model_id is not None or self.model_version is not None:
                raise ValueError("Unavailable metadata cannot claim a model identity")
        else:
            association = self.metadata_association
            if association is None or not self._matches_association(association):
                raise ValueError("Legacy identity requires a destination/account/config-bound association")
            if (self.model_id, self.model_version) != (association.model_id, association.model_version):
                raise ValueError("Legacy identity must agree with its association")
        if self.metadata_association is not None and self.metadata_source is not MetadataSource.LEGACY_COORDINATE:
            raise ValueError("Only legacy identity may carry a legacy metadata association")

    @property
    def metadata_association_reference(self) -> str | None:
        return self.metadata_association.reference if self.metadata_association is not None else None

    def _matches_association(self, association: LegacyMetadataAssociation) -> bool:
        return (
            self.endpoint == association.endpoint
            and self.deployment_name == association.deployment_name
            and self.configuration_revision == association.configuration_revision
        )

    def with_legacy_metadata(self, association: LegacyMetadataAssociation) -> ResolvedDeployment:
        """Admit only proven same-target metadata; never change the destination."""
        if self.metadata_source is not MetadataSource.UNAVAILABLE or not self._matches_association(association):
            return self
        return replace(
            self,
            model_id=association.model_id,
            model_version=association.model_version,
            metadata_source=MetadataSource.LEGACY_COORDINATE,
            metadata_association=association,
        )


@dataclass(frozen=True)
class DeploymentResolver:
    """Pure, immutable routing snapshot; no environment reads during resolution.

    ``from_environment`` retains tier errors until the affected path is used.
    Direct typed construction retains the foundation types' ValueError checks.
    Injected maps are copied and validated, never a bypass for an invalid raw map.
    """

    configuration: RoutingConfiguration
    deployments: InitVar[Mapping[str, str] | None] = None
    _entries: tuple[LegacyRoutingEntry, ...] = field(init=False, repr=False)

    def __post_init__(self, deployments: Mapping[str, str] | None) -> None:
        entries = parse_deployment_entries(self.configuration.raw_deployments)
        if self.configuration.legacy_entries is not None:
            entries = _validated_entries(
                (
                    (entry.routing_key, entry.deployment_name)
                    for entry in (*entries, *self.configuration.legacy_entries)
                ),
                source="AZURE_AI_PROJECT_DEPLOYMENTS / legacy_entries",
            )
        if deployments is not None:
            entries = _validated_entries(deployments.items(), source="injected deployments")
        object.__setattr__(self, "_entries", entries)

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
        *,
        configuration_revision: str,
        verification_reference: str | None = None,
        deployments: Mapping[str, str] | None = None,
    ) -> DeploymentResolver:
        """Capture settings once; global map errors fail now, tier errors fail on use."""
        settings = dict(os.environ if environment is None else environment)
        tiers: list[TierConfiguration] = []
        errors: list[tuple[OperationalTier, str]] = []
        try:
            _require_non_empty(configuration_revision, "configuration_revision")
            for tier in OperationalTier:
                try:
                    tiers.append(
                        TierConfiguration.from_settings(tier, settings, configuration_revision=configuration_revision)
                    )
                except ValueError as exc:
                    errors.append((tier, str(exc)))
                    tiers.append(TierConfiguration(tier, configuration_revision))
            configuration = RoutingConfiguration(
                endpoint=settings.get("AZURE_AI_PROJECT_ENDPOINT"),
                region=settings.get("AZURE_AI_PROJECT_REGION"),
                raw_deployments=settings.get("AZURE_AI_PROJECT_DEPLOYMENTS"),
                tiers=tuple(tiers),
                tier_errors=tuple(errors),
                configuration_revision=configuration_revision,
                verification_reference=verification_reference,
            )
        except ValueError as exc:
            raise FoundryConfigurationError(str(exc)) from exc
        return cls(configuration, deployments=deployments)

    def _endpoint(self) -> str:
        for name, value in (
            ("AZURE_AI_PROJECT_ENDPOINT", self.configuration.endpoint),
            ("AZURE_AI_PROJECT_REGION", self.configuration.region),
        ):
            if value is None or not value.strip():
                raise FoundryConfigurationError(f"{name} must be configured and non-empty before resolving deployment")
        assert self.configuration.endpoint is not None
        return normalize_foundry_endpoint(self.configuration.endpoint)

    def _entry_for(self, key: str) -> LegacyRoutingEntry | None:
        return next((entry for entry in self._entries if entry.routing_key == key), None)

    def _legacy_destination(self, key: str) -> tuple[str, ResolutionSource]:
        exact = self._entry_for(key)
        if exact is not None:
            return exact.deployment_name, ResolutionSource.LEGACY_EXACT
        base = self._entry_for(key.split("@", 1)[0])
        if base is not None:
            return base.deployment_name, ResolutionSource.LEGACY_BASE
        raise FoundryConfigurationError(
            f"no Foundry deployment configured for {key!r}; set an unambiguous exact or base key in "
            "AZURE_AI_PROJECT_DEPLOYMENTS (routing-key=deployment-name)"
        )

    @staticmethod
    def _metadata_key(configuration: TierConfiguration) -> str | None:
        if configuration.legacy_model_key is not None:
            return configuration.legacy_model_key.strip()
        return configuration.model.model_key if configuration.model is not None else None

    def _tier_destination(self, tier: OperationalTier) -> tuple[str, ResolutionSource]:
        for invalid_tier, diagnostic in self.configuration.tier_errors:
            if invalid_tier is tier:
                raise FoundryConfigurationError(diagnostic)
        configuration = self.configuration.tier_configuration(tier)
        setting = f"AZURE_AI_{tier.value.upper()}_DEPLOYMENT"
        if configuration.deployment_name is not None:
            if not configuration.deployment_name.strip():
                raise FoundryConfigurationError(f"{setting} must be non-empty")
            return configuration.deployment_name.strip(), ResolutionSource.EXPLICIT_TIER
        if tier is OperationalTier.SIMULATION:
            raise FoundryConfigurationError(f"{setting} is required for simulation; legacy fallback is not allowed")
        alias = self._entry_for(tier.value)
        if alias is not None:
            return alias.deployment_name, ResolutionSource.TIER_ALIAS
        key = self._metadata_key(configuration)
        if key is not None:
            try:
                return self._legacy_destination(key)
            except FoundryConfigurationError as exc:
                raise FoundryConfigurationError(f"{tier.value}: {exc}; or set {setting}") from exc
        raise FoundryConfigurationError(
            f"{tier.value}: set {setting}, a tier alias in AZURE_AI_PROJECT_DEPLOYMENTS, "
            f"or AZURE_AI_{tier.value.upper()}_MODEL_KEY with an unambiguous configured mapping"
        )

    def resolve(
        self,
        tier: OperationalTier | str,
        *,
        metadata_association: LegacyMetadataAssociation | None = None,
    ) -> ResolvedDeployment:
        """Resolve a chat purpose, checking simulation against both effective live paths."""
        try:
            purpose = OperationalTier(tier)
        except ValueError as exc:
            raise FoundryConfigurationError(
                f"Unsupported chat tier {tier!r}; expected reasoning, drafting or simulation"
            ) from exc
        endpoint = self._endpoint()
        destination, source = self._tier_destination(purpose)
        if purpose is OperationalTier.SIMULATION:
            for live in (OperationalTier.REASONING, OperationalTier.DRAFTING):
                try:
                    live_destination, _ = self._tier_destination(live)
                except FoundryConfigurationError as exc:
                    raise FoundryConfigurationError(
                        f"simulation isolation requires a resolvable {live.value} deployment in this account: {exc}"
                    ) from exc
                if destination == live_destination:
                    raise FoundryConfigurationError(
                        f"simulation deployment {destination!r} must be distinct from {live.value} "
                        "in the same account; change AZURE_AI_SIMULATION_DEPLOYMENT or the affected live routing"
                    )
        configuration = self.configuration.tier_configuration(purpose)
        model = configuration.model
        resolved = ResolvedDeployment(
            tier=purpose,
            endpoint=endpoint,
            deployment_name=destination,
            resolution_source=source,
            configuration_revision=self.configuration.configuration_revision,
            model_id=model.model_id if model is not None else None,
            model_version=model.model_version if model is not None else None,
            metadata_source=configuration.metadata_source,
            verification_reference=self.configuration.verification_reference,
        )
        return self._associate_metadata(resolved, self._metadata_key(configuration), metadata_association)

    def resolve_legacy(self, model_key: str) -> ResolvedDeployment:
        """Keep unambiguous exact/base and embedding lookup outside the chat-tier API."""
        if not isinstance(model_key, str) or not model_key.strip():
            raise FoundryConfigurationError("Legacy model_key must be a non-empty configured routing key")
        key = model_key.strip()
        if key in OperationalTier:
            return self.resolve(key)
        endpoint = self._endpoint()
        destination, source = self._legacy_destination(key)
        resolved = ResolvedDeployment(
            tier=None,
            endpoint=endpoint,
            deployment_name=destination,
            resolution_source=source,
            configuration_revision=self.configuration.configuration_revision,
            verification_reference=self.configuration.verification_reference,
        )
        return self._associate_metadata(resolved, key, None)

    def _associate_metadata(
        self,
        resolved: ResolvedDeployment,
        key: str | None,
        proof: LegacyMetadataAssociation | None,
    ) -> ResolvedDeployment:
        if resolved.metadata_source is not MetadataSource.UNAVAILABLE:
            return resolved
        if key is not None:
            for candidate in dict.fromkeys((key, key.split("@", 1)[0])):
                entry = self._entry_for(candidate)
                if entry is None or entry.deployment_name != resolved.deployment_name:
                    continue
                model_id, separator, version = candidate.partition("@")
                if not model_id or (separator and not version):
                    continue
                association = LegacyMetadataAssociation(
                    endpoint=resolved.endpoint,
                    deployment_name=resolved.deployment_name,
                    configuration_revision=resolved.configuration_revision,
                    model_id=model_id,
                    model_version=version if separator else None,
                    reference=f"{resolved.configuration_revision}:validated-routing-map:entry-{entry.source_position}",
                )
                return resolved.with_legacy_metadata(association)
        return resolved.with_legacy_metadata(proof) if proof is not None else resolved


@dataclass(frozen=True)
class LLMClientConfig:
    """Immutable LLM configuration read from environment variables with sensible defaults.

    Spec 036 / ADR-20 hard cutover: the chat plane is Microsoft Foundry only,
    surfaced via ``AZURE_AI_PROJECT_ENDPOINT`` + ``AZURE_AI_PROJECT_DEPLOYMENTS``
    (CSV of ``modelId@version=deploymentName``) per
    ``apps/eval-runner/src/ama_eval/foundry_client.py``.

    The ``AZURE_OPENAI_*`` env vars are RETAINED here purely as a hermetic
    test seam — unit tests can inject a synthetic endpoint without
    provisioning Foundry. Production Bicep (``infra/main.bicep``) does
    NOT set these variables on the API or Agents container apps.
    """

    # ───────── Test-only fallback (production sets AZURE_AI_PROJECT_* only) ─────────
    endpoint: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT", ""))
    reasoning_deployment: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_REASONING_DEPLOYMENT", ""))
    drafting_deployment: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_DRAFTING_DEPLOYMENT", ""))
    api_version: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"))

    # ───────── Spec 036 — Foundry connection (FR-RAG-FM-01, R-01) ─────────
    foundry_endpoint: str = field(default_factory=lambda: os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""))
    foundry_deployments: str = field(default_factory=lambda: os.getenv("AZURE_AI_PROJECT_DEPLOYMENTS", ""))
    foundry_region: str = field(default_factory=lambda: os.getenv("AZURE_AI_PROJECT_REGION", "australiaeast"))

    # Model parameters
    model_tier: str = field(default_factory=lambda: os.getenv("LLM_MODEL_TIER", "drafting"))
    temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))
    max_input_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_INPUT_TOKENS", "4000")))
    max_output_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2000")))

    # Retry & circuit breaker
    retry_attempts: int = field(default_factory=lambda: int(os.getenv("LLM_RETRY_ATTEMPTS", "3")))
    retry_min_wait: float = field(default=1.0)
    retry_max_wait: float = field(default=4.0)
    timeout_seconds: float = field(default_factory=lambda: float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0")))
    circuit_breaker_failure_threshold: int = field(
        default_factory=lambda: int(os.getenv("LLM_CB_FAILURE_THRESHOLD", "3"))
    )
    circuit_breaker_recovery_timeout: float = field(
        default_factory=lambda: float(os.getenv("LLM_CB_RECOVERY_TIMEOUT", "30.0"))
    )

    # Confidence
    confidence_threshold: float = field(default_factory=lambda: float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.7")))
    fallback_reduction_factor: float = field(
        default_factory=lambda: float(os.getenv("LLM_FALLBACK_REDUCTION_FACTOR", "0.5"))
    )

    # Cost tracking
    monthly_budget_usd: float = field(default_factory=lambda: float(os.getenv("LLM_MONTHLY_BUDGET_USD", "50.0")))
    _routing_environment: tuple[tuple[str, str], ...] = field(init=False, repr=False)
    foundry_configured: bool = field(init=False)

    def __post_init__(self) -> None:
        """Validate configuration values immediately after construction."""
        settings = {key: value for key, value in os.environ.items() if key.startswith("AZURE_AI_")}
        object.__setattr__(
            self,
            "foundry_configured",
            bool(
                "AZURE_AI_PROJECT_ENDPOINT" in settings
                or self.foundry_endpoint
                or self.foundry_deployments
                or any(
                    key.startswith(f"AZURE_AI_{tier.value.upper()}_") for tier in OperationalTier for key in settings
                )
            ),
        )
        settings["AZURE_AI_PROJECT_ENDPOINT"] = self.foundry_endpoint
        settings["AZURE_AI_PROJECT_DEPLOYMENTS"] = self.foundry_deployments
        # Retain absent region information instead of silently authorising a gateway bypass.
        if "AZURE_AI_PROJECT_REGION" in settings or self.foundry_region != "australiaeast":
            settings["AZURE_AI_PROJECT_REGION"] = self.foundry_region
        object.__setattr__(self, "_routing_environment", tuple(settings.items()))
        if self.endpoint:
            hostname = self.endpoint.lower()
            # Azure OpenAI endpoints use format: https://<resource>.openai.azure.com/
            # The resource name doesn't contain the region, so we validate the
            # endpoint is a valid Azure OpenAI URL rather than checking for region
            # in the hostname. Region compliance is enforced by Bicep IaC (FR-009).
            if not (
                hostname.startswith("https://")
                and ("openai.azure.com" in hostname or "cognitiveservices.azure.com" in hostname)
            ):
                raise ValueError(
                    f"AZURE_OPENAI_ENDPOINT must be a valid Azure OpenAI URL "
                    f"(https://<resource>.openai.azure.com or .cognitiveservices.azure.com), got: {self.endpoint}"
                )
        if self.model_tier not in ("reasoning", "drafting"):
            raise ValueError(f"Invalid LLM_MODEL_TIER: {self.model_tier}")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"LLM_TEMPERATURE must be 0.0–2.0, got {self.temperature}")
        if self.max_input_tokens <= 0 or self.max_input_tokens > 200000:
            raise ValueError(f"LLM_MAX_INPUT_TOKENS must be 1–200000, got {self.max_input_tokens}")
        if self.max_output_tokens <= 0 or self.max_output_tokens > 16384:
            raise ValueError(f"LLM_MAX_OUTPUT_TOKENS must be 1–16384, got {self.max_output_tokens}")
        if not (0.0 <= self.confidence_threshold <= 1.0):
            raise ValueError(f"LLM_CONFIDENCE_THRESHOLD must be 0.0–1.0, got {self.confidence_threshold}")
        if not (0.0 <= self.fallback_reduction_factor <= 1.0):
            raise ValueError(f"LLM_FALLBACK_REDUCTION_FACTOR must be 0.0–1.0, got {self.fallback_reduction_factor}")
        if self.monthly_budget_usd <= 0:
            raise ValueError(f"LLM_MONTHLY_BUDGET_USD must be > 0, got {self.monthly_budget_usd}")

    def deployment_for(self, purpose: str) -> str:
        """Return the deployment name for the given purpose."""
        if purpose == "reasoning":
            return self.reasoning_deployment
        if purpose == "drafting":
            return self.drafting_deployment
        raise ValueError(f"Unknown LLM purpose: {purpose!r}. Must be 'reasoning' or 'drafting'.")

    # Spec 036 (T021) — return the Foundry deployment **map** for the
    # constructor-injectable seam (FR-RAG-FM-07). The CSV format mirrors
    # apps/eval-runner/src/ama_eval/foundry_client._parse_deployment_map.
    def foundry_deployment_map(self) -> dict[str, str]:
        """Validate raw compatibility pairs before creating the injectable lookup."""
        return parse_deployment_map(self.foundry_deployments)

    def deployment_resolver(self, *, allow_test_endpoint: bool = False) -> DeploymentResolver:
        """Validate and resolve from the captured settings, never the current environment."""
        settings = dict(self._routing_environment)
        if allow_test_endpoint and not self.foundry_configured and self.endpoint:
            settings["AZURE_AI_PROJECT_ENDPOINT"] = self.endpoint
            settings.setdefault("AZURE_AI_PROJECT_REGION", self.foundry_region)
            for tier, deployment in (
                (OperationalTier.REASONING, self.reasoning_deployment),
                (OperationalTier.DRAFTING, self.drafting_deployment),
            ):
                if deployment:
                    settings[f"AZURE_AI_{tier.value.upper()}_DEPLOYMENT"] = deployment
        return DeploymentResolver.from_environment(settings, configuration_revision="llm-client-snapshot")

    def foundry_model_key_for(self, purpose: str) -> str:
        """Return the chat-purpose selector; model coordinates do not select a tier."""
        try:
            return OperationalTier(purpose).value
        except ValueError as exc:
            raise FoundryConfigurationError(f"Unsupported chat tier {purpose!r}") from exc
