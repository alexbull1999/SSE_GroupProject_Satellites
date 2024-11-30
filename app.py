import ephem
import math
from flask import Flask, render_template, request
import requests
import pycountry


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
                tle_lines = satellite_data["tle"].split("\r\n")
                name = satellite_data["info"]["satname"]
                tle = [name, tle_lines[0], tle_lines[1]]
                data = pyephem(tle)
                data["name"] = input_satellite
                data["id"] = satellite_data["info"]["satid"]
                if "url" in satellite:
                    data["url"] = satellite["url"]
                lat = str(data["lat"])
                long = str(data["long"])
                data["location"] = getlocation(lat, long)
                return render_template("satellite.html", satellite=data)
                # return pyephem(tle)
    return "404 Not Found", 404


def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"


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
        if location[0]["country"] is not None:
            code = location[0]["country"].upper()
            country = pycountry.countries.get(alpha_2=code)
            location_string = country.name if country else code
            if location[0]["state"] is not None:
                state = location[0]["state"]
                location_string = location_string + ", " + state
                if location[0]["name"] is not None:
                    name = location[0]["name"]
                    location_string = location_string + ", " + name
        return location_string
    return "No location Found"

    # 41e586f2e94d706bdda4da03e56922e5


# url = f"https://tle.ivanstanojevic.me/api/tle/{id}"
# data = []
# response = requests.get(url)
# if response.status_code == 200:
# data = response.json()

#       return render_template("satellite.html", satellite=satellite_data)
