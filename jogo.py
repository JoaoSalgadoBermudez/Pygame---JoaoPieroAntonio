import pygame
import sys

pygame.init()

WIDTH  = 560
HEIGHT = 680

BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
YELLOW = (255, 255,   0)
BLUE   = ( 33,  33, 255)

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man")

rodando = True

while rodando:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False
        if event.type == pygame.KEYUP:
            rodando = False

    window.fill(BLACK)

    

    # --- Paredes do labirinto (retângulos azuis) ---
    # draw.rect(superfície, cor, (x, y, largura, altura))

    # Borda externa — quatro paredes ao redor da área de jogo
    pygame.draw.rect(window, BLUE, (  0,   0, WIDTH,  20))   # topo
    pygame.draw.rect(window, BLUE, (  0, 580, WIDTH,  20))   # base
    pygame.draw.rect(window, BLUE, (  0,   0,  20,  600))   # esquerda
    pygame.draw.rect(window, BLUE, (540,   0,  20,  600))   # direita

    # Algumas paredes internas de exemplo (protótipo do labirinto)
    pygame.draw.rect(window, BLUE, ( 60,  60, 120,  20))
    pygame.draw.rect(window, BLUE, (380,  60, 120,  20))
    pygame.draw.rect(window, BLUE, ( 60, 140,  20, 100))
    pygame.draw.rect(window, BLUE, (480, 140,  20, 100))
    pygame.draw.rect(window, BLUE, (160, 140, 240,  20))
    pygame.draw.rect(window, BLUE, (240, 200,  80,  20))
    pygame.draw.rect(window, BLUE, ( 60, 280, 160,  20))
    pygame.draw.rect(window, BLUE, (340, 280, 160,  20))
    pygame.draw.rect(window, BLUE, (240, 260,  80,  80))   # "casa" dos fantasmas
    pygame.draw.rect(window, BLUE, ( 60, 380, 120,  20))
    pygame.draw.rect(window, BLUE, (380, 380, 120,  20))
    pygame.draw.rect(window, BLUE, (160, 460, 240,  20))
    pygame.draw.rect(window, BLUE, ( 60, 500,  20, 100))
    pygame.draw.rect(window, BLUE, (480, 500,  20, 100))

    # --- Pellets normais (círculos brancos pequenos) ---
    # draw.circle(superfície, cor, (centro_x, centro_y), raio)
    # Fileira de pellets no corredor superior
    for col in range(7):
        pygame.draw.circle(window, WHITE, (40 + col * 80, 40), 4)

    # Fileira de pellets no corredor do meio
    for col in range(5):
        pygame.draw.circle(window, WHITE, (80 + col * 100, 320), 4)

    # Fileiras de pellets nos corredores laterais
    for row in range(5):
        pygame.draw.circle(window, WHITE, (40, 100 + row * 80), 4)
        pygame.draw.circle(window, WHITE, (520, 100 + row * 80), 4)

    # --- Power pellets (círculos amarelos grandes) — nos 4 cantos ---
    # São desenhados POR CIMA dos pellets normais (ordem importa!)
    pygame.draw.circle(window, YELLOW, ( 40,  40), 10)   # canto sup-esq
    pygame.draw.circle(window, YELLOW, (520,  40), 10)   # canto sup-dir
    pygame.draw.circle(window, YELLOW, ( 40, 560), 10)   # canto inf-esq
    pygame.draw.circle(window, YELLOW, (520, 560), 10)   # canto inf-dir

    # Linha separando labirinto do HUD
    pygame.draw.rect(window, YELLOW, (0, 600, WIDTH, 4))

    pygame.display.update()

pygame.quit()
sys.exit()
