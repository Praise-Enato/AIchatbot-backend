from fastapi.testclient import TestClient

from chatbot_backend.app import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "healthy"}
