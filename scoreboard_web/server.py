from flask import Flask, jsonify, request, send_from_directory
import json
import os

app = Flask(__name__)

STATE_FILE = "state.json"

# Hilfsfunktion: Zustand speichern
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Hilfsfunktion: Zustand laden
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
    
@app.route("/")
def index_page():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    