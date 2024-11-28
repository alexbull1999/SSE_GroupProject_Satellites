import pytest
from app import process_query
from app import app


def test_knows_about_moon():
    assert process_query("moon") == "Moon made of cheese"


# tests to simulate HTTP requests to the app
@pytest.fixture
def client():
    # Setting up of test client
    with app.test_client() as client:
        yield client


def test_homepage(client):
    """Test the homepage."""
    response = client.get("/")
    assert response.status_code == 200
    # test should return with content from the homepage
    assert b"Track To The Future" in response.data


def test_satellite_search(client):
    """Test the satellite search."""
    data = {"name": "Hubble Space Telescope"}
    response = client.post("/satellite", data=data)
    assert response.status_code == 200
    # UPDATE HST TO MATCH NEW HTML PAGE
    assert b"HST" in response.data


def test_invalid_search(client):
    """Test for non-existent satellite search."""
    data = {"name": "non-existent satellite"}
    response = client.post("/satellite", data=data)
    assert response.status_code == 404
    # UPDATE HST TO MATCH NEW HTML PAGE
    assert b"404 Not Found" in response.data


def test_clickable_satellite(client):
    """test the clickable satellite on landing page"""
    response = client.get("/satellite/20580")
    assert response.status_code == 200
    # UPDATE HST TO MATCH NEW HTML PAGE
    assert b"HST" in response.data