import pygame
import sys
import time
import json
import os
import datetime
from zoneinfo import ZoneInfo

GERMAN_WEEKDAYS = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag",
}

pygame.init()

# --- Screensize ---
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Scoreboard Uhr")

# --- Fonts ---
font = pygame.font.SysFont("Arial", 180)
team_font = pygame.font.SysFont("Arial", 160)
score_font = pygame.font.SysFont("Arial", 350)
clock_font_small = pygame.font.SysFont("Arial", 100)
clock_font_large = pygame.font.SysFont("Arial", 300)
date_font_small   = pygame.font.SysFont("Arial", 100)
game_time_font = pygame.font.SysFont("Arial", 140)

clock = pygame.time.Clock()

# --- Path to state.json ---
STATE_FILE = "/home/lori/VWA/scoreboard_web/state.json"

# --- State handling functions ---
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

def wrap_text(text, font, max_width):
    
    #Splits text into multiple lines so that each line
    #fits within max_width. Line breaks occur only at whole words.
    
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        # Test if adding the next word exceeds the max width
        test_line = current_line + (" " if current_line else "") + word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            # Start a new line
            if current_line:
                lines.append(current_line)
            current_line = word

    # Add the last line
    if current_line:
        lines.append(current_line)

    return lines

def get_fitting_font(text, base_font_name, max_width, max_height, max_size, min_size):
   
    #Returns a pygame Font object with the largest possible size
    #that allows 'text' to fit within max_width and max_height.
    
    font_size = max_size

    while font_size >= min_size:
        font = pygame.font.SysFont(base_font_name, font_size)
        # Wrap text based on current font size
        lines = wrap_text(text, font, max_width)
        line_height = font.get_height()
        text_height = line_height * len(lines)
        text_width = max(font.size(line)[0] for line in lines)

        if text_width <= max_width and text_height <= max_height:
            return font, lines  # fits perfectly

        font_size -= 2  # try smaller font

    # If nothing fits, return min size
    font = pygame.font.SysFont(base_font_name, min_size)
    lines = wrap_text(text, font, max_width)
    return font, lines

def format_hms(ms):
    total = ms // 1000
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02}:{m:02}:{s:02}"

# --- Time variables ---
state = load_state()
total_elapsed = state.get("elapsed_ms", 0) / 1000
last_tick = time.time()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Load state from file
    state = load_state()
    mode = state.get("mode", "index")
    message_text = state.get("message", "Nachricht")
    clock_running = state.get("clock_running", False)

    current_time = time.time()

    # --- Calculate stopwatch time ---
    if clock_running and state.get("last_start_ts"):
        # total_elapsed = stored time + time elapsed since last start
        total_elapsed = state.get("elapsed_ms", 0) / 1000 + (current_time - state["last_start_ts"] / 1000)
    elif not clock_running:
        # If stopwatch is stopped or reset, use stored state only
        total_elapsed = state.get("elapsed_ms", 0) / 1000

    hours = int(total_elapsed // 3600)
    minutes = int((total_elapsed % 3600) // 60)
    seconds = int(total_elapsed % 60)
    milliseconds = int((total_elapsed - int(total_elapsed)) * 1000) // 10

    time_text = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:02}"

    # --- Always use white background ---
    screen.fill((255, 255, 255))

    # --- Current time and date ---
    now = datetime.datetime.now(ZoneInfo("Europe/Vienna"))

    weekday = GERMAN_WEEKDAYS[now.weekday()]
    now_time = f"{now.hour:02}:{now.minute:02}:{now.second:02}"
    date_text = f"{weekday}, {now.day:02}.{now.month:02}.{now.year}"

    # Always display date at the top-right
    date_surface = date_font_small.render(date_text, True, (0, 0, 0))
    screen.blit(date_surface, (WIDTH - date_surface.get_width() - 10, 10))

    if mode == "index":
        # Large centered time display
        time_surface = clock_font_large.render(now_time, True, (0, 0, 0))
        screen.blit(
            time_surface,
            ((WIDTH - time_surface.get_width()) // 2,
            (HEIGHT - time_surface.get_height()) // 2)
        )
    else:
        # Small time display at the top-left
        clock_surface = clock_font_small.render(now_time, True, (0, 0, 0))
        screen.blit(clock_surface, (10, 10))

    if mode == "stopwatch":
        # Blue box (same style as message/timer)
        box_width = WIDTH * 0.7
        box_height = HEIGHT * 0.4
        box_x = (WIDTH - box_width) / 2
        box_y = (HEIGHT - box_height) / 2

        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (91, 124, 255), rect, border_radius=40)

        # Stopwatch time (white, centered)
        text_surface = font.render(time_text, True, (255, 255, 255))
        screen.blit(
            text_surface,
            ((WIDTH - text_surface.get_width()) // 2,
            (HEIGHT - text_surface.get_height()) // 2)
        )

    elif mode == "message":
        padding = 40

        # Original box size
        base_box_width = int(WIDTH * 0.7)
        base_box_height = int(HEIGHT * 0.4)
        box_width = base_box_width
        box_height = base_box_height

        # Maximum allowed size (safe area)
        top_margin = 160
        bottom_margin = 60  # distance to bottom screen edge
        max_box_width = int(WIDTH * 0.9)
        max_box_height = HEIGHT - top_margin - bottom_margin

        # Max & Min font sizes
        MAX_FONT_SIZE = 180
        MIN_FONT_SIZE = 50

        # Get optimal font and wrapped lines
        font, lines = get_fitting_font(
            message_text, "Arial",
            max_box_width - 2 * padding,
            max_box_height - 2 * padding,
            MAX_FONT_SIZE,
            MIN_FONT_SIZE
        )

        # Text dimensions
        line_height = font.get_height()
        text_height = line_height * len(lines)
        text_width = max(font.size(line)[0] for line in lines)

        # Adjust box width if text is wider than base
        if text_width + 2 * padding > base_box_width:
            box_width = min(text_width + 2 * padding, max_box_width)

        # Adjust box height **only if text is taller than base**
        if text_height + 2 * padding > base_box_height:
            box_height = min(text_height + 2 * padding, max_box_height)

        # Center box horizontally and vertically like stopwatch
        box_x = (WIDTH - box_width) // 2
        box_y = (HEIGHT - box_height) // 2

        # Draw box
        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (91, 124, 255), rect, border_radius=40)

        # Text vertical positioning
        if text_height + 2 * padding >= box_height:
            y_offset = box_y + padding  # start at top padding if text is too tall
        else:
            y_offset = box_y + (box_height - text_height) // 2  # center vertically

        # Draw text lines
        for line in lines:
            line_surface = font.render(line, True, (255, 255, 255))
            x = box_x + (box_width - line_surface.get_width()) // 2
            screen.blit(line_surface, (x, y_offset))
            y_offset += line_height
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

            # Team card
            rect = pygame.Rect(x, y, card_width, card_height)
            pygame.draw.rect(screen, color, rect, border_radius=40)

            # Team name
            name_surf = team_font.render(name, True, (255, 255, 255))
            screen.blit(
                name_surf,
                (x + (card_width - name_surf.get_width()) // 2, y + 40)
            )

            # Score
            score_surf = score_font.render(score, True, (255, 255, 255))
            screen.blit(
                score_surf,
                (x + (card_width - score_surf.get_width()) // 2,
                y + (card_height - score_surf.get_height()) // 2)
            )
        elapsed = state.get("game_elapsed_ms", 0)

        if state.get("game_clock_running") and state.get("game_last_start_ts"):
            elapsed += int(time.time() * 1000 - state["game_last_start_ts"])

        time_text = format_hms(elapsed)

        time_surf = game_time_font.render(time_text, True, (255, 255, 255))
        screen.blit(
            time_surf,
            ((WIDTH - time_surf.get_width()) // 2, HEIGHT - 80)
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

        # Blue Box
        box_width = WIDTH * 0.7
        box_height = HEIGHT * 0.4
        box_x = (WIDTH - box_width) / 2
        box_y = (HEIGHT - box_height) / 2

        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (91, 124, 255), rect, border_radius=40)

        # Time (white)
        timer_surface = font.render(time_text, True, (255, 255, 255))
        screen.blit(
            timer_surface,
            ((WIDTH - timer_surface.get_width()) // 2,
            (HEIGHT - timer_surface.get_height()) // 2)
        )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
