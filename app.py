from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import sqlite3
from database import (
    get_engine,
    DATABASE_URL,
    init_db,
    find_satellites_by_name,
    get_satellite_by_id,
    add_satellite_to_user,
    get_user_satellites,
    check_username_exists,
    add_user,
    get_satellite_id_by_name,
    delete_satellite_from_user
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


@app.route("/country", methods=["POST"])
def get_satellites_over_country():
    """
    Retrieve satellites currently over a specified country using the N2YO API.
    """

    # Extract the country name from the form input
    input_country = request.form.get("country")

    # If no country specified, render the country.html page with error message
    if not input_country:
        return render_template(
            "country.html",
            country=None,  # No country to display
            satellites=[],  # No satellites found
            message="Please specify a country",
        )  # Error message for the user

    # Initialize an empty list to store satellites found above the country
    satellites_over_country = []

    # Hardcoded country data try
    country_data = {
        "USA": {"lat": 37.0902, "lng": -95.7129},
        "India": {"lat": 20.5937, "lng": 78.9629},
        "Turkey": {"lat": 38.9637, "lng": 35.2433},
    }

    # Render page with an error if input country is not in the country database
    if input_country not in country_data:
        return render_template(
            "country.html",
            country=input_country,
            satellites=[],
            message="Country not found.",
        )

    # Extract the latitude and longitude for the specified country
    country_coords = country_data[input_country]
    observer_lat = country_coords["lat"]
    observer_lng = country_coords["lng"]

    # Define additional parameters for the satellite search
    observer_alt = 0  # Default altitude in meters
    search_radius = 90  # Search radius in degrees
    category_id = 0  # 0 to search for all satellite categories

    try:
        API_KEY = os.getenv("API_KEY")
        # Construct the API request URL for fetching satellites above country
        start_url = f"{N2YO_API_BASE}above/{observer_lat}/"
        middle_url = f"{observer_lng}/{observer_alt}/"
        end_url = f"{search_radius}/{category_id}/&apiKey={API_KEY}"
        # Send the request to the N2YO API
        response = requests.get(start_url + middle_url + end_url)

        # Return an error message if response status not successful
        if response.status_code != 200:
            return render_template(
                "country.html",
                country=input_country,
                satellites=[],
                message="Failed to fetch data from N2YO API.",
            )

        # Parse the response JSON to extract satellite data
        data = response.json()

        # Loop through satellites listed in the "above" field of the response
        for sat in data.get("above", []):
            satellites_over_country.append(
                {
                    "id": sat.get("satid"),
                    "name": sat.get("satname"),
                    "latitude": sat.get("satlat"),
                    "longitude": sat.get("satlng"),
                }
            )

        # Render country.html with the found satellites and country name
        over = satellites_over_country
        ic = input_country
        return render_template("country.html", country=ic, satellites=over)

    except Exception as e:
        # Handle any unexpected exceptions during API request / data processing
        ic = input_country
        return render_template(
            "country.html", country=ic, satellites=[], message=str(e)
        )


if __name__ == "__main__":
    init_db(DATABASE_URL)
    app.run(debug=True)


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
        satellite_name = data.get("satellite_name") #this could easily change to satellite id.
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




""" CHATGPT suggestion
@app.route('/delete_satellite', methods=['POST'])
def delete_satellite():
    data = request.get_json()
    user_id = data.get('user_id')
    satellite_id = data.get('satellite_id')

    if not user_id or not satellite_id:
        return jsonify({'error': 'Missing user_id or satellite_id'}), 400

    # Assuming user_satellite_table is already defined in your SQLAlchemy setup
    delete_stmt = user_satellite_table.delete().where(
        user_satellite_table.c.user_id == user_id,
        user_satellite_table.c.satellite_id == satellite_id
    )

    with engine.connect() as conn:
        conn.execute(delete_stmt)
        conn.commit()

    return jsonify({'message': 'Satellite deleted successfully'})
"""