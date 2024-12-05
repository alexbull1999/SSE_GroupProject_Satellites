from flask import Blueprint, request, jsonify
from database import (
    check_username_exists,
    add_user,
)

login_bp = Blueprint("login", __name__, url_prefix="/login")

@login_bp.route("/create_account", methods=["POST"])
def create_account():
    data = request.get_json()
    username = data.get("username")

    # Check if username is provided
    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Check if the username already exists in the database
    if check_username_exists(username):
        return (
            jsonify({"error": "User already exists"}),
            400,
        )  # Return an error if username exists

    # Add the user to the database
    try:
        add_user(username)
        return jsonify({"message": "Account created successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error creating account: {str(e)}"}), 500


@login_bp.route("/", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    # check if username exists

    if not check_username_exists(username):
        return jsonify({"error": "User does not exist"}), 400

    return jsonify({"message": "Login successful"}), 200
