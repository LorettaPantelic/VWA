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
font = pygame.font.SysFont("Arial", 80)          # Stoppuhr
clock_font = pygame.font.SysFont("Arial", 40)    # Uhrzeit oben links
date_font = pygame.font.SysFont("Arial", 40)     # Datum oben rechts
team_font = pygame.font.SysFont("Arial", 64)
score_font = pygame.font.SysFont("Arial", 180)

clock = pygame.time.Clock()

# --- Pfad zur state.json ---
STATE_FILE = "../scoreboard_web/state.json"

# --- Statusfunktionen ---
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def load_state():
    if not os.path.exists(STATE_FILE):
        save_state({"clock_running": False, "elapsed_ms": 0})
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {"clock_running": False, "elapsed_ms": 0}
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

    # Uhrzeit oben links
    now = datetime.datetime.now()
    now_time = now.strftime("%H:%M:%S")

    # Datum oben rechts – deutscher Stil
    date_text = now.strftime("%A, %d.%m.%Y")

    # --- Anzeige ---
    screen.fill((0, 0, 0))

    if mode == "index":
        time_surface = font.render(now_time, True, (255, 255, 255))
        screen.blit(time_surface, ((WIDTH - time_surface.get_width()) / 2,
                                (HEIGHT - time_surface.get_height()) / 2))
    elif mode == "stopwatch":
        text_surface = font.render(time_text, True, (255, 255, 255))
        screen.blit(text_surface, ((WIDTH - text_surface.get_width()) / 2,
                                (HEIGHT - text_surface.get_height()) / 2))

        clock_surface = clock_font.render(now_time, True, (255, 255, 255))
        screen.blit(clock_surface, (10, 10))

        date_surface = date_font.render(date_text, True, (255, 255, 255))
        screen.blit(date_surface, (WIDTH - date_surface.get_width() - 10, 10))
    elif mode == "message":
        msg_surface = font.render(message_text, True, (255, 255, 255))
        screen.blit(msg_surface, ((WIDTH - msg_surface.get_width()) / 2,
                                (HEIGHT - msg_surface.get_height()) / 2))
    elif mode == "scoreboard":
        teams = state.get("teams", [])

        screen.fill((20, 25, 40))  # dunkler Hintergrund wie Foto

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

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
