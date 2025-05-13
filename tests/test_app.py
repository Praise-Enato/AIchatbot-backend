from fastapi.testclient import TestClient

from chatbot_backend.app import app

client = TestClient(app)


def test_hello_endpoint() -> None:
    """Test the /hello endpoint."""
    response = client.get("/hello")
    assert response.status_code == 200
    data = response.json()
    assert data == {"input": "hello", "output": "world"}
