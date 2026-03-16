from app.main import create_app
from fastapi.testclient import TestClient


def test_error_responses_are_structured_json() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/dead-letters/missing-entry/resolve", json={"resolution": "replayed"}
    )

    assert response.status_code == 422
    payload = response.json()
    assert "correlationId" in payload
    assert payload["statusCode"] == 422
    assert payload["errorCategory"] == "validation_error"
    assert "message" in payload
