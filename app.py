from flask import Flask, render_template, request

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
            return render_template("satellite.html", id=id)
    return "404 Not Found", 404


def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"
