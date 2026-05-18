import pygame

NAME = "PAC-MAN"

def main():
    pygame.init()
    WIDTH, HEIGHT = 600, 300
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"Jogo da/do {NAME}")

    game = True
    BLUE = (0, 0, 255)
    clock = pygame.time.Clock()

    while game:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game = False
            elif event.type == pygame.KEYUP:
                game = False

        window.fill(BLUE)
        pygame.display.update()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()


#teste