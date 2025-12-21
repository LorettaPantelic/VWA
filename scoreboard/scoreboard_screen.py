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
WIDTH, HEIGHT = 800, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Scoreboard Uhr")

# --- Schriftarten ---
font = pygame.font.SysFont("Arial", 80)          # Stoppuhr
clock_font = pygame.font.SysFont("Arial", 40)    # Uhrzeit oben links
date_font = pygame.font.SysFont("Arial", 40)     # Datum oben rechts

clock = pygame.time.Clock()

# --- Pfad zur state.json ---
STATE_FILE = "../scoreboard_web/state.json"

# --- Statusfunktionen ---
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def load_state():
    if not os.path.exists(STATE_FILE):
        save_state({"clock_running": False})
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {"clock_running": False}
        save_state(data)
    return data

# --- Zeitvariablen ---
total_elapsed = 0
last_tick = time.time()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Status aus Datei
    state = load_state()
    clock_running = state.get("clock_running", False)

    current_time = time.time()

    if clock_running:
        total_elapsed += current_time - last_tick

    last_tick = current_time

    # Stoppuhr berechnen
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

    # Stoppuhr zentriert
    text_surface = font.render(time_text, True, (255, 255, 255))
    screen.blit(text_surface, ((WIDTH - text_surface.get_width()) / 2,
                               (HEIGHT - text_surface.get_height()) / 2))

    # Uhrzeit oben links
    clock_surface = clock_font.render(now_time, True, (255, 255, 255))
    screen.blit(clock_surface, (10, 10))

    # Datum oben rechts
    date_surface = date_font.render(date_text, True, (255, 255, 255))
    screen.blit(date_surface, (WIDTH - date_surface.get_width() - 10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
