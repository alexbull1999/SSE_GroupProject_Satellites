from unittest.mock import patch, MagicMock

import requests

from app import app
from database import (
    read_and_insert_csv,
    init_db,
    get_engine,
    populate_country_table,
)
import pytest
from sqlalchemy import inspect, select
import polars as pl
import os
from models import satellite_table as get_satellite_table
from models import country_table as get_country_table
from blueprints.utils import (
    process_query,
    get_satellite_data,
    fetch_satellite_image,
    generateSatData,
)


def test_knows_about_moon():
    assert process_query("moon") == "Moon made of cheese"


# tests to simulate HTTP requests to the app
@pytest.fixture
def client():
    # Setting up of test client
    app.testing = True
    with app.test_client() as client:
        yield client


# Mock database connection for tests
@pytest.fixture
def mock_db(mocker):
    mock_conn = mocker.patch("sqlite3.connect")
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    return mock_cursor


def test_homepage(client):
    """Test the homepage."""
    response = client.get("/")
    assert response.status_code == 200
    # test should return with content from the homepage
    assert b"Track To The Future" in response.data


def test_satellite_search(client, mock_db):
    """Test the satellite search."""
    mock_db.fetchone.return_value = (20580, "HST")
    response = client.get("/?name=HST")
    assert response.status_code == 200
    assert b"HST" in response.data


def test_invalid_search(client):
    """Test for non-existent satellite search."""
    response = client.get("/satellite?name=No-satellite")
    # Confirm it performs an HTTP 404 status code response
    assert response.status_code == 404


def test_clickable_satellite(client, mock_db):
    """test the clickable satellite on landing page"""
    mock_db.fetchone.return_value = (20580, "HST")
    response = client.get("/satellites/20580/HST")
    assert response.status_code == 200
    assert b"HST" in response.data


@patch("requests.get")
def test_clickable_country(mock_requests_get, client, mock_db):
    """test the clicking on a country in user page"""
    # Mock database response
    mock_db.fetchone.return_value = (
        "USA",
        40.7128,
        -74.0060,
        0,
        0,
        500,
    )  # Country, lat, lng, radius

    # Mock API response
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {
        "above": [{"satid": 12345, "satname": "HST"}]
    }

    # Send the request
    response = client.get("/country/?country=USA")
    print(response.data.decode())  # Debug rendered content

    # Assertions
    assert response.status_code == 200
    assert b"Satellites Over" in response.data
    assert b"HST" in response.data


