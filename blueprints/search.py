from flask import Blueprint, request, jsonify, redirect, url_for

from database import (
    find_satellites_by_name,
    find_country_by_name,
)

search_bp = Blueprint("search", __name__)


# route to implement the suggested search in index.html
@search_bp.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    if query:
        results = find_satellites_by_name(query)
        return jsonify(results)  # return the results as JSON
    return jsonify([])  # return an empty list if no query


# route to implement the suggested search for countries
@search_bp.route("/country_search", methods=["GET"])
def country_search():
    query = request.args.get("query")
    if query:
        results = find_country_by_name(query)
        return jsonify(results)
    return jsonify([])  # return empty list if no query


@search_bp.route("/country/<country_name>", methods=["GET"])
def country_details(country_name):
    # Redirect to country page
    return redirect(
        url_for("country.get_satellites_over_country", country=country_name)
    )
