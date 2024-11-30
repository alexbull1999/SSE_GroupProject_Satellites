from pickletools import long1
from unicodedata import decimal

import ephem
import math
from flask import Flask, render_template, request
import requests


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
                tle_lines = satellite_data["tle"].split('\r\n')

                tle = [satellite_data["info"]["satname"], tle_lines[0], tle_lines[1]]
                data = pyephem(tle)
                data["name"] = satellite_data["info"]["satname"]
                data["id"] = satellite_data["info"]["satid"]
                #data["location"] = getlocation(data["lat"], data["long"])
                string = "28:15:49.9"
                return dms_to_decimal(string)
                #return render_template("satellite.html", satellite=data)
                #return pyephem(tle)
    return "404 Not Found", 404


def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"

def dms_to_decimal(dms_str):
    d, m, s = map(float, dms_str.split(":"))
    decimal = float(d) + (float(m) / 60) + (float(s) / 3600)
    return str(decimal)

def pyephem(tle):

    EARTH_RADIUS = 6371.0
    EARTH_GRAVITY = 398600.4418 # km^3/s^2

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
    orbital_velocity = math.sqrt(EARTH_GRAVITY / (EARTH_RADIUS + elevation))
    ground_speed = orbital_velocity * (EARTH_RADIUS / (EARTH_RADIUS + elevation))

    data = {
        "lat": lat,
        "long": long,
        #"lat": lat,
        #"long": long,
        "elevation": "{:.0f}".format(elevation),
        "ground_speed": round(ground_speed, 2)
    }
    return data

def getlocation(lat, long):
    url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={long}&limit=5&appid=41e586f2e94d706bdda4da03e56922e5"
    response = requests.get(url)
    if response.status_code == 200:
        location = response.json()
        return location

    #41e586f2e94d706bdda4da03e56922e5

# url = f"https://tle.ivanstanojevic.me/api/tle/{id}"
# data = []
# response = requests.get(url)
# if response.status_code == 200:
# data = response.json()

#       return render_template("satellite.html", satellite=satellite_data)
