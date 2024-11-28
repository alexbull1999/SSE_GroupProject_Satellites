from models import satelliteTable
from database import read_and_insert_csv
from app import process_query
import pytest
from sqlalchemy import inspect, select, delete
from database import init_db, get_engine
import polars as pl
import os

def test_knows_about_moon():
    assert process_query("moon") == "Moon made of cheese"

#Use a temporary test database
TEST_DATABASE_FILE = "test_app_database.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DATABASE_FILE}"

@pytest.fixture(scope="module", autouse=True)
def engine():
    """Provide a database engine for testing"""
    if os.path.exists(TEST_DATABASE_FILE):
        os.remove(TEST_DATABASE_FILE) # ensure a clean database

    init_db() #Initialize database
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
    df = pl.DataFrame({
        "NORAD Catalog Number": [25544, 43205],
        "Name": ["ISS (ZARYA)", "STARLINK-1"],
    })
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

    #assert the required columns exist
    assert "id" in column_names, "Column 'Id' does not exist"
    assert "name" in column_names, "Column 'Name' does not exist"

def test_csv_import(engine, sample_csv):
    """Test if csv can be imported"""
    #Run CSV import logic
    read_and_insert_csv(sample_csv)

    #Query the satellite table
    with engine.connect() as connection:
        result = connection.execute(select(satelliteTable)).mappings() #Using .mappings() to map column names to vlaues
        rows = list(result)

    # Verify the data matches the CSV
    assert len(rows) == 2, "Expected 2 rows in satellite table"
    assert rows[0]["id"] == 25544
    assert rows[0]["name"] == "ISS (ZARYA)"
    assert rows[1]["id"] == 43205
    assert rows[1]["name"] == "STARLINK-1"
