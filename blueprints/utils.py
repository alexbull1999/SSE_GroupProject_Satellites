import requests
import sqlite3
import os
import ephem
import math
import pycountry

def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"


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

