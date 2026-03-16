from apps.agents.communication.agent import CommunicationAgent


def test_communication_generates_all_supported_languages() -> None:
    agent = CommunicationAgent()
    alert = agent.draft_alert("incident-comm-1", "rec-comm-1")

    expected_languages = {"en-AU", "zh-Hans", "ar", "vi", "el", "it"}
    assert set(alert.languages) == expected_languages
    assert expected_languages.issubset(set(alert.content_blocks.keys()))
    assert alert.generation_method in {"llm", "template_fallback", "safety_fallback"}
