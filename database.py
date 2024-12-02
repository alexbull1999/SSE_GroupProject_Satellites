from sqlalchemy import create_engine, insert
from sqlalchemy.orm import sessionmaker
from models import satellite_table, Base, country_table
import polars as pl
import sqlite3

# Define the SQLite database file
DATABASE_FILE = "app_database.db"  # SQLite database file name
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(DATABASE_URL, echo=True)  # echo=True for logging
Session = sessionmaker(bind=engine)


def get_engine(database_url=None):
    """Returns database engine"""
    return create_engine(database_url or DATABASE_URL)


def init_db(database_url=None):
    """Initializes the database by creating all tables defined
    in the metadata"""
    engine = create_engine(database_url or DATABASE_URL)
    Base.metadata.drop_all(bind=engine)  # drop all existing tables
    Base.metadata.create_all(bind=engine)  # recreate all tables


# Use satellite_table defined in models
def read_and_insert_csv(file_path, engine):
    """Reads a csv file and inserts selected columns into the database"""
    # Read the CSV file using Polars
    schema_overrides = {
        "MEAN_MOTION_DDOT": pl.Float64,
        # treat scientific notation as a float to stop errors
    }

    df = pl.read_csv(file_path, schema_overrides=schema_overrides)

    # Select the required columns and rename them
    selected_df = df.select(
        [
            pl.col("NORAD_CAT_ID").alias("id"),
            pl.col("OBJECT_NAME").alias("name"),
        ]
    )

    # Convert to a list of dictionaries for insertion
    data = selected_df.to_dicts()

    # Insert data into database
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                satellite_table.insert().prefix_with("OR IGNORE"),
                data,
            )
            transaction.commit()
        except Exception as e:
            transaction.rollback()
            raise e


def process_multiple_csv(files):
    """Processes multiple csv files and inserts data into database"""
    for file in files:
        read_and_insert_csv(file, engine)


def find_satellites_by_name(search_term):
    connection = sqlite3.connect("app_database.db")
    cursor = connection.cursor()
    query = "SELECT * FROM satellite WHERE name LIKE ? LIMIT 5"
    cursor.execute(query, ("%" + search_term + "%",))  # Match partial input
    results = cursor.fetchall()
    connection.close()
    return results


def populate_country_table(csv_file_path, area_csv_file_path, engine):
    """Populates country table with country names and coordinates"""
    try:
        # read csv into polars dataframe
        country_df = pl.read_csv(csv_file_path)

        # load area data from country_area.csv into polars dataframe
        area_df = pl.read_csv(area_csv_file_path).rename(
            {"Country": "name", "Area (sq. mi.)": "area"}
        )

        # Normalize name column in both DFs
        country_df = country_df.with_columns(
            pl.col("name").str.strip_chars().str.to_lowercase()
        )
        area_df = area_df.with_columns(
            pl.col("name").str.strip_chars().str.to_lowercase()
        )

        # Perform the join operation
        merged_df = country_df.join(area_df, on="name", how="inner")

        # Select only required columns from the merged dataframe
        merged_df = merged_df.select(
            ["country", "latitude", "longitude", "name", "area"]
        )
        merged_df = merged_df.with_columns(pl.col("name").str.to_uppercase())

        earth_area = 197_000_000
        merged_df = merged_df.with_columns(
            (merged_df["area"] / earth_area).round(1).alias("above_angle")
        )

        # select and map required columns
        countries = [
            {
                "country": row["country"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "name": row["name"],
                "area": row["area"],
                "above_angle": row["above_angle"],
            }
            for row in merged_df.to_dicts()
        ]

        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(insert(country_table), countries)
                transaction.commit()
            except Exception as e:
                transaction.rollback()
                print(f"Error committing to database: {e}")

    except Exception as e:
        print(f"Error inserting country data: {e}")


if __name__ == "__main__":
    init_db(DATABASE_URL)

    csv_files = [
        "active1.csv",
        "noaa1.csv",
        "weather1.csv",
        "science1.csv",
        "galileo1.csv",
        "starlink1.csv",
    ]
    process_multiple_csv(csv_files)

    populate_country_table("countries.csv", "country_area.csv", engine)
