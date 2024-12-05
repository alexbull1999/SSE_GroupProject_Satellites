from flask import Blueprint, render_template, request, jsonify, redirect, url_for, requests, sqlite3
import os
from database import (
    find_satellites_by_name,
    find_country_by_name,
    add_satellite_to_user,
    get_user_satellites,
    check_username_exists,
    add_user,
    delete_satellite_from_user,
)
from .utils import (
    generateSatData,
    fetch_satellite_image,
    get_observer_location,
)

satellites = Blueprint("satellites", __name__, url_prefix="/satellites")


@satellites.route("/", methods=["GET"])
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


@satellites.route("/<int:satellite_id>", methods=["GET"])
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


@satellites.route("/country", methods=["GET"])
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


# route to implement the suggested search in index.html
@satellites.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    if query:
        results = find_satellites_by_name(query)
        return jsonify(results)  # return the results as JSON
    return jsonify([])  # return an empty list if no query


# route to implement the suggested search for countries
@satellites.route("/country_search", methods=["GET"])
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


@satellites.route("/country/<country_name>", methods=["GET"])
def country_details(country_name):
    # for now placeholder. update with sermilla code
    return f"Details for country: {country_name} (this is a placeholder) "

@satellites.route("/create_account", methods=["POST"])
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


@satellites.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    # check if username exists

    if not check_username_exists(username):
        return jsonify({"error": "User does not exist"}), 400

    return jsonify({"message": "Login successful"}), 200


@satellites.route("/account/<username>")
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


@satellites.route("/add_satellite", methods=["POST"])
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


@satellites.route("/delete_satellite", methods=["POST"])
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
