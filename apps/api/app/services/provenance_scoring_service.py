class ProvenanceScoringService:
    AUTHORITY_BASELINE = {
        "authoritative": 0.95,
        "sensor": 0.8,
        "iot": 0.75,
        "field_report": 0.7,
        "community": 0.55,
        "social": 0.45,
        "derived": 0.65,
    }

    def score(self, source_kind: str, freshness_score: float, confidence_score: float) -> float:
        baseline = self.AUTHORITY_BASELINE.get(source_kind, 0.4)
        return round((baseline + freshness_score + confidence_score) / 3, 3)
