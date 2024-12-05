from sqlalchemy import create_engine, insert
from models import (
    satellite_table,
    Base,
    country_table,
    user_table,
    user_satellite_table,
    user_country_table
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, select, insert
import polars as pl
import sqlite3
from math import acos, pi, degrees

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


def find_country_by_name(country_search):
    connection = sqlite3.connect("app_database.db")
    cursor = connection.cursor()
    query = "SELECT * FROM country WHERE name LIKE ? LIMIT 5"
    cursor.execute(query, ("%" + country_search + "%",))
    results = cursor.fetchall()
    connection.close()
    return results


def calculate_above_angle(country_area):
    """Caclulate the above angle for a given country's area
    using the coverage radius"""
    earth_radius = 6371  # Earth radius in km
    earth_surface_area = 4 * pi * earth_radius**2  # Total surface area

    # Normalize country area relative to Earth's surface
    normalized_area = country_area / earth_surface_area

    # Calculate the above angle (spherical cap formula)
    if normalized_area < 1e-6:  # Avoid extremely small areas
        return 5.0  # Min angle threshold

    angle_radians = acos(1 - (normalized_area * 2 * pi))
    angle_degrees = degrees(angle_radians)

    return max(angle_degrees, 5.0)


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

        above_angle = [
            calculate_above_angle(area) for area in merged_df["area"].to_list()
        ]
        merged_df = merged_df.with_columns(
            pl.Series("above_angle", above_angle)
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


# Helper function to get satellite name by id
def get_satellite_by_id(satellite_id):
    session = Session()  # Use SQLAlchemy session for consistency
    try:
        # Query the satellite by name (case-insensitive search)
        stmt = select(satellite_table).where(
            func.lower(satellite_table.c.name) == satellite_name.lower()
        )
        result = session.execute(stmt).fetchone()
        if result:
            return result.id  # Assuming result contains an 'id' field
        return None
    except Exception as e:
        print(f"Error finding satellite by name: {e}")
        return None  # Return None if an error occurs
    finally:
        session.close()


def get_satellite_id_by_name(satellite_name):
    connection = sqlite3.connect("app_database.db")
    cursor = connection.cursor()

    # Query to find the satellite by its name
    query = "SELECT id FROM satellite WHERE name = ? LIMIT 1"
    cursor.execute(query, (satellite_name,))  # Match exact name
    result = cursor.fetchone()

    # Close the connection
    connection.close()

    # If a satellite is found, return its ID
    if result:
        return result[0]
    return None


# Function to add a user
def add_user(user_name):
    session = Session()
    try:
        new_user = {"user_name": user_name}
        session.execute(
            user_table.insert().values(new_user)
        )  # Insert the new user
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()


def check_username_exists(username):
    session = Session()  # Create a session instance
    try:
        # Query the database to check if the username exists
        user_result = session.execute(
            user_table.select().where(
                func.lower(user_table.c.user_name) == username.lower()
            )
        ).fetchone()
        # Convert result to a dictionary
        if user_result:
            user = {
                column: value
                for column, value in zip(
                    user_table.columns.keys(), user_result
                )
            }
            return user  # Now it's a dictionary
        else:
            return None

    except Exception as e:
        print(f"Error checking username: {e}")
        return None  # In case of an error, we can return False
    finally:
        session.close()


# Function to add a satellite to a user (by satellite name or ID)
def add_satellite_to_user(username, satellite_name):
    session = Session()
    try:
        # Find the user by username using raw user_table
        stmt = select(user_table).filter(user_table.c.user_name == username)
        user_result = session.execute(stmt).fetchone()
        if not user_result:
            raise ValueError(f"User '{username}' not found")

        user_id = user_result.id  # Extract the user_id

        # Find satellite by name
        satellite_id = get_satellite_id_by_name(satellite_name)
        print(f"Satellite ID found: {satellite_id}")
        if not satellite_id:
            raise ValueError("Satellite not found")

        # Check if the user is already tracking this satellite
        check_stmt = select(user_satellite_table).where(
            user_satellite_table.c.user_id == user_id,
            user_satellite_table.c.satellite_id == satellite_id,
        )
        is_tracking = session.execute(check_stmt).fetchone()

        if is_tracking:
            raise ValueError("Satellite already tracked by user")

        # Insert the relationship into the user_satellite table
        insert_stmt = insert(user_satellite_table).values(
            user_id=user_id, satellite_id=satellite_id
        )
        session.execute(insert_stmt)
        session.commit()

        print(
            f"Satellite '{satellite_name}' successfully added to user '{username}'"
        )

    except ValueError as ve:
        print(f"Error: {ve}")
        raise  # Re-raise for higher-level error handling if needed
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise  # Re-raise for higher-level error handling if needed
    finally:
        session.close()

def add_country_to_user(username, country_name):
    session = Session()
    try:
        # Find the user by username using raw user_table
        stmt = select(user_table).filter(user_table.c.user_name == username)
        user_result = session.execute(stmt).fetchone()
        if not user_result:
            raise ValueError(f"User '{username}' not found")

        user_id = user_result.id  # Extract the user_id

        # Check if the user is already tracking this country
        check_stmt = select(user_country_table).where(
            user_country_table.c.user_id == user_id,
            user_country_table.c.country_name == country_name,
        )
        is_tracking = session.execute(check_stmt).fetchone()

        if is_tracking:
            raise ValueError("Country already tracked by user")

        # Insert the relationship into the user_country table
        insert_stmt = insert(user_country_table).values(
            user_id=user_id, country_name=country_name
        )
        session.execute(insert_stmt)
        session.commit()

        print(
            f"Country '{country_name}' successfully added to user '{username}'"
        )

    except ValueError as ve:
        print(f"Error: {ve}")
        raise  # Re-raise for higher-level error handling if needed
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise  # Re-raise for higher-level error handling if needed
    finally:
        session.close()


def delete_satellite_from_user(username, satellite_name):
    session = Session()
    try:
        # Find the user by username
        stmt = select(user_table).filter(user_table.c.user_name == username)
        user_result = session.execute(stmt).fetchone()
        if not user_result:
            raise ValueError(f"User '{username}' not found")

        user_id = (
            user_result.id
        )  # Extract the user_id - maybe not necessary if I can easily get the user_id

        # Find satellite by name
        satellite_id = get_satellite_id_by_name(satellite_name)
        if not satellite_id:
            raise ValueError("Satellite not found")

        # Check if the user is tracking this satellite - surely they already will be if it can be deleted.
        check_stmt = select(user_satellite_table).where(
            user_satellite_table.c.user_id == user_id,
            user_satellite_table.c.satellite_id == satellite_id,
        )
        is_tracking = session.execute(check_stmt).fetchone()

        if not is_tracking:
            raise ValueError("Satellite is not currently tracked by user")

        # Delete the relationship from the user_satellite table
        delete_stmt = user_satellite_table.delete().where(
            user_satellite_table.c.user_id == user_id,
            user_satellite_table.c.satellite_id == satellite_id,
        )
        session.execute(delete_stmt)
        session.commit()

        print(
            f"Satellite '{satellite_name}' successfully deleted from user '{username}'"
        )
    except Exception as e:
        session.rollback()
        print(f"Error deleting satellite: {e}")
    finally:
        session.close()

def delete_country_from_user(username, country_name):
    session = Session()
    try:
        # Find the user by username
        stmt = select(user_table).filter(user_table.c.user_name == username)
        user_result = session.execute(stmt).fetchone()
        if not user_result:
            raise ValueError(f"User '{username}' not found")

        user_id = user_result.id  # Extract user_id

        # Find country by name directly (no need for country_id)
        country_stmt = select(country_table).filter(country_table.c.name == country_name)
        country_result = session.execute(country_stmt).fetchone()

        if not country_result:
            raise ValueError("Country not found")

        # Assuming the country name is unique, we don't need the country_id.
        # Check if the user is tracking this country
        check_stmt = select(user_country_table).where(
            user_country_table.c.user_id == user_id,
            user_country_table.c.country_name == country_name,  # Use country_name directly
        )
        is_tracking = session.execute(check_stmt).fetchone()

        if not is_tracking:
            raise ValueError("Country is not currently tracked by user")

        # Delete the relationship from the user_country table
        delete_stmt = user_country_table.delete().where(
            user_country_table.c.user_id == user_id,
            user_country_table.c.country_name == country_name,  # Use country_name directly
        )
        session.execute(delete_stmt)
        session.commit()

        print(f"Country '{country_name}' successfully deleted from user '{username}'")
    except Exception as e:
        session.rollback()
        print(f"Error deleting country: {e}")
    finally:
        session.close()



def get_user_satellites(username):
    session = Session()
    try:
        # Find the user by username using the raw user_table, not a User object
        stmt = select(user_table).filter(user_table.c.user_name == username)
        result = session.execute(stmt).first()

        if not result:
            raise ValueError("User not found")

        user_id = result.id  # Extract the user_id

        # Query to get all satellites for the user
        satellites_stmt = (
            select(satellite_table)
            .join(user_satellite_table)
            .filter(user_satellite_table.c.user_id == user_id)
        )
        satellites = session.execute(satellites_stmt).all()

        # Return the satellites as a list of dicts
        return [
            {"id": satellite.id, "name": satellite.name}
            for satellite in satellites
        ]

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        session.close()


def get_user_countries(username):
    session = Session()
    try:
        # Find the user by username
        stmt = select(user_table).filter(user_table.c.user_name == username)
        result = session.execute(stmt).fetchone()

        # Debugging output
        print(f"User query result: {result}")  # Check if the user exists

        if not result:
            raise ValueError("User not found")

        user_id = result.id  # Extract the user_id

        # Debugging output
        print(f"User ID: {user_id}")  # Check the extracted user_id

        # Query to get all countries for the user
        countries_stmt = (
            select(country_table.c.name)  # We want the 'name' column from country_table
            .join(user_country_table, user_country_table.c.country_name == country_table.c.name)  # Join on the country_name and name
            .filter(user_country_table.c.user_id == user_id)  # Filter by the user_id
        )
        countries = session.execute(countries_stmt).all()

        # Debugging output
        print(f"Countries found: {countries}")  # Check the countries retrieved

        # Return the countries as a list of dicts
        return [{"name": country[0]} for country in countries]

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        session.close()

