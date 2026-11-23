import pygame

from game import Game
from settings import WINDOW_SIZE, WINDOW_TITLE


def main() -> None:
    pygame.display.init()
    try:
        screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption(WINDOW_TITLE)
        Game(screen).run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
