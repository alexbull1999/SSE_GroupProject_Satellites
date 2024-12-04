from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import sqlite3
from database import (
    get_engine,
    DATABASE_URL,
    init_db,
    find_satellites_by_name,
    populate_country_table,
    find_country_by_name,
    add_satellite_to_user,
    get_user_satellites,
    check_username_exists,
    add_user,
    delete_satellite_from_user,
)
import os
from dotenv import load_dotenv
import ephem
import math
import pycountry

load_dotenv()
app = Flask(__name__)

# configure production database
engine = get_engine(DATABASE_URL)


if __name__ == "__main__":
    init_db(DATABASE_URL)
    populate_country_table("countries.csv", engine)
    app.run(debug=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/lookup")
def lookup():
    return render_template("search.html")


@app.route("/login_page")
def login_page():
    return render_template("login.html")


@app.route("/satellite", methods=["GET"])
def satellite():
    input_satellite = request.args.get("name")

    if not input_satellite:
        return "Satellite name is required", 400

    # Connect to the database and fetch corresponding satellite ID
    try:
        # Get observer location
        observer_location = get_observer_location()
        if not observer_location:
            return "Could not determine observer location", 500

        observer_lat, observer_lng = observer_location
        observer_alt = 0  # set observer altitude to sea level

        connection = sqlite3.connect("app_database.db")
        cursor = connection.cursor()

        # Query to get the satellite ID based on the name
        query = "SELECT * FROM satellite WHERE name = ?"
        cursor.execute(query, (input_satellite,))
        result = cursor.fetchone()  # Fetch first result

        connection.close()

        # Check if result was found
        if result:
            satellite_id = result[0]
            satellite_name = result[1]
            API_KEY = os.getenv("API_KEY")
            NY20_API_BASE = "https://api.n2yo.com/rest/v1/satellite/"

            # Fetch TLE data
            tle_url = f"{NY20_API_BASE}tle/{satellite_id}&apiKey={API_KEY}"
            tle_response = requests.get(tle_url)
            if tle_response.status_code != 200:
                return "Failed to fetch TLE data", 500
            tle_data = tle_response.json()

            # Fetch orbit data
            orbit_url = (
                f"{NY20_API_BASE}positions/{satellite_id}/"
                f"{observer_lat}/{observer_lng}/"
                f"{observer_alt}/10&apiKey={API_KEY}"
            )
            orbit_response = requests.get(orbit_url)
            if orbit_response.status_code != 200:
                return "Failed to fetch Orbit data", 500
            orbit_data = orbit_response.json()

            # Fetch visible passes
            days = 10  # Max prediction range
            min_visibility = 300  # min visibility in seconds
            passes_url = (
                f"{NY20_API_BASE}visualpasses/{satellite_id}/"
                f"{observer_lat}/{observer_lng}/{observer_alt}/"
                f"{days}/{min_visibility}&apiKey={API_KEY}"
            )
            passes_response = requests.get(passes_url)
            if passes_response.status_code != 200:
                return "Failed to fetch visible passes data", 500
            passes_data = passes_response.json()

            # Extract next visible pass
            next_pass = None
            if passes_data.get("passes"):
                next_pass = passes_data["passes"][0][
                    "startUTC"
                ]  # Get pass time

            # Fetch satellite image
            image_url = fetch_satellite_image(satellite_name)

            # Generate satellite data for template
            data = generateSatData(image_url, tle_data)

            # Render template with all the data
            return render_template(
                "satellite.html",
                satellite=data,
                observer_lat=observer_lat,
                observer_lng=observer_lng,
                orbit_data=orbit_data,
                next_pass=next_pass,
            )
        else:
            return "404 Not Found", 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/satellite/<int:satellite_id>", methods=["GET"])
def satellite_by_id(satellite_id):

    # Get the image URL from the query parameter
    image_url = request.args.get("image_url")
    # Search for the satellite by ID
    start_url = "https://api.n2yo.com/rest/v1/satellite/tle/"
    end_url = "&apiKey=LMFEWE-UWEWBT-WF7CWC-5DK0"
    url = f"{start_url}{satellite_id}{end_url}"
    response = requests.get(url)
    if response.status_code == 200:
        satellite_data = response.json()
        data = generateSatData(image_url, satellite_data)
        return render_template("satellite.html", satellite=data)
    return "404 Not Found", 404


def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"


@app.route("/country", methods=["GET"])
def get_satellites_over_country():
    """
    Retrieve satellites currently over a specified country using the N2YO API.
    """
    # Extract the country name from the form input
    input_country = request.args.get("country")

    if not input_country:
        return "Country name is required", 400

    # Connect to the database and fetch matching country names
    try:
        connection = sqlite3.connect("app_database.db")
        cursor = connection.cursor()

        # Query to get the satellite ID based on the name
        query = "SELECT * FROM country WHERE name = ?"
        cursor.execute(query, (input_country,))
        result = cursor.fetchone()  # Fetch first result

        connection.close()

        # Check if result was found
        if result:
            observer_lat = result[1]
            observer_lng = result[2]
            search_radius = result[5]
            observer_alt = 0
            category_id = 0

            # Extract API key
            API_KEY = os.getenv("API_KEY")
            if not API_KEY:
                return "API key is missing in environment variables", 500

            # Construct API request URL for fetching satellites above country
            NY20_API_BASE = "https://api.n2yo.com/rest/v1/satellite/"
            url = (
                f"{NY20_API_BASE}above/{observer_lat}/{observer_lng}/"
                f"{observer_alt}/"
                f"{search_radius}/{category_id}/&apiKey={API_KEY}"
            )

            # Send the request to the N2YO API
            response = requests.get(url)

            satellites = []

            # Process the API response
            if response.status_code == 200:
                # Check if the request was successful
                # Parse the response JSON to extract satellite data
                data = response.json()
                for sat in data.get(
                    "above", []
                ):  # Iterate through the satellites in the "above" field
                    satellites.append(
                        {
                            "id": sat.get("satid"),
                            "name": sat.get("satname"),
                        }
                    )
            else:
                return "Failed to retrieve satellite data from API", 500

            # Render the country.html template with the satellite data
            # and the selected country
            error_message = "No satellites currently above this country"
            return render_template(
                "country.html",
                country=input_country,  # The country name for the display
                satellites=satellites,  # List of satellites above the country
                error_message=None if satellites else error_message,
            )

        else:
            return "Country not found in database", 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_satellite_data(satellite_id):
    start_url = "https://api.n2yo.com/rest/v1/satellite/tle/"
    end_url = "&apiKey=LMFEWE-UWEWBT-WF7CWC-5DK0"
    url = f"{start_url}{satellite_id}{end_url}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
        # change to return to the render template satellite.html
    else:
        return None


def dms_to_decimal(dms_str):
    d, m, s = map(float, dms_str.split(":"))
    decimal = float(d) + (float(m) / 60) + (float(s) / 3600)
    return str(round(decimal, 6))


def pyephem(tle):

    RADIUS = 6371.0
    GRAVITY = 398600.4418  # km^3/s^2

    time = ephem.now()

    observer = ephem.Observer()
    observer.date = ephem.now()
    sat = ephem.readtle(tle[0], tle[1], tle[2])
    sat.compute(observer)

    lat = sat.sublat
    long = sat.sublong

    observer2 = ephem.Observer()
    observer2.lat, observer2.long, observer2.elevation = lat, long, 0
    observer2.date = time

    sat.compute(observer2)

    elevation = sat.elevation / 1000
    ov = math.sqrt(GRAVITY / (RADIUS + elevation))
    ground_speed = ov * (RADIUS / (RADIUS + elevation))

    data = {
        "lat": lat,
        "long": long,
        # "lat": lat,
        # "long": long,
        "elevation": "{:.0f}".format(elevation),
        "ground_speed": round(ground_speed, 2),
    }
    return data


def getlocation(lat, long):
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    url_start = "https://api.openweathermap.org/geo/1.0/reverse?"
    url_lat_long = f"lat={dms_to_decimal(lat)}&lon={dms_to_decimal(long)}"
    url_end = f"&limit=5&appid={WEATHER_API_KEY}"
    response = requests.get(url_start + url_lat_long + url_end)
    if response.status_code == 200:
        location = response.json()
        if len(location) == 0:
            return "Currently flying over the ocean"
        location_string = "No location found"
        if "country" in location[0]:
            code = location[0]["country"].upper()
            country = pycountry.countries.get(alpha_2=code)
            location_string = country.name if country else code
            if "state" in location[0]:
                state = location[0]["state"]
                location_string = location_string + ", " + state
                if "name" in location[0]:
                    name = location[0]["name"]
                    location_string = location_string + ", " + name
        return location_string
    return "No location Found"


def generateSatData(image_url, satellite_data):
    tle_data = satellite_data["tle"]
    name = satellite_data["info"]["satname"]
    data = {}
    if tle_data != "":
        tle_lines = tle_data.split("\r\n")
        tle = [name, tle_lines[0], tle_lines[1]]
        data = pyephem(tle)
        lat = str(data["lat"])
        long = str(data["long"])
        data["location"] = getlocation(lat, long)
    if image_url is not None:
        data["image_url"] = image_url
    data["name"] = satellite_data["info"]["satname"]
    data["id"] = satellite_data["info"]["satid"]
    return data


# route to implement the suggested search in index.html
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    if query:
        results = find_satellites_by_name(query)
        return jsonify(results)  # return the results as JSON
    return jsonify([])  # return an empty list if no query


# route to implement the suggested search for countries
@app.route("/country_search", methods=["GET"])
def country_search():
    query = request.args.get("query")
    if query:
        results = find_country_by_name(query)
        return jsonify(results)
    return jsonify([])  # return empty list if no query


# dummy data for user accounts
user_info = {
    "AlexB": {
        "username": "AlexB",
        "countries": ["USA", "India"],
        "satellites": ["20580", "25544"],
    },
    "RobL": {"username": "RobL"},
    "SermilaI": {"username": "SermilaI"},
    "TimJ": {
        "username": "TimJ",
        "countries": [],
        "satellites": ["25544"],
    },
}


@app.route("/country/<country_name>", methods=["GET"])
def country_details(country_name):
    # for now placeholder. update with sermilla code
    return f"Details for country: {country_name} (this is a placeholder) "


# Helper function to get satellite name by id.
def get_satellite_by_id(satellite_id):
    connection = sqlite3.connect("app_database.db")
    cursor = connection.cursor()
    query = "SELECT * FROM satellite WHERE id = ?"
    cursor.execute(query, (satellite_id,))
    result = cursor.fetchone()
    connection.close()
    if result:
        # Return a dictionary or an object with the necessary details
        return {
            "id": result[0],  # Assuming the id is in the first column
            "name": result[1],  # Assuming the name is in the second column
        }
    return None


def fetch_satellite_image(satellite_name):
    """Fetch a satellite image URL dynamically using Google custom
    search API"""

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    CX = os.getenv("GOOGLE_CX")

    satellite_name = satellite_name.strip().upper()

    curated_images = {
        "HST": (
            "https://upload.wikimedia.org/wikipedia/commons/3/3f/"
            "HST-SM4.jpeg"
        ),
        "ISS (ZARYA)": (
            "https://ichef.bbci.co.uk/ace/standard/3840/cpsprodpb/e7e2/"
            "live/bea2c100-3539-11ef-a647-6fc50b20e53e.jpg"
        ),
    }

    if satellite_name in curated_images:
        return curated_images[satellite_name]

    if not GOOGLE_API_KEY or not CX:
        return (
            "https://wmo.int/sites/default/files/2023-03/"
            "AdobeStock_580430822.jpeg"
        )

    search_query = f"{satellite_name} satellite"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_query,
        "cx": CX,
        "key": GOOGLE_API_KEY,
        "searchType": "image",
        "num": 1,  # Fetch only the first result
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract the image URL
        items = data.get("items", [])
        if items:
            return items[0]["link"]  # return first image url

    except requests.RequestException as e:
        print(f"Error fetching image: {e}")

    return (
        "https://wmo.int/sites/default/files/2023-03/AdobeStock_580430822.jpeg"
    )


def get_observer_location():
    """Fetches the observer's latitude and longitude based on
    their public API"""

    try:
        response = requests.get("http://ip-api.com/json")
        response.raise_for_status()
        data = response.json()
        return data.get("lat"), data.get("lon")
    except Exception as e:
        print(f"Error fetching location: {e}")
        return None


@app.route("/create_account", methods=["POST"])
def create_account():
    data = request.get_json()
    username = data.get("username")

    # Check if username is provided
    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Check if the username already exists in the database
    if check_username_exists(username):
        return (
            jsonify({"error": "User already exists"}),
            400,
        )  # Return an error if username exists

    # Add the user to the database
    try:
        add_user(username)
        return jsonify({"message": "Account created successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error creating account: {str(e)}"}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    # check if username exists

    if not check_username_exists(username):
        return jsonify({"error": "User does not exist"}), 400

    return jsonify({"message": "Login successful"}), 200


@app.route("/account/<username>")
def account(username):
    user = check_username_exists(username)
    if not user:
        return redirect(
            url_for("login")
        )  # redirect to home page if no account found

    username = user["user_name"]
    # convert satellites id to satellite name
    satellites = get_user_satellites(username)

    # get country names
    # countries = get_user_countries(username)

    # Return the account page for hte user if the account exists
    return render_template(
        "account.html",
        username=user["user_name"],
        satellites=satellites,
        # countries=countries,
    )


@app.route("/add_satellite", methods=["POST"])
def add_satellite():
    print(f"Received form data")
    try:
        data = request.get_json()  # This will parse the incoming JSON
        username = data.get("username")
        satellite_name = data.get("satellite_name")
    except Exception as e:
        return f"Error parsing JSON: {str(e)}", 400

    print(
        f"Received data: username={username}, satellite_name={satellite_name}"
    )  # Debugging line

    if not username or not satellite_name:
        return "Invalid data", 400
    try:
        # Call the function to add the satellite to the user
        add_satellite_to_user(username, satellite_name)

        # Get the updated list of satellites for the user
        updated_satellites = get_user_satellites(username)

        # Return the updated list of satellites as JSON
        return jsonify(updated_satellites)

    except ValueError as ve:
        return str(ve), 400
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/delete_satellite", methods=["POST"])
def delete_satellite():
    print(f"Received form data")
    try:
        data = request.get_json()  # This will parse the incoming JSON
        username = data.get("username")
        satellite_name = data.get(
            "satellite_name"
        )  # this could easily change to satellite id.
    except Exception as e:
        return f"Error parsing JSON: {str(e)}", 400

    print(
        f"Received data: username={username}, satellite_name={satellite_name}"
    )  # Debugging line

    if not username or not satellite_name:
        return "Invalid data", 400
    try:
        # Call the function to add the satellite to the user
        delete_satellite_from_user(username, satellite_name)

        # Get the updated list of satellites for the user
        updated_satellites = get_user_satellites(username)

        # Return the updated list of satellites as JSON
        return jsonify(updated_satellites)

    except ValueError as ve:
        return str(ve), 400
    except Exception as e:
        return f"Error: {e}", 500
