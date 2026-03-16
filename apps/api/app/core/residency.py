from dataclasses import dataclass


AUSTRALIAN_AZURE_REGIONS = {"Australia East", "Australia Southeast"}


@dataclass(frozen=True)
class ResidencyPolicy:
    allowed_regions: tuple[str, ...]

    def validate_region(self, region: str) -> None:
        if region not in self.allowed_regions:
            raise ValueError(f"Region '{region}' is not allowed for this workload")


def build_residency_policy(allowed_regions: list[str]) -> ResidencyPolicy:
    normalized = tuple(region for region in allowed_regions if region in AUSTRALIAN_AZURE_REGIONS)
    if not normalized:
        raise ValueError("At least one Australian Azure region must be configured")
    return ResidencyPolicy(allowed_regions=normalized)
