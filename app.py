from flask import Flask, render_template, request, jsonify
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
app = Flask(__name__)

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

# Satellite positions try
satellite_positions = [
    {"id": "25544", "name": "International Space Station", "lat": 28.5, "lng": 77.2},
    {"id": "20580", "name": "Hubble Space Telescope", "lat": 40.7, "lng": -74.0},
    {"id": "12345", "name": "Example Satellite", "lat": -25.5, "lng": 134.0},
]

geolocator =Nominatim(user_agent="satellite_app")
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/satellite", methods=["POST"])
def satellite():
    input_satellite = request.form.get("name")
    for satellite in all_satellites:
        if satellite["name"] == input_satellite:
            id = satellite["id"]
            start_url = "https://api.n2yo.com/rest/v1/satellite/tle/"
            end_url = "&apiKey=LMFEWE-UWEWBT-WF7CWC-5DK0"
            url = f"{start_url}{id}{end_url}"
            response = requests.get(url)
            if response.status_code == 200:
                satellite_data = response.json()
                return satellite_data
    return "404 Not Found", 404


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
def get_satellite_position(satid):
    url = f"{N2YO_API_KEY}positions/{satid}/0/0/0/1&apiKey={N2YO_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            position_data = response.json()
            if "positions" in position_data and position_data["positions"]:
                pos = position_data["positions"][0]
                return pos.get("satlatitude"), pos.get("satlongitude")

    except requests.exceptions.RequestException as e:
        print("Error fetching satellite position: {e}")
    return None, None

def get_country_from_coordinates(lat, lng):
    try:
        coord = f"{lat}, {lng}"
        location = geolocator.reverse(coord, exactly_one=True)
        if location:
            address = location.raw.get('address', {})
            return address.get('country', None)
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print("Geocoding error: {e}")
    return None


@app.route("/country", methods=["POST"])
def get_satellites_over_country():

    input_country = request.form.get("country")

    if not input_country:
        return jsonify({"error": "Please specify a country."}), 400

    url = f"{N2YO_API_BASE}above/0/0/0/90/0&apiKey={N2YO_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch satellites from API."}), 500

    all_satellites_data = response.json()
    satellites = all_satellites_data.get("above", [])

    satellites_over_country = []

    input_country_normalized = input_country.strip().lower()

    print(f"Total satellites fetched: {len(satellites)}")

    for satellite in satellites:
        satid = satellite.get("satid")
        satname = satellite.get("satname")
        sat_lat, sat_lng = get_satellite_position(satid)

        if sat_lat is not None and sat_lng is not None:
            satellite_country = get_country_from_coordinates(sat_lat, sat_lng)
            print(f"Satellite {satname} ({satid} -> Coordinates: {sat_lat}, {sat_lng}, Country: {satellite_country})")

            if satellite_country:
                satellite_country_normalized = satellite_country.strip().lower()
                if satellite_country_normalized == input_country_normalized:
                    satellites_over_country.append({
                            "id": satid,
                            "name": satellite["satname"],
                            "latitude": sat_lat,
                            "longitude": sat_lng
                    })

    if satellites_over_country:
        return jsonify({
            "country": input_country,
            "satellites": satellites_over_country
        })

    return jsonify({
        "country": input_country,
        "satellites": [],
        "message": "No satellites over this country."
    })


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
