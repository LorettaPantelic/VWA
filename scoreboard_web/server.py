from flask import Flask, jsonify, request, render_template
import json
import os

# Absolute base directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Explicitly define template and static directories
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# Absolute path to the state file
STATE_FILE = os.path.join(BASE_DIR, "state.json")

# Helper function: save application state to disk
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Helper function: load application state from disk
def load_state():
    if not os.path.exists(STATE_FILE):
        save_state({"clock_running": False})
    with open(STATE_FILE, "r") as f:
        return json.load(f)

@app.route("/toggle_clock", methods=["POST"])
def toggle_clock():
    state = load_state()
    state["clock_running"] = not state["clock_running"]
    save_state(state)
    return jsonify(state)

@app.route("/get_state")
def get_state():
    return jsonify(load_state())

# HTML is loaded from the templates directory using Flask's standard mechanism
@app.route("/")
def index_page():
    return render_template("index.html")

@app.route("/stopwatch")
def stopwatch_page():
    return render_template("stopwatch.html")

@app.route("/message")
def message_page():
    return render_template("message.html")

@app.route("/scores_and_teams")
def scores_and_teams_page():
    return render_template("scores_and_teams.html")

@app.route("/timer")
def timer_page():
    return render_template("timer.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
