import os
import sys
import pytest

# Projektwurzel zu sys.path hinzufügen, damit `app` importierbar ist,
# auch wenn pytest das Working Directory anders setzt.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app


@pytest.fixture
def client():
    """Erzeuge einen Test-Client mit eigener App-Instanz."""
    app = create_app()
    app.config["TESTING"] = True
    # Achtung: benötigt eine laufende MongoDB laut MONGO_URI
    with app.test_client() as c:
        yield c


def test_register_and_login(client):
    """Smoke-Test für /auth/register und /auth/login."""
    r = client.post("/auth/register", json={"username": "max", "password": "123456"})
    assert r.status_code == 201
    tokens = r.get_json()
    assert "access" in tokens and "refresh" in tokens

    r2 = client.post("/auth/login", json={"username": "max", "password": "123456"})
    assert r2.status_code == 200
    data = r2.get_json()
    assert "access" in data and "refresh" in data


