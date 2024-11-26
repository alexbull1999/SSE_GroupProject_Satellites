from flask import Flask, render_template, request, jsonify
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
            url = f"https://api.n2yo.com/rest/v1/satellite/tle/{id}&apiKey=LMFEWE-UWEWBT-WF7CWC-5DK0"
            response = requests.get(url)
            if response.status_code == 200:
                satellite_data = response.json()
                return satellite_data
    return "404 Not Found", 404


def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"


# url = f"https://tle.ivanstanojevic.me/api/tle/{id}"
# data = []
# response = requests.get(url)
# if response.status_code == 200:
# data = response.json()

#       return render_template("satellite.html", satellite=satellite_data)
