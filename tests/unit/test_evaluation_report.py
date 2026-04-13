"""Unit tests for EvaluationReport domain model.

Tests: report creation, period validation, AI-assisted safety requirement,
domain findings keys, severity levels, recommendations, dissemination.
"""
import pytest
from datetime import datetime, timedelta, UTC

from packages.domain.src.domain.models.evaluation_report import (
    EvaluationReport,
    Finding,
    DomainFinding,
    Recommendation,
    DisseminationRecord,
    EvaluationDomain,
)


class TestFinding:
    def test_valid_finding_positive(self):
        f = Finding(
            finding_text="Community engagement exceeded targets",
            evidence_summary="Survey response rate 89%",
            severity="positive",
        )
        assert f.severity == "positive"
        assert f.related_indicator_ids == []

    def test_finding_with_related_indicators(self):
        f = Finding(
            finding_text="Health outcomes below baseline",
            evidence_summary="Hospital data Q3",
            severity="concern",
            related_indicator_ids=["ind-1", "ind-2"],
        )
        assert len(f.related_indicator_ids) == 2

    @pytest.mark.parametrize("severity", ["positive", "neutral", "concern", "critical"])
    def test_all_severity_levels(self, severity):
        f = Finding(
            finding_text="Test finding",
            evidence_summary="Test evidence",
            severity=severity,
        )
        assert f.severity == severity

    def test_finding_critical_severity(self):
        f = Finding(
            finding_text="Major governance failure identified",
            evidence_summary="Audit report findings",
            severity="critical",
        )
        assert f.severity == "critical"


class TestDomainFinding:
    def test_valid_domain_finding(self):
        df = DomainFinding(
            evaluation_domain="governance",
            questions_addressed=["Were governance structures effective?"],
            findings=[
                Finding(
                    finding_text="Governance was effective",
                    evidence_summary="Meeting records",
                    severity="positive",
                ),
            ],
        )
        assert df.evaluation_domain == "governance"
        assert len(df.questions_addressed) == 1
        assert len(df.findings) == 1

    def test_domain_finding_with_evidence_references(self):
        df = DomainFinding(
            evaluation_domain="effectiveness",
            evidence_references=["report-2024-01.pdf", "survey-results.csv"],
        )
        assert len(df.evidence_references) == 2

    @pytest.mark.parametrize("domain", [
        "governance", "community_engagement", "effectiveness",
        "efficiency", "implementation",
    ])
    def test_all_evaluation_domains_valid(self, domain):
        df = DomainFinding(evaluation_domain=domain)
        assert df.evaluation_domain == domain

    def test_domain_finding_empty_findings_list(self):
        df = DomainFinding(evaluation_domain="efficiency")
        assert df.findings == []
        assert df.questions_addressed == []


class TestRecommendation:
    def test_valid_recommendation(self):
        rec = Recommendation(
            text="Increase community liaison officer hours",
            priority="high",
        )
        assert rec.priority == "high"
        assert rec.target_domain is None
        assert rec.suggested_activity_ids == []

    def test_recommendation_with_target_domain(self):
        rec = Recommendation(
            text="Rebuild community centre",
            priority="medium",
            target_domain="built",
        )
        assert rec.target_domain == "built"

    def test_recommendation_with_suggested_activities(self):
        rec = Recommendation(
            text="Implement mental health support",
            priority="high",
            target_domain="social",
            suggested_activity_ids=["aidr:social:mental-health:act:1", "aidr:social:mental-health:act:2"],
        )
        assert len(rec.suggested_activity_ids) == 2

    @pytest.mark.parametrize("priority", ["high", "medium", "low"])
    def test_all_priority_levels_valid(self, priority):
        rec = Recommendation(text="Test", priority=priority)
        assert rec.priority == priority


class TestDisseminationRecord:
    def test_valid_dissemination_record(self):
        dr = DisseminationRecord(
            recipient="State Emergency Management",
            recipient_type="government",
            disseminated_at=datetime.now(UTC),
            format="pdf",
        )
        assert dr.format == "pdf"
        assert dr.recipient_type == "government"

    @pytest.mark.parametrize("fmt", ["pdf", "json", "presentation"])
    def test_all_formats_valid(self, fmt):
        dr = DisseminationRecord(
            recipient="Test",
            recipient_type="community",
            disseminated_at=datetime.now(UTC),
            format=fmt,
        )
        assert dr.format == fmt

    @pytest.mark.parametrize("rtype", ["government", "community", "ngo", "research"])
    def test_all_recipient_types_valid(self, rtype):
        dr = DisseminationRecord(
            recipient="Test",
            recipient_type=rtype,
            disseminated_at=datetime.now(UTC),
            format="pdf",
        )
        assert dr.recipient_type == rtype


