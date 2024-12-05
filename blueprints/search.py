from flask import Blueprint, request, jsonify
from database import (
    find_satellites_by_name,
    find_country_by_name,
)

search_bp = Blueprint('search', __name__)

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
    # for now placeholder. update with sermila code
    return f"Details for country: {country_name} (this is a placeholder) "











