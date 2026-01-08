from flask import Flask, jsonify, request, render_template
import json
import os
import time
import subprocess

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
            "stopwatch_running": False,
            "elapsed_ms": 0,
            "last_start_ts": None,

            "game_clock_running": False,
            "game_elapsed_ms": 0,
            "game_last_start_ts": None,

            "mode": "index",
            "message": "Nachricht"
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

# -------- API: State --------
@app.route("/get_state")
def get_state():
    state = load_state()

    # If the clock is running → calculate current time

    if state["stopwatch_running"] and state.get("last_start_ts"):
        now = int(time.time() * 1000)
        state["current_elapsed_ms"] = (
            state["elapsed_ms"] + (now - state["last_start_ts"])
        )
    else:
        state["current_elapsed_ms"] = state["elapsed_ms"]

    # Timer state for clients
    if state.get("timer_running") and state.get("timer_start_ts"):
        now_s = time.time()
        elapsed = now_s - state["timer_start_ts"]
        state["remaining_seconds"] = max(0, state.get("timer_duration", 0) - elapsed)
    else:
        state["remaining_seconds"] = state.get("timer_duration", 0)

    # Game clock
    if state.get("game_clock_running") and state.get("game_last_start_ts"):
        now = int(time.time() * 1000)
        state["game_current_elapsed_ms"] = (
            state.get("game_elapsed_ms", 0)
            + (now - state["game_last_start_ts"])
        )
    else:
        state["game_current_elapsed_ms"] = state.get("game_elapsed_ms", 0)

    return jsonify(state)

# -------- API: Scores_and_teams --------
@app.route("/scoreboard/update", methods=["POST"])
def scoreboard_update():
    data = request.get_json()
    if not data:
        return "No data received", 400

    state = load_state()
    state["mode"] = "scores_and_teams"
    state["teams"] = data.get("teams", state.get("teams", []))
    save_state(state)

    return jsonify({"status": "ok"})

@app.route("/game_clock/toggle", methods=["POST"])
def game_clock_toggle():
    state = load_state()
    now = int(time.time() * 1000)

    if not state.get("game_clock_running"):
        # Start
        state["game_last_start_ts"] = now
        state["game_clock_running"] = True
    else:
        # Stop
        state["game_elapsed_ms"] = state.get("game_elapsed_ms", 0) + (
            now - state["game_last_start_ts"]
        )
        state["game_last_start_ts"] = None
        state["game_clock_running"] = False

    save_state(state)
    return "", 204

@app.route("/game_clock/reset", methods=["POST"])
def game_clock_reset():
    state = load_state()

    state["game_elapsed_ms"] = 0
    state["game_clock_running"] = False
    state["game_last_start_ts"] = None

    save_state(state)
    return "", 204

# -------- API: Stopwatch --------
@app.route("/toggle_stopwatch", methods=["POST"])
def toggle_stopwatch():
    state = load_state()
    now = int(time.time() * 1000)

    if not state["stopwatch_running"]:
        # ▶ Start
        state["stopwatch_running"] = True
        state["last_start_ts"] = now
    else:
        # ■ Stop
        state["stopwatch_running"] = False
        if state.get("last_start_ts"):
            state["elapsed_ms"] += now - state["last_start_ts"]
        state["last_start_ts"] = None

    save_state(state)
    return jsonify(state)

@app.route("/reset_stopwatch", methods=["POST"])
def reset_stopwatch():
    state = load_state()
    state["stopwatch_running"] = False
    state["elapsed_ms"] = 0
    state["last_start_ts"] = None
    save_state(state)
    return jsonify(state)

# -------- API: Timer --------
@app.route("/timer/update", methods=["POST"])
def timer_update():
    data = request.json

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except:
        state = {}

    now = time.time()

    # Start timer
    if data.get("running") is True:
        # If the timer is already running, do nothing
        if not state.get("timer_running", False):
            state["timer_start_ts"] = now
            # If a duration is provided, set a new duration
            if "duration" in data:
                state["timer_duration"] = data["duration"]
            state["timer_running"] = True

    # Stop timer
    elif data.get("running") is False:
        if state.get("timer_running") and state.get("timer_start_ts"):
            elapsed = now - state["timer_start_ts"]
            state["timer_duration"] = max(0, state.get("timer_duration", 0) - elapsed)
        state["timer_start_ts"] = None
        state["timer_running"] = False
        # If a duration is provided (preset or manual input)
        if "duration" in data:
            state["timer_duration"] = data["duration"]

    # Only set duration (preset or manual), timer is not running
    elif "duration" in data:
        state["timer_duration"] = data["duration"]
        state["timer_running"] = False
        state["timer_start_ts"] = None

    state["mode"] = "timer"

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

    return "", 204

# -------- API: TV --------
@app.route("/tv/<action>")
def tv_control(action):
    if action == "on":
        subprocess.run('echo "on 0" | cec-client -s -d 1', shell=True)
    elif action == "off":
        subprocess.run('echo "standby 0" | cec-client -s -d 1', shell=True)
    return "", 204

# Pages

@app.route("/")
def index_page():
    set_mode("index")
    return render_template("index.html")

@app.route("/scores_and_teams")
def scores_and_teams_page():
    state = load_state()
    set_mode("scores_and_teams")
    return render_template(
        "scores_and_teams.html",
        team1=state["teams"][0],
        team2=state["teams"][1]
    )

@app.route("/stopwatch")
def stopwatch_page():
    set_mode("stopwatch")
    return render_template("stopwatch.html")

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
