import pygame
import sys
from datetime import datetime

pygame.init()

WIDTH, HEIGHT = 800, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Scoreboard Uhr")

font = pygame.font.SysFont("Arial", 100)
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))

    current_time = datetime.now().strftime("%H:%M:%S")
    text_surface = font.render(current_time, True, (255, 255, 255))
    screen.blit(text_surface, ((WIDTH - text_surface.get_width()) / 2, (HEIGHT - text_surface.get_height()) / 2))

    pygame.display.flip()
    clock.tick(1)

pygame.quit()
sys.exit()