def test_login_valid_user(client):
    """test for a valid user"""
    response = client.post(
        "/login", json={"username": "AlexB"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Login successful" in response.data


def test_login_invalid_user(client):
    """test for an invalid user"""
    response = client.post(
        "/login", json={"username": "nonexistent_use"}, follow_redirects=True
    )
    assert response.status_code == 400
    assert b"User does not exist" in response.data


@patch("requests.get")
def test_api_satellite(mock_get):
    """Mock Test the N2Y0 API"""
    # set up the mock to return a fake response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "satname": "HST",
        "satid": 20580,
    }

    # call the function under test
    result = get_satellite_data(20580)

    assert result["satname"] == "HST"
    assert result["satid"] == 20580


# Use a temporary test database
TEST_DATABASE_FILE = "test_app_database.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DATABASE_FILE}"


@pytest.fixture(scope="module", autouse=True)
def engine():
    """Provide a database engine for testing"""
    if os.path.exists(TEST_DATABASE_FILE):
        os.remove(TEST_DATABASE_FILE)  # ensure a clean database

    init_db(TEST_DATABASE_URL)  # Initialize database
    return get_engine(TEST_DATABASE_URL)


@pytest.fixture
def sample_csv(tmp_path):
    """Create sample csv file to test"""
    csv_path = tmp_path / "sample.csv"
    df = pl.DataFrame(
        {
            "NORAD_CAT_ID": [25544, 43205],
            "OBJECT_NAME": ["ISS (ZARYA)", "STARLINK-1"],
        }
    )
    df.write_csv(csv_path)
    return csv_path


def test_satellite_table_exists(engine):
    """Test if the satellite table exists in database"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "satellite" in tables, "Table 'satellite' does not exist"


def test_satellite_table_columns(engine):
    """Test if satellite table has correct columns"""
    inspector = inspect(engine)
    columns = inspector.get_columns("satellite")
    column_names = [col["name"] for col in columns]

    # assert the required columns exist
    assert "id" in column_names, "Column 'Id' does not exist"
    assert "name" in column_names, "Column 'Name' does not exist"


def test_csv_import(engine, sample_csv):
    """Test if csv can be imported"""
    # Run CSV import logic
    read_and_insert_csv(sample_csv, engine)

    # Query the satellite table
    with engine.connect() as connection:
        result = connection.execute(
            select(get_satellite_table)
        ).mappings()  # Using .mappings() to map column names to values
        rows = list(result)

    # Verify the data matches the CSV
    assert len(rows) == 2, "Expected 2 rows in satellite table"
    assert rows[0]["id"] == 25544
    assert rows[0]["name"] == "ISS (ZARYA)"
    assert rows[1]["id"] == 43205
    assert rows[1]["name"] == "STARLINK-1"


# New tests for country table
def test_country_table_exists(engine):
    """Test if country table exists in database"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "country" in tables, "Table 'country' does not exist"


def test_country_table_columns(engine):
    """Test if country table has correct columns"""
    inspector = inspect(engine)
    columns = inspector.get_columns("country")
    column_names = [col["name"] for col in columns]
    assert "name" in column_names, "Column 'name' does not exist"
    assert "latitude" in column_names, "Column 'latitude' does not exist"
    assert "longitude" in column_names, "Column 'longitude' does not exist"
    assert "area" in column_names, "Column 'area' does not exist"
    assert "above_angle" in column_names, "Column 'above_angle' does not exist"


def test_country_table_population(tmp_path, engine):
    """Test if country table populated properly"""

    csv_path = tmp_path / "countries.csv"
    df = pl.DataFrame(
        {
            "country": ["AUS", "GB"],
            "latitude": [10.0, 20.0],
            "longitude": [-10.0, -20.0],
            "name": ["Australia", "Great Britain"],
        }
    )
    df.write_csv(csv_path)

    populate_country_table(csv_path, "csvfiles/country_area.csv", engine)

    with engine.connect() as connection:
        result = connection.execute(select(get_country_table)).mappings()
        rows = list(result)

    # Verify that at least some countries were populates
    assert len(rows) > 0, "Country table is empty"
    assert rows[0]["name"] is not None, "Expected country name to be populated"
    assert rows[0]["latitude"] is not None, "Expected latitude to be populated"
    assert (
        rows[0]["longitude"] is not None
    ), "Expected country longitude to be populated"
    assert rows[0]["area"] is not None, "Expected country area to be populated"
    assert (
        rows[0]["above_angle"] is not None
    ), "Expected country above_angle to be populated"


@patch("sqlite3.connect")
def test_satellite_missing_name(mock_connect, client):
    """Test for missing satellite name."""
    response = client.get("/satellites/?name=")
    assert response.status_code == 400
    assert b"Satellite name is required" in response.data


@patch("requests.get")
@patch("blueprints.utils.get_observer_location")
@patch("sqlite3.connect")
def test_satellite_not_found(
    mock_connect, mock_get_observer_location, mock_requests_get, client
):
    """Test for satellite not found in the database."""
    mock_get_observer_location.return_value = (
        10.0,
        20.0,
    )  # Mock observer location
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # No satellite found

    response = client.get("/satellite/?name=NonExistentSatellite")
    assert response.status_code == 404
    assert b"404 Not Found" in response.data


@patch("os.getenv")
@patch("requests.get")
def test_fetch_satellite_image_curated(mock_requests_get, mock_getenv):
    """Test fetching curated satellite image."""
    # Test with a curated image (e.g., "HST")
    result = fetch_satellite_image("HST")
    assert (
        result
        == "https://upload.wikimedia.org/wikipedia/commons/3/3f/HST-SM4.jpeg"
    )


@patch("os.getenv")
@patch("requests.get")
def test_fetch_satellite_image_missing_api_key(mock_requests_get, mock_getenv):
    """Test fetching satellite image when Google API key is missing."""
    mock_getenv.side_effect = lambda key: None  # Mock missing API keys
    result = fetch_satellite_image("NonExistent")
    assert (
        result == "https://wmo.int/sites/default/files/"
        "2023-03/AdobeStock_580430822.jpeg"
    )


@patch("os.getenv")
@patch("requests.get")
def test_fetch_satellite_image_google_api_success(
    mock_requests_get, mock_getenv
):
    """Test fetching satellite image with Google API success."""
    # Mock Google API Key and CX
    mock_getenv.side_effect = lambda key: (
        "test_key" if key == "GOOGLE_API_KEY" else "test_cx"
    )

    # Mock Google API response
    mock_requests_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "items": [{"link": "http://example.com/satellite_image.jpg"}]
        },
    )

    result = fetch_satellite_image("TestSatellite")
    assert result == "http://example.com/satellite_image.jpg"


@patch("os.getenv")
@patch("requests.get")
def test_fetch_satellite_image_google_api_failure(
    mock_requests_get, mock_getenv
):
    """Test fetching satellite image with Google API failure."""
    # Mock Google API Key and CX
    mock_getenv.side_effect = lambda key: (
        "test_key" if key == "GOOGLE_API_KEY" else "test_cx"
    )

    # Mock API request failure
    mock_requests_get.side_effect = requests.RequestException(
        "Google API failure"
    )

    result = fetch_satellite_image("TestSatellite")
    assert (
        result == "https://wmo.int/sites/default/files/"
        "2023-03/AdobeStock_580430822.jpeg"
    )


def test_generateSatData_empty_tle():
    """Test generateSatData with empty TLE data."""
    satellite_data = {
        "tle": "",
        "info": {
            "satname": "TestSatellite",
            "satid": 12345,
        },
    }

    image_url = "http://example.com/image.jpg"
    result = generateSatData(image_url, satellite_data)

    assert result["name"] == "TestSatellite"
    assert result["id"] == 12345
    assert result["image_url"] == image_url
    assert "location" not in result  # Location should be absent