class TestEvaluationReport:
    @pytest.fixture()
    def base_kwargs(self) -> dict:
        now = datetime.now(UTC)
        return {
            "report_id": "er-1",
            "framework_id": "me-1",
            "incident_id": "inc-1",
            "evaluation_period_start": now - timedelta(days=90),
            "evaluation_period_end": now,
        }

    def test_valid_report_creation(self, base_kwargs):
        report = EvaluationReport(**base_kwargs)
        assert report.report_id == "er-1"
        assert report.generated_by == "manual"
        assert report.content_safety_result is None

    def test_period_end_must_be_after_start(self, base_kwargs):
        base_kwargs["evaluation_period_end"] = base_kwargs["evaluation_period_start"] - timedelta(days=1)
        with pytest.raises(ValueError, match="evaluation_period_end must be after"):
            EvaluationReport(**base_kwargs)

    def test_period_end_equal_to_start_raises(self, base_kwargs):
        base_kwargs["evaluation_period_end"] = base_kwargs["evaluation_period_start"]
        with pytest.raises(ValueError, match="evaluation_period_end must be after"):
            EvaluationReport(**base_kwargs)

    def test_ai_assisted_requires_content_safety_result(self, base_kwargs):
        base_kwargs["generated_by"] = "ai_assisted"
        with pytest.raises(ValueError, match="content_safety_result required"):
            EvaluationReport(**base_kwargs)

    def test_ai_assisted_with_safety_result_ok(self, base_kwargs):
        base_kwargs["generated_by"] = "ai_assisted"
        base_kwargs["content_safety_result"] = "pass"
        report = EvaluationReport(**base_kwargs)
        assert report.content_safety_result == "pass"

    def test_manual_without_safety_result_ok(self, base_kwargs):
        report = EvaluationReport(**base_kwargs)
        assert report.generated_by == "manual"
        assert report.content_safety_result is None

    def test_invalid_domain_findings_key(self, base_kwargs):
        df = DomainFinding(evaluation_domain="governance")
        base_kwargs["domain_findings"] = {"invalid_domain": df}
        with pytest.raises(ValueError, match="Invalid domain_findings key"):
            EvaluationReport(**base_kwargs)

    def test_valid_domain_findings_keys(self, base_kwargs):
        for domain in ["governance", "community_engagement", "effectiveness", "efficiency", "implementation"]:
            df = DomainFinding(evaluation_domain=domain)
            report = EvaluationReport(**{**base_kwargs, "domain_findings": {domain: df}})
            assert domain in report.domain_findings

    def test_report_with_all_domain_findings(self, base_kwargs):
        domains = ["governance", "community_engagement", "effectiveness", "efficiency", "implementation"]
        findings = {d: DomainFinding(evaluation_domain=d) for d in domains}
        base_kwargs["domain_findings"] = findings
        report = EvaluationReport(**base_kwargs)
        assert len(report.domain_findings) == 5

    def test_report_with_recommendations(self, base_kwargs):
        recs = [
            Recommendation(text="Improve governance", priority="high"),
            Recommendation(text="Update plans", priority="low"),
        ]
        base_kwargs["recommendations"] = recs
        report = EvaluationReport(**base_kwargs)
        assert len(report.recommendations) == 2

    def test_report_with_dissemination_records(self, base_kwargs):
        records = [
            DisseminationRecord(
                recipient="Government", recipient_type="government",
                disseminated_at=datetime.now(UTC), format="pdf",
            ),
            DisseminationRecord(
                recipient="Community Group", recipient_type="community",
                disseminated_at=datetime.now(UTC), format="presentation",
            ),
        ]
        base_kwargs["dissemination_records"] = records
        report = EvaluationReport(**base_kwargs)
        assert len(report.dissemination_records) == 2

    def test_finding_nesting_all_severities(self, base_kwargs):
        findings_list = [
            Finding(finding_text=f"Finding {s}", evidence_summary="Evidence", severity=s)
            for s in ["positive", "neutral", "concern", "critical"]
        ]
        df = DomainFinding(
            evaluation_domain="governance",
            findings=findings_list,
        )
        base_kwargs["domain_findings"] = {"governance": df}
        report = EvaluationReport(**base_kwargs)
        severities = [f.severity for f in report.domain_findings["governance"].findings]
        assert severities == ["positive", "neutral", "concern", "critical"]
