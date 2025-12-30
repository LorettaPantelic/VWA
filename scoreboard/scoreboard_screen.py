import pygame
import sys
import time
import json
import os
import datetime
import locale

# --- Deutsche Datums- und Zeitformate aktivieren ---
locale.setlocale(locale.LC_TIME, "")

pygame.init()

# --- Bildschirmgröße ---
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Scoreboard Uhr")

# --- Schriftarten ---
font = pygame.font.SysFont("Arial", 80)
clock_font = pygame.font.SysFont("Arial", 40)
date_font = pygame.font.SysFont("Arial", 40)
team_font = pygame.font.SysFont("Arial", 64)
score_font = pygame.font.SysFont("Arial", 180)
timer_font = pygame.font.SysFont("Arial", 160)
clock = pygame.time.Clock()

# --- Pfad zur state.json ---
STATE_FILE = "/home/lori/VWA/scoreboard_web/state.json"

# --- Statusfunktionen ---
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)
        f.flush()
        os.fsync(f.fileno())

def load_state():
    if not os.path.exists(STATE_FILE):
        save_state({
            "clock_running": False,
            "elapsed_ms": 0,
            "mode": "index",
            "message": "Nachricht",
            "teams": [
                {"name": "Team 1", "score": 0, "color": [91, 124, 255]},
                {"name": "Team 2", "score": 0, "color": [214, 76, 76]}
            ],
            "last_start_ts": None
        })
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {
            "clock_running": False,
            "elapsed_ms": 0,
            "mode": "index",
            "message": "Nachricht",
            "teams": [
                {"name": "Team 1", "score": 0, "color": [91, 124, 255]},
                {"name": "Team 2", "score": 0, "color": [214, 76, 76]}
            ],
            "last_start_ts": None
        }
        save_state(data)
    return data


# --- Zeitvariablen ---
state = load_state()
total_elapsed = state.get("elapsed_ms", 0) / 1000  # ms → Sekunden
last_tick = time.time()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Status aus Datei
    state = load_state()
    mode = state.get("mode", "index")
    message_text = state.get("message", "Nachricht")
    clock_running = state.get("clock_running", False)

    current_time = time.time()

    # --- Stoppuhr berechnen ---
    if clock_running and state.get("last_start_ts"):
        # total_elapsed = gespeicherte Zeit + seit Start vergangene Zeit
        total_elapsed = state.get("elapsed_ms", 0) / 1000 + (current_time - state["last_start_ts"] / 1000)
    elif not clock_running:
        # Wenn Uhr gestoppt oder reset, total_elapsed nur aus saved state
        total_elapsed = state.get("elapsed_ms", 0) / 1000

    hours = int(total_elapsed // 3600)
    minutes = int((total_elapsed % 3600) // 60)
    seconds = int(total_elapsed % 60)
    milliseconds = int((total_elapsed - int(total_elapsed)) * 1000) // 10

    time_text = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:02}"

    # --- Hintergrund immer weiß ---
    screen.fill((255, 255, 255))

    # --- Aktuelle Zeit und Datum ---
    now = datetime.datetime.now()
    now_time = now.strftime("%H:%M:%S")
    date_text = now.strftime("%A, %d.%m.%Y")  # Dienstag, 30.12.2025

    # --- Datum immer oben rechts ---
    date_surface = date_font.render(date_text, True, (0, 0, 0))
    screen.blit(date_surface, (WIDTH - date_surface.get_width() - 10, 10))

    if mode == "index":
        # Uhrzeit groß, zentriert
        time_surface = font.render(now_time, True, (0, 0, 0))
        screen.blit(
            time_surface,
            ((WIDTH - time_surface.get_width()) // 2,
            (HEIGHT - time_surface.get_height()) // 2)
        )
    else:
        # Uhrzeit oben links
        clock_surface = clock_font.render(now_time, True, (0, 0, 0))
        screen.blit(clock_surface, (10, 10))

    if mode == "stopwatch":
        # Blaue Box (gleich wie Message/Timer)
        box_width = WIDTH * 0.7
        box_height = HEIGHT * 0.4
        box_x = (WIDTH - box_width) / 2
        box_y = (HEIGHT - box_height) / 2

        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (91, 124, 255), rect, border_radius=40)

        # Stopwatch-Zeit (weiß, zentriert)
        text_surface = font.render(time_text, True, (255, 255, 255))
        screen.blit(
            text_surface,
            ((WIDTH - text_surface.get_width()) // 2,
            (HEIGHT - text_surface.get_height()) // 2)
        )

    elif mode == "message":
        # Blaue Box (gleiche Proportionen wie beim Timer)
        box_width = WIDTH * 0.7
        box_height = HEIGHT * 0.4
        box_x = (WIDTH - box_width) / 2
        box_y = (HEIGHT - box_height) / 2

        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (91, 124, 255), rect, border_radius=40)

        # Nachricht (weiß, zentriert)
        msg_surface = font.render(message_text, True, (255, 255, 255))
        screen.blit(
            msg_surface,
            ((WIDTH - msg_surface.get_width()) // 2,
            (HEIGHT - msg_surface.get_height()) // 2)
    )
    elif mode == "scores_and_teams":
        teams = state.get("teams", [])

        card_width = WIDTH // 2 - 80
        card_height = HEIGHT - 200
        y = 120

        for i, team in enumerate(teams[:2]):
            x = 60 + i * (card_width + 40)

            color = team.get("color", [80, 80, 80])
            name = team.get("name", "Team")
            score = str(team.get("score", 0))

            # Karte
            rect = pygame.Rect(x, y, card_width, card_height)
            pygame.draw.rect(screen, color, rect, border_radius=40)

            # Teamname
            name_surf = team_font.render(name, True, (255, 255, 255))
            screen.blit(
                name_surf,
                (x + (card_width - name_surf.get_width()) // 2, y + 40)
            )

            # Punktestand
            score_surf = score_font.render(score, True, (255, 255, 255))
            screen.blit(
                score_surf,
                (x + (card_width - score_surf.get_width()) // 2,
                y + (card_height - score_surf.get_height()) // 2)
            )
    elif mode == "timer":
        timer_duration = state.get("timer_duration", 0)
        timer_start_ts = state.get("timer_start_ts", 0)
        timer_running = state.get("timer_running", False)

        remaining = float(timer_duration)

        if timer_running and timer_start_ts > 0:
            elapsed = time.time() - timer_start_ts
            remaining = max(0.0, timer_duration - elapsed)

        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        centiseconds = int((remaining - int(remaining)) * 100)

        time_text = f"{minutes:02}:{seconds:02}.{centiseconds:02}"

        # Blaue Box
        box_width = WIDTH * 0.7
        box_height = HEIGHT * 0.4
        box_x = (WIDTH - box_width) / 2
        box_y = (HEIGHT - box_height) / 2

        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (91, 124, 255), rect, border_radius=40)

        # Zeit (weiß)
        timer_surface = timer_font.render(time_text, True, (255, 255, 255))
        screen.blit(
            timer_surface,
            ((WIDTH - timer_surface.get_width()) // 2,
            (HEIGHT - timer_surface.get_height()) // 2)
        )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
