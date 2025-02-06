import pytest
from app import app

@pytest.fixture
def client():
    """ Erstellt einen Test-Client für die API """
    app.config["TESTING"] = True
    client = app.test_client()
    yield client

def test_index_route(client):
    """ Testet, ob die Startseite geladen wird """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Amazon Product Sentiment Analysis" in response.data
