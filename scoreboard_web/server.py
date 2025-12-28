from flask import Flask, jsonify, request, render_template
import json
import os
import time

# Absolute base directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

STATE_FILE = os.path.join(BASE_DIR, "state.json")

# State Helpers

def load_state():
    if not os.path.exists(STATE_FILE):
        save_state({
            "clock_running": False,
            "elapsed_ms": 0,
            "mode": "index",
            "message": "Nachricht",
            "last_start_ts": None
        })
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def set_mode(mode, message=None):
    state = load_state()
    state["mode"] = mode
    if message is not None:
        state["message"] = message
    save_state(state)

# Clock Endpoints

@app.route("/toggle_clock", methods=["POST"])
def toggle_clock():
    state = load_state()
    now = int(time.time() * 1000)

    if not state["clock_running"]:
        # ▶ Start
        state["clock_running"] = True
        state["last_start_ts"] = now
    else:
        # ■ Stop
        state["clock_running"] = False
        if state.get("last_start_ts"):
            state["elapsed_ms"] += now - state["last_start_ts"]
        state["last_start_ts"] = None

    save_state(state)
    return jsonify(state)

@app.route("/reset_clock", methods=["POST"])
def reset_clock():
    state = load_state()
    state["clock_running"] = False
    state["elapsed_ms"] = 0
    state["last_start_ts"] = None
    save_state(state)
    return jsonify(state)

@app.route("/get_state")
def get_state():
    state = load_state()

    # Wenn Uhr läuft → aktuelle Zeit berechnen
    if state["clock_running"] and state.get("last_start_ts"):
        now = int(time.time() * 1000)
        state["current_elapsed_ms"] = (
            state["elapsed_ms"] + (now - state["last_start_ts"])
        )
    else:
        state["current_elapsed_ms"] = state["elapsed_ms"]

    # Timer-Status für Clients
    if state.get("timer_running") and state.get("timer_start_ts"):
        now_s = time.time()
        elapsed = now_s - state["timer_start_ts"]
        state["remaining_seconds"] = max(0, state.get("timer_duration", 0) - elapsed)
    else:
        state["remaining_seconds"] = state.get("timer_duration", 0)

    return jsonify(state)

# Pages

@app.route("/")
def index_page():
    set_mode("index")
    return render_template("index.html")

@app.route("/stopwatch")
def stopwatch_page():
    set_mode("stopwatch")
    return render_template("stopwatch.html")

@app.route("/message", methods=["GET", "POST"])
def message_page():
    if request.method == "POST":
        msg = request.form.get("message", "").strip()
        if not msg:
            msg = "Nachricht"
        set_mode("message", msg)
    else:
        set_mode("message")
    return render_template("message.html")

@app.route("/scores_and_teams")
def scores_and_teams_page():
    state = load_state()  # lädt die aktuelle JSON
    set_mode("scores_and_teams")
    return render_template(
        "scores_and_teams.html",
        team1=state["teams"][0],
        team2=state["teams"][1]
    )

@app.route("/update_scoreboard", methods=["POST"])
def update_scoreboard():
    data = request.get_json()
    if not data:
        return "No data received", 400

    state = load_state()
    state["mode"] = "scores_and_teams"  # wichtig: Pygame erkennt diesen Mode
    state["teams"] = data.get("teams", state.get("teams", []))
    save_state(state)

    return jsonify({"status": "ok"})

@app.route("/timer")
def timer_page():
    try:
        with open("state.json", "r") as f:
            state = json.load(f)
    except:
        state = {}

    state["mode"] = "timer"

    with open("state.json", "w") as f:
        json.dump(state, f)

    return render_template("timer.html")

@app.route("/update_timer", methods=["POST"])
def update_timer():
    data = request.json

    try:
        with open("state.json", "r") as f:
            state = json.load(f)
    except:
        state = {}

    if "duration" in data:
        state["timer_duration"] = data["duration"]
        # nur starten, wenn running = True
        if data.get("running"):
            state["timer_start_ts"] = time.time()
            state["timer_running"] = True
        else:
            state["timer_start_ts"] = None
            state["timer_running"] = False

    if data.get("running") is False:
        state["timer_running"] = False

    state["mode"] = "timer"

    with open("state.json", "w") as f:
        json.dump(state, f)

    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
