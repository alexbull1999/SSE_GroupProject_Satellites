from sqlalchemy import create_engine
from models import satellite_table, Base, user_table, user_satellite_table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, select, insert
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
    Base.metadata.create_all(bind=engine)


# Use satelliteTable defined in models
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


if __name__ == "__main__":
    csv_files = [
        "active1.csv",
        "noaa1.csv",
        "weather1.csv",
        "science1.csv",
        "galileo1.csv",
        "starlink1.csv",
    ]
    process_multiple_csv(csv_files)


def find_satellites_by_name(search_term):
    connection = sqlite3.connect("app_database.db")
    cursor = connection.cursor()
    query = "SELECT * FROM satellite WHERE name LIKE ? LIMIT 5"
    cursor.execute(query, ("%" + search_term + "%",))  # Match partial input
    results = cursor.fetchall()
    connection.close()
    return results


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

def delete_satellite_from_user(username, satellite_name):
    session = Session()
    try:
        # Find the user by username
        stmt = select(user_table).filter(user_table.c.user_name == username)
        user_result = session.execute(stmt).fetchone()
        if not user_result:
            raise ValueError(f"User '{username}' not found")

        user_id = user_result.id  # Extract the user_id - maybe not necessary if I can easily get the user_id

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

        print(f"Satellite '{satellite_name}' successfully deleted from user '{username}'")
    except Exception as e:
        session.rollback()
        print(f"Error deleting satellite: {e}")
    finally:
        session.close()


"""
# Function to add a country to a user (similar approach)
def add_country_to_user(user_id, country_id):
    session = Session()
    try:
        # Link the user with the country
        new_entry = {"user_id": user_id, "country_id": country_id}
        session.execute(user_country_table.insert().values(new_entry))
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()
"""


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


"""
def get_user_countries(username):
    session = Session()
    try:
        user = session.query(user_table).filter(user_table.c.user_name == username).first()
        if not user:
            raise ValueError("User not found")

        user_id = user.id  # Extract the user_id

        # Query to get all countries for the user (assuming you have a user_country_table)
        countries = session.query(country_table).join(user_country_table).filter(
            user_country_table.c.user_id == user_id
        ).all()

        return [country.name for country in countries]

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        session.close()

"""
