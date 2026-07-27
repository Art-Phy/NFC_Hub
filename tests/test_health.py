from fastapi.testclient import TestClient

from nfc_hub.main import app

client = TestClient(app)


class TestHealth:
    def test_status_code(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_json_response(self):
        response = client.get("/health")
        assert response.json() == {"status": "ok"}
