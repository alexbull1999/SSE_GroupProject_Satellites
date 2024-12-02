from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
from database import get_engine, DATABASE_URL, init_db, find_satellites_by_name
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# configure production database
engine = get_engine(DATABASE_URL)


if __name__ == "__main__":
    init_db(DATABASE_URL)
    app.run(debug=True)


all_satellites = [
    {
        "id": "25544",
        "name": "International Space Station",
    },
    {
        "id": "20580",
        "name": "Hubble Space Telescope",
    },
]


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

# Hardcoded country data try
country_data = {
    "USA": {"lat": 37.0902, "lng": -95.7129},
    "India": {"lat": 20.5937, "lng": 78.9629},
    "Turkey": {"lat": 38.9637, "lng": 35.2433},
}
@app.route("/country", methods=["POST"])
def get_satellites_over_country():
    """
       Retrieve satellites currently over a specified country using the N2YO API.
       """
    # Extract the country name from the form input
    input_country = request.form.get("country")

    # Render the country.html page with an error if the input country is not in the country database
    if input_country not in country_data:
        return render_template(
            "country.html",
            country=None, # No country to display
            satellites=[], # No satellites found
            message = "Country not found.") # Error message for the user

    #Extract the latitude and longitude for the specified country
    observer_lat = country_data[input_country]["lat"]
    observer_lng = country_data[input_country]["lng"]

    # Define additional parameters for the satellite search
    observer_alt = 0  # Default altitude in meters
    search_radius = 10  # Search radius in degrees
    category_id = 0 # 0 for all categories

    satellites = []

    # Extract the API key
    API_KEY = os.getenv("API_KEY")
    # Construct the API request URL for fetching satellites above the country
    url = f"{N2YO_API_BASE}above/{observer_lat}/{observer_lng}/{observer_alt}/{search_radius}/{category_id}/&apiKey={API_KEY}"
    # Send the request to the N2YO API
    response = requests.get(url)

    # Process the API response
    if response.status_code == 200: # Check if the request was successful
        # Parse the response JSON to extract satellite data
        data = response.json()
        for sat in data.get("above", []):  # Iterate through the satellites in the "above" field
            satellites.append({
                "id": sat.get("satid"),
                "name": sat.get("satname"),
            })
    else:
        satellites = [] # Set an empty list if the request was unsuccessful

    # Render the country.html template with the satellite data and the selected country
    return render_template(
        "country.html",
        country=input_country,  # The country name for the display
        satellites=satellites,  # The list of satellites above the country
        message=None if satellites else "No satellites currently above this country"
    )


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
