from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
from database import get_engine, DATABASE_URL, init_db, find_satellites_by_name

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
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
            start_url = "https://api.n2yo.com/rest/v1/satellite/tle/"
            end_url = "&apiKey=LMFEWE-UWEWBT-WF7CWC-5DK0"
            url = f"{start_url}{satellite_id}{end_url}"
            response = requests.get(url)
            if response.status_code == 200:
                satellite_data = response.json()
                return satellite_data
        else:
            return "404 Not Found", 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/satellite/<int:satellite_id>", methods=["GET"])
def satellite_by_id(satellite_id):
    # Search for the satellite by ID
    start_url = "https://api.n2yo.com/rest/v1/satellite/tle/"
    end_url = "&apiKey=LMFEWE-UWEWBT-WF7CWC-5DK0"
    url = f"{start_url}{satellite_id}{end_url}"
    response = requests.get(url)
    if response.status_code == 200:
        satellite_data = response.json()
        # change to return to the render template satellite.html
        return satellite_data
    return "404 Not Found", 404

def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"


N2YO_API_BASE = "https://api.n2yo.com/rest/v1/satellite/"
N2YO_API_KEY = "LMFEWE-UWEWBT-WF7CWC-5DK0"

@app.route("/country", methods=["POST"])
def get_satellites_over_country():
    """
       Retrieve satellites currently over a specified country using the N2YO API.
       """

    # Extract the country name from the form input
    input_country = request.form.get("country")

    # If no country is specified, render the country.html page with an error message
    if not input_country:
        return render_template(
            "country.html",
            country=None, # No country to display
            satellites=[], # No satellites found
            message = "Please specify a country" ) # Error message for the user

    # Initialize an empty list to store satellites found above the country
    satellites_over_country = []

    # Hardcoded country data try
    country_data = {
        "USA": {"lat": 37.0902, "lng": -95.7129},
        "India": {"lat": 20.5937, "lng": 78.9629},
        "Turkey": {"lat": 38.9637, "lng": 35.2433},
    }

    # Render the country.html page with an error if the input country is not in the country database
    if input_country not in country_data:
        return render_template(
            "country.html",
            country=input_country,
            satellites=[],
            message="Country not found.")

    #Extract the latitude and longitude for the specified country
    country_coords = country_data[input_country]
    observer_lat = country_coords["lat"]
    observer_lng = country_coords["lng"]

    # Define additional parameters for the satellite search
    observer_alt = 0  # Default altitude in meters
    search_radius = 90  # Search radius in degrees
    category_id = 0  # 0 to search for all satellite categories

    try:
        # Construct the API request URL for fetching satellites above the country
        url = f"{N2YO_API_BASE}above/{observer_lat}/{observer_lng}/{observer_alt}/{search_radius}/{category_id}/&apiKey={N2YO_API_KEY}"
        # Send the request to the N2YO API
        response = requests.get(url)

        # Return an error message if response status not successful
        if response.status_code != 200:
            return render_template(
                "country.html",
                country=input_country,
                satellites=[],
                message="Failed to fetch data from N2YO API.")

        # Parse the response JSON to extract satellite data
        data = response.json()

        # Loop through the satellites listed in the "above" field of the response
        for sat in data.get("above", []):
            satellites_over_country.append({
                "id": sat.get("satid"),
                "name": sat.get("satname"),
                "latitude": sat.get("satlat"),
                "longitude": sat.get("satlng"),
            })

        # Render the country.html template with the found satellites and country name
        return render_template(
            "country.html",
            country=input_country,
            satellites=satellites_over_country)

    except Exception as e:
        # Handle any unexpected exceptions during the API request or data processing
        return render_template(
            "country.html",
            country=input_country,
            satellites=[],
            message=str(e))

if __name__ == "__main__":
    init_db(DATABASE_URL)
    app.run(debug=True)

# url = f"https://tle.ivanstanojevic.me/api/tle/{id}"
# data = []
# response = requests.get(url)
# if response.status_code == 200:
# data = response.json()

#       return render_template("satellite.html", satellite=satellite_data)
# function to mock test api

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


# route to implement the suggested search in index.html
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    if query:
        results = find_satellites_by_name(query)
        return jsonify(results)  # return the results as JSON
    return jsonify([])  # return an empty list if no query
