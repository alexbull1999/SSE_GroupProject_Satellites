from flask import Flask, render_template
from database import (
    get_engine,
    DATABASE_URL,
    init_db,
    populate_country_table,
)
from dotenv import load_dotenv
from blueprints import (
    register_blueprints,
)  # Import the function to register blueprints

load_dotenv()
app = Flask(__name__)

# configure production database
engine = get_engine(DATABASE_URL)

# Register all blueprints
register_blueprints(app)

if __name__ == "__main__":
    init_db(DATABASE_URL)
    populate_country_table("countries.csv", engine)
    app.run(debug=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/lookup")
def lookup():
    return render_template("search.html")


@app.route("/login_page")
def login_page():
    return render_template("login.html")
