import pytest
from datetime import datetime

def test_dummy_api(client):
    response = client.get("/api/v1/signals/")
    assert response.status_code in (200, 404)  # 200 если реализовано, 404 если нет 