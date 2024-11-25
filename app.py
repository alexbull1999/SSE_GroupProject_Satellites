from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    return "<h1> TOTALLY USELESS APP; no really</h1"


def process_query(query):
    if query.lower() == "moon":
        return "Moon made of cheese"
