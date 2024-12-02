from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import sqlite3
from database import (
    get_engine,
    DATABASE_URL,
    init_db,
    find_satellites_by_name,
    populate_country_table,
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


@app.route("/satellite", methods=["GET"])
def satellite():
    input_satellite = request.args.get("name")

    if not input_satellite:
        return "Satellite name is required", 400

    # Connect to the database and fetch corresponding satellite ID
    try:
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
            API_KEY = os.getenv("API_KEY")
            start_url = "https://api.n2yo.com/rest/v1/satellite/tle/"
            end_url = f"&apiKey={API_KEY}"
            url = f"{start_url}{satellite_id}{end_url}"
            response = requests.get(url)
            if response.status_code == 200:
                satellite_data = response.json()
                image_url = None
                if "url" in result:
                    image_url = url
                data = generateSatData(image_url, satellite_data)
                return render_template("satellite.html", satellite=data)
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


N2YO_API_BASE = "https://api.n2yo.com/rest/v1/satellite/"

# Hardcoded country data try
country_data = {
    "USA": {"lat": 37.0902, "lng": -95.7129},
    "India": {"lat": 20.5937, "lng": 78.9629},
    "Turkey": {"lat": 38.9637, "lng": 35.2433},
}


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
        query = "SELECT * FROM satellite WHERE name = ?"
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

            # Construct the API request URL for fetching satellites above the country
            NY20_API_BASE = "https://api.n2yo.com/rest/v1/satellite/"
            url = (
                f"{NY20_API_BASE}above/{observer_lat}/{observer_lng}/{observer_alt}/"
                f"{search_radius}/{category_id}/&apiKey={API_KEY}"
            )

            # Send the request to the N2YO API
            response = requests.get(url)

            satellites = []

            # Process the API response
            if (
                response.status_code == 200
            ):  # Check if the request was successful
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
                return "Failed to retrieve satellite data from API"  # Set an empty list if the request was unsuccessful

            # Render the country.html template with the satellite data
            # and the selected country
            error_message = "No satellites currently above this country"
            return render_template(
                "country.html",
                country=input_country,  # The country name for the display
                satellites=satellites,  # List of satellites above the country
                message=None if satellites else error_message,
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
    url_start = "https://api.openweathermap.org/geo/1.0/reverse?"
    url_lat_long = f"lat={dms_to_decimal(lat)}&lon={dms_to_decimal(long)}"
    url_end = "&limit=5&appid=41e586f2e94d706bdda4da03e56922e5"
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


@app.route("/create_account", methods=["POST"])
def create_account():
    data = request.get_json()
    username = data.get("username")
    # check if username already exists
    if username in user_info:
        return (
            jsonify({"error": "User already exists"}),
            400,
        )  # return in jsonify so java can read it.
    user_info[username] = {"username": username}
    return jsonify({"message": "Account created successfully"}), 200


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    # check if username exists
    if username not in user_info:
        return jsonify({"error": "User does not exist"}), 400
    return jsonify({"message": "Login successful"}), 200


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


@app.route("/account/<username>")
def account(username):
    if username not in user_info:
        return redirect(url_for("login"))
        # redirect to home page if no account found

    # retrive user data
    user = user_info[username]

    # convert satellites id to satellite name
    satellites = [
        get_satellite_by_id(satellite_id)
        for satellite_id in user.get("satellites", [])
    ]

    # get country names
    countries = user.get("countries", [])

    # Return the account page for hte user if the account exists
    return render_template(
        "account.html",
        username=user["username"],
        satellites=satellites,
        countries=countries,
    )
