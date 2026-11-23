import pygame

from player import Player
from settings import BACKGROUND_COLOR, FPS


class Game:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.bounds = screen.get_rect()
        self.clock = pygame.time.Clock()
        self.player = Player(self.bounds.center)

    def run(self) -> None:
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            self.player.update(pygame.key.get_pressed(), dt, self.bounds)
            self.screen.fill(BACKGROUND_COLOR)
            self.player.draw(self.screen)
            pygame.display.flip()
