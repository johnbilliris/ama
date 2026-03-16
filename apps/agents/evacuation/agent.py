class EvacuationAgent:
    def review(self, scenario_type: str, jurisdictions: list[str]) -> dict[str, object]:
        route_pressure = "high" if scenario_type in {"flood", "bushfire"} else "moderate"
        return {
            "scenarioType": scenario_type,
            "jurisdictions": jurisdictions,
            "routePressure": route_pressure,
            "recommendation": (
                "Validate assembly areas and transport corridors before public release."
            ),
        }
