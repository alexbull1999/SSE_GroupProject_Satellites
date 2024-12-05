from flask import Blueprint, render_template, request, jsonify
import requests
import sqlite3
import os

from utils import (
    get_observer_location,
    generateSatData,
    fetch_satellite_image
)

satellites_bp = Blueprint("satellites", __name__, url_prefix="/satellites")
@satellites_bp.route("/", methods=["GET"])
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


@satellites_bp.route("/<int:satellite_id>", methods=["GET"])
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
