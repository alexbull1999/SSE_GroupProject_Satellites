from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests


app = Flask(__name__)

# dummy data for satellites
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

# dummy data for user accounts
user_info = {
    "AlexB": {"username": "AlexB"},
    "RobL": {"username": "RobL"},
    "SermilaI": {"username": "SermilaI"},
    "TimJ": {"username": "TimJ"},
}


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


@app.route("/create_account", methods=["POST"])
def create_account():
    data = request.get_json()
    username = data.get("username")
    # check if username already exists
    if username in user_info:
        return (
            jsonify({"error": "User already exists"}),
            400,
        )  # return in jsonify so java can read it.
    user_info[username] = {"username": username}
    return jsonify({"message": "Account created successfully"}), 200


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    # check if username exists
    if username not in user_info:
        return jsonify({"error": "User does not exist"}), 400
    return jsonify({"message": "Login successful"}), 200


@app.route("/account/<username>")
def account(username):
    if username not in user_info:
        return redirect(
            url_for("login")
        )  # redirect to home page if no account found

    # Return the account page for hte user if the account exists
    return render_template("account.html", username=username)


if __name__ == "__main__":
    app.run(debug=True)


def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"


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
