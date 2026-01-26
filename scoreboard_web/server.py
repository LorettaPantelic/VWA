from flask import Flask, jsonify, request, render_template, send_from_directory
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

            "buzzer1_running": False,
            "buzzer1_elapsed_ms": 0,
            "buzzer1_last_start_ts": None,

            "buzzer2_running": False,
            "buzzer2_elapsed_ms": 0,
            "buzzer2_last_start_ts": None,

            "mode": "index",
            "message": "Nachricht",

            "sport": ""  # NEW: default empty sport
        })
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    # Ensure 'sport' key exists in case old JSON doesn't have it
    if "sport" not in state:
        state["sport"] = ""

    return state

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)
        f.flush()
        os.fsync(f.fileno())

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

    if state.get("winner_locked") and state.get("winner_start_ts"):
        if time.time() - state["winner_start_ts"] > 5:
            state["winner_locked"] = False
            state["winner_name"] = None
            state["winner_start_ts"] = None
            save_state(state)

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

    # --- Update teams ---
    old_scores = [team.get("score", 0) for team in state.get("teams", [])]
    new_scores = data.get("teams", old_scores)
    state["teams"] = new_scores

    # --- Reset winner_locked if scores changed ---
    new_score_values = [team.get("score", 0) for team in new_scores]
    if new_score_values != old_scores:
        state["winner_locked"] = False

    # --- Save sport if provided ---
    if "sport" in data:
        state["sport"] = data["sport"]

    sport = state.get("sport", "").lower()

    # --- Helper: stop game clock safely ---
    def stop_game_clock(winner_name):
        now = int(time.time() * 1000)

        if state.get("game_clock_running") and state.get("game_last_start_ts"):
            state["game_elapsed_ms"] = state.get("game_elapsed_ms", 0) + (
                now - state["game_last_start_ts"]
            )

        state["game_clock_running"] = False
        state["game_last_start_ts"] = None

        state["winner_locked"] = True
        state["winner_name"] = winner_name
        state["winner_start_ts"] = time.time()

    # --- Volleyball ---
    if sport == "volleyball" and len(state["teams"]) >= 2 and not state.get("winner_locked", False):
        sa = state["teams"][0].get("score", 0)
        sb = state["teams"][1].get("score", 0)
    if max(sa, sb) >= 25 and abs(sa - sb) >= 2:
        winner = state["teams"][0]["name"] if sa > sb else state["teams"][1]["name"]
        stop_game_clock(winner)

    # --- Badminton ---
    if sport == "badminton" and len(state["teams"]) >= 2 and not state.get("winner_locked", False):
        sa = state["teams"][0].get("score", 0)
        sb = state["teams"][1].get("score", 0)

        if (
            (max(sa, sb) >= 21 and abs(sa - sb) >= 2)
            or sa == 30
            or sb == 30
        ):
            winner = state["teams"][0]["name"] if sa > sb else state["teams"][1]["name"]
            stop_game_clock(winner)

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

@app.route("/scoreboard/trigger_winner", methods=["POST"])
def trigger_winner():
    data = request.get_json()
    team_index = int(data.get("team", 0)) - 1

    state = load_state()

    if team_index not in (0, 1):
        return "Invalid team", 400

    winner_team = state["teams"][team_index]

    state["winner_locked"] = True
    state["winner_name"] = winner_team["name"]
    state["winner_start_ts"] = time.time()
    state["game_clock_running"] = False
    state["game_last_start_ts"] = None

    save_state(state)
    return jsonify({"winner_name": winner_team["name"]})

@app.route("/scoreboard/reset_all", methods=["POST"])
def scoreboard_reset_all():
    state = load_state()

    state["teams"] = [
        {"name": "Team 1", "score": 0, "color": [11, 173, 254]},
        {"name": "Team 2", "score": 0, "color": [214, 76, 76]},
    ]

    state["sport"] = ""
    state["winner_locked"] = False

    state["game_elapsed_ms"] = 0
    state["game_clock_running"] = False
    state["game_last_start_ts"] = None

    save_state(state)
    return "", 204

# -------- API: Stopwatch --------
@app.route("/stopwatch/toggle", methods=["POST"])
def stopwatch_toggle():
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

@app.route("/stopwatch/reset", methods=["POST"])
def stopwatch_reset():
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
    state = load_state()
    now = time.time()

    # Start timer
    if data.get("running") is True:
        if not state.get("timer_running", False):
            state["timer_start_ts"] = now
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
        if "duration" in data:
            state["timer_duration"] = data["duration"]

    # Only set duration (preset/manual), timer is not running
    elif "duration" in data:
        state["timer_duration"] = data["duration"]
        state["timer_running"] = False
        state["timer_start_ts"] = None

    state["mode"] = "timer"
    save_state(state)
    return "", 204

# -------- API: Buzzer Stopwatch --------
@app.route("/buzzer/<int:buzzer_id>/toggle", methods=["POST"])
def buzzer_toggle(buzzer_id):
    state = load_state()
    now = int(time.time() * 1000)

    buzzer_key = f"buzzer{buzzer_id}"
    buzzer = state.get(buzzer_key, {})

    if not buzzer.get("running", False):
        buzzer["running"] = True
        buzzer["last_start_ts"] = int(time.time() * 1000)
    else:
        buzzer["running"] = False
        if buzzer.get("last_start_ts"):
            buzzer["elapsed_ms"] = buzzer.get("elapsed_ms", 0) + int(time.time() * 1000 - buzzer["last_start_ts"])
        buzzer["last_start_ts"] = None

    state[buzzer_key] = buzzer
    save_state(state)

    save_state(state)
    return "", 204

@app.route("/buzzer/<int:buzzer_id>/reset", methods=["POST"])
def buzzer_reset(buzzer_id):
    state = load_state()

    buzzer_key = f"buzzer{buzzer_id}"
    state[buzzer_key] = {
        "running": False,
        "elapsed_ms": 0,
        "last_start_ts": None
    }
    save_state(state)

    save_state(state)
    return "", 204

# -------- API: TV --------
@app.route("/tv/<action>")
def tv_control(action):
    state = load_state()  # read current state

    if action == "on":
        subprocess.run('echo "on 0" | cec-client -s -d 1', shell=True)
        state["tv_on"] = True  # save state
    elif action == "off":
        subprocess.run('echo "standby 0" | cec-client -s -d 1', shell=True)
        state["tv_on"] = False  # save state

    save_state(state)
    return "", 204

# -------- API: HDMI --------
@app.route("/hdmi/<int:port>")
def switch_hdmi(port):
    state = load_state()
    state['hdmi'] = port
    save_state(state)

    if port == 1:
        subprocess.run('echo "tx 10:44:82:10:00" | cec-client -s -d 1', shell=True)
    elif port == 2:
        subprocess.run('echo "tx 10:44:82:20:00" | cec-client -s -d 1', shell=True)

    return jsonify({"status": "ok", "hdmi": port})

@app.route("/hdmi/status")
def hdmi_status():
    state = load_state()
    return jsonify({"hdmi": state.get("hdmi", 1)})
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
        team1=state.get("teams", [{}])[0],
        team2=state.get("teams", [{}])[1]
    )

@app.route("/stopwatch")
def stopwatch_page():
    set_mode("stopwatch")
    return render_template("stopwatch.html")

@app.route("/timer")
def timer_page():
    state = load_state()
    state["mode"] = "timer"
    save_state(state)
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

@app.route("/buzzer")
def buzzer_page():
    set_mode("buzzer")
    return render_template("buzzer.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
