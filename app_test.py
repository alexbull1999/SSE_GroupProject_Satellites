from unittest.mock import patch
from app import process_query, get_satellite_data, app, user_info
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
    response = client.get("/satellite?name=HST")
    assert response.status_code == 200
    # UPDATE HST TO MATCH NEW HTML PAGE
    assert b"HST" in response.data


def test_invalid_search(client):
    """Test for non-existent satellite search."""
    response = client.get("/satellite?name=non-existent%20satellite")
    assert response.status_code == 404
    # UPDATE HST TO MATCH NEW HTML PAGE
    assert b"404 Not Found" in response.data


def test_clickable_satellite(client):
    """test the clickable satellite on landing page"""
    response = client.get("/satellite/20580")
    assert response.status_code == 200
    # UPDATE HST TO MATCH NEW HTML PAGE
    assert b"HST" in response.data


def test_clickable_country(client):
    """test the clicking on a country in user page"""
    response = client.get("/country/USA")
    assert response.status_code == 200
    assert b"USA" in response.data


@pytest.mark.skip
def test_create_new_user(client):
    # simulating creating a new user
    response = client.post(
        "/create_account",
        json=({"username": "new_user"}),
        follow_redirects=False,
    )

    # Check JSON response code
    assert response.status_code == 200
    assert b'{"message":"Account created successfully"}\n' in response.data
    # check the user is in the user_info database
    assert "new_user" in user_info


@pytest.mark.skip
def test_create_account_existing_user(client):
    # simulate creating an account
    response = client.post("/create_account", json={"username": "test_user"})
    assert response.status_code == 200  # Account created successfully

    # Simulate trying to create the same account again
    response = client.post("/create_account", json={"username": "test_user"})
    assert response.status_code == 400  # Should return error for existing user
    assert b"User already exists" in response.data


def test_login_valid_user(client):
    """test for a valid user"""
    response = client.post("/login", json={"username": "AlexB"})
    assert response.status_code == 200
    assert b"Login successful" in response.data


def test_login_invalid_user(client):
    """test for an invalid user"""
    response = client.post("/login", json={"username": "nonexistent_use"})
    assert response.status_code == 400
    assert b"User does not exist" in response.data


@pytest.mark.skip
def test_account_display_valid_user(client):
    """Test for a valid user with multiple satellites & countries"""
    # Send a POST requst to login
    response = client.get("/account/AlexB")
    assert response.status_code == 200
    assert b"Welcome, AlexB"
    assert b"Countries You Are Tracking" in response.data
    assert b"USA" in response.data
    assert b"India" in response.data
    assert b"ISS" in response.data
    assert b"HST" in response.data


@pytest.mark.skip
def test_account_display_valid_user_no_countries_or_satellites(client):
    """Test for a valid user with no satellites & countries tracked"""
    response = client.get("/account/RobL")
    assert response.status_code == 200
    assert b"No satellites being tracked" in response.data
    assert b"No countries being tracked" in response.data


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

    populate_country_table(csv_path, "country_area.csv", engine)

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
