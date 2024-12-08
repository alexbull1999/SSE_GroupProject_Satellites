from flask import Blueprint, render_template, request, jsonify
import requests
import sqlite3
import os

country_bp = Blueprint("country", __name__, url_prefix="/country")


@country_bp.route("/", methods=["GET"])
def get_satellites_over_country():
    """
    Retrieve satellites currently over a specified country using the N2YO API.
    """
    # Extract the country name from the form input
    input_country = request.args.get("country")

    if not input_country:
        return "Country name is required", 400

    # Connect to the database and fetch matching country names
    try:
        connection = sqlite3.connect("app_database.db")
        cursor = connection.cursor()

        # Query to get the satellite ID based on the name
        query = "SELECT * FROM country WHERE name = ?"
        cursor.execute(query, (input_country,))
        result = cursor.fetchone()  # Fetch first result

        connection.close()

        # Check if result was found
        if result:
            observer_lat = result[1]
            observer_lng = result[2]
            search_radius = result[5]
            observer_alt = 0
            category_id = 0

            # Extract API key
            API_KEY = os.getenv("API_KEY")
            if not API_KEY:
                return "API key is missing in environment variables", 500

            # Construct API request URL for fetching satellites above country
            NY20_API_BASE = "https://api.n2yo.com/rest/v1/satellite/"
            url = (
                f"{NY20_API_BASE}above/{observer_lat}/{observer_lng}/"
                f"{observer_alt}/"
                f"{search_radius}/{category_id}/&apiKey={API_KEY}"
            )

            # Send the request to the N2YO API
            response = requests.get(url)

            satellites = []

            # Process the API response
            if response.status_code == 200:
                # Check if the request was successful
                # Parse the response JSON to extract satellite data
                data = response.json()
                for sat in data.get(
                    "above", []
                ):  # Iterate through the satellites in the "above" field
                    satellites.append(
                        {
                            "id": sat.get("satid"),
                            "name": sat.get("satname"),
                        }
                    )
            else:
                return "Failed to retrieve satellite data from API", 500

            # Render the country.html template with the satellite data
            # and the selected country
            error_message = "No satellites currently above this country"
            return render_template(
                "country.html",
                country=input_country,  # The country name for the display
                satellites=satellites,  # List of satellites above the country
                error_message=None if satellites else error_message,
            )

        else:
            error_message = f"Sorry we can't find the country, f{input_country}"
            return render_template("notFound.html", error_code=404, error_message=error_message), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
