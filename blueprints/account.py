from flask import Blueprint,  render_template, request, jsonify, redirect, url_for
from database import (
    add_country_to_user,
    add_satellite_to_user,
    get_user_satellites,
    get_user_countries,
    check_username_exists,
    delete_satellite_from_user,
    delete_country_from_user,
)

account_bp = Blueprint("account", __name__)

@account_bp.route("/account/<username>")
def account(username):
    user = check_username_exists(username)
    if not user:
        return redirect(
            url_for("login")
        )  # redirect to home page if no account found

    username = user["user_name"]
    # convert satellites id to satellite name
    satellites = get_user_satellites(username)

    # get country names
    countries = get_user_countries(username)

    # Return the account page for hte user if the account exists
    return render_template(
        "account.html",
        username=user["user_name"],
        satellites=satellites,
        countries=countries,
    )


@account_bp.route("/add_satellite", methods=["POST"])
def add_satellite():
    print("Received form data")
    try:
        data = request.get_json()  # This will parse the incoming JSON
        username = data.get("username")
        satellite_name = data.get("satellite_name")
    except Exception as e:
        return f"Error parsing JSON: {str(e)}", 400

    print(
        f"Received data: username={username}, satellite_name={satellite_name}"
    )  # Debugging line

    if not username or not satellite_name:
        return "Invalid data", 400
    try:
        # Call the function to add the satellite to the user
        add_satellite_to_user(username, satellite_name)

        # Get the updated list of satellites for the user
        updated_satellites = get_user_satellites(username)

        # Return the updated list of satellites as JSON
        return jsonify(updated_satellites)

    except ValueError as ve:
        return str(ve), 400
    except Exception as e:
        return f"Error: {e}", 500


@account_bp.route("/add_country", methods=["POST"])
def add_country():
    try:
        data = request.get_json()  # This will parse the incoming JSON
        username = data.get("username")
        country_name = data.get("country_name")
    except Exception as e:
        return f"Error parsing JSON: {str(e)}", 400

    print(
        f"Received data: username={username}, country_name={country_name}"
    )  # Debugging line

    if not username or not country_name:
        return "Invalid data", 400
    try:
        # Call the function to add the satellite to the user
        add_country_to_user(username, country_name)

        # Get the updated list of satellites for the user
        updated_countries = get_user_countries(username)

        # Return the updated list of satellites as JSON
        return jsonify(updated_countries)

    except ValueError as ve:
        return str(ve), 400
    except Exception as e:
        return f"Error: {e}", 500


@account_bp.route("/delete_satellite", methods=["POST"])
def delete_satellite():
    print("Received form data")
    try:
        data = request.get_json()  # This will parse the incoming JSON
        username = data.get("username")
        satellite_name = data.get(
            "satellite_name"
        )  # this could easily change to satellite id.
    except Exception as e:
        return f"Error parsing JSON: {str(e)}", 400

    print(
        f"Received data: username={username}, satellite_name={satellite_name}"
    )  # Debugging line

    if not username or not satellite_name:
        return "Invalid data", 400
    try:
        # Call the function to add the satellite to the user
        delete_satellite_from_user(username, satellite_name)

        # Get the updated list of satellites for the user
        updated_satellites = get_user_satellites(username)

        # Return the updated list of satellites as JSON
        return jsonify(updated_satellites)

    except ValueError as ve:
        return str(ve), 400
    except Exception as e:
        return f"Error: {e}", 500


@account_bp.route("/delete_country", methods=["POST"])
def delete_country():
    try:
        data = request.get_json()  # This will parse the incoming JSON
        username = data.get("username")
        country_name = data.get("country_name")
    except Exception as e:
        return f"Error parsing JSON: {str(e)}", 400

    print(f"Received data: username={username}, country_name={country_name}")

    if not username or not country_name:
        return "Invalid data", 400

    try:
        # Call the function to delete the country from the user's tracking list
        delete_country_from_user(username, country_name)

        # Get the updated list of countries for the user
        updated_countries = get_user_countries(username)

        # Return the updated list of countries as JSON
        return jsonify(updated_countries)

    except ValueError as ve:
        return str(ve), 400
    except Exception as e:
        return f"Error: {e}", 500
