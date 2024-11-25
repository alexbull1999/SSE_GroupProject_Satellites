from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"
