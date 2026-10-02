---
purpose: Documents the data exchange protocols and lead-agency designation rules at each cross-sector boundary for NSW RFS, VIC CFA, SES, Health, Transport, and Utilities personas.
personas:
  - Sector
diagrams:
  - SECTOR-05
specs:
  - spec-015
  - spec-022
---

# SECTOR-05 — Cross-Sector Touchpoints

[→ Architecture index](../README.md)

![SECTOR-05: Cross-Sector Touchpoints](cross-sector-touchpoints.png)

<!-- spec-cross-ref: spec-015 -->
<!-- spec-cross-ref: spec-022 -->

This view documents bidirectional data exchanges and lead-agency designation rules at each cross-sector boundary for Fire, SES/Flood, Health, Transport, Utilities, and supporting partner sectors.

The lead-agency examples are policy/documentation guidance, not proof that every external exchange is wired in the current deployment. Implemented jurisdiction routing is hazard- and agency-hint-dependent; see `apps/api/app/services/simulation/jurisdiction_routing.py` and SECTOR-04.

## Touchpoint Reference

| Sector Pair | Data Format | Lead-Agency Rule | Spec Citation |
| --- | --- | --- | --- |
| Fire (RFS/CFA) ↔ AMA Hub | CAP, EDXL-DE, GeoJSON | Fire lead during suppression hazards; handover when hazard class changes | spec-022 |
| SES/Flood ↔ AMA Hub | CAP, EDXL-DE, GeoJSON | SES lead for flood/storm response and evacuation routing | spec-022 |
| Health ↔ AMA Hub | EDXL-HAVE, REST | Health authority lead for casualty and public-health advisories | spec-015 |
| Transport ↔ AMA Hub | REST, GeoJSON | Transport lead for corridor closures and re-entry routing | spec-015 |
| Utilities ↔ AMA Hub | REST, EDXL, GeoJSON | Utility operator lead for network restoration and outage constraints | spec-015 |
| Local Government ↔ AMA Hub | REST, GeoJSON | Local government lead for welfare coordination during recovery | spec-022 |

## FR Notes

- **FR-015**: Cross-sector integration touchpoints documented with protocol labels and lead-agency designation rules.

## Related Pages

- [Architecture index](../README.md)
- [SECTOR-04 — Jurisdiction-Filter Behaviour](jurisdiction-filter.md)
- [SECTOR-01 — Multi-Jurisdiction Tenancy](multi-jurisdiction-tenancy.md)
