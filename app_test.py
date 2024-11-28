from unittest.mock import patch
from app import process_query, get_satellite_data, app
from models import satelliteTable
from database import read_and_insert_csv, init_db, get_engine
import pytest
from sqlalchemy import inspect, select, delete
import polars as pl
import os


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

    init_db()  # Initialize database
    return get_engine()


@pytest.fixture(autouse=True)
def clear_table(engine):
    """Clear satellite table before each test"""
    with engine.connect() as connection:
        connection.execute(delete(satelliteTable))
        connection.commit()


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
    read_and_insert_csv(sample_csv)

    # Query the satellite table
    with engine.connect() as connection:
        result = connection.execute(
            select(satelliteTable)
        ).mappings()  # Using .mappings() to map column names to vlaues
        rows = list(result)

    # Verify the data matches the CSV
    assert len(rows) == 2, "Expected 2 rows in satellite table"
    assert rows[0]["id"] == 25544
    assert rows[0]["name"] == "ISS (ZARYA)"
    assert rows[1]["id"] == 43205
    assert rows[1]["name"] == "STARLINK-1"
