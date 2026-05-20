import pygame
import sys

pygame.init()  # inicia todos os módulos do pygame

# Tamanho da janela — 28 colunas × 20px de tile = 560px; 80px extras para o HUD
WIDTH  = 560
HEIGHT = 680

# Cores em RGB (vermelho, verde, azul) — cada canal de 0 a 255
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
YELLOW = (255, 255,   0)
BLUE   = ( 33,  33, 255)

window = pygame.display.set_mode((WIDTH, HEIGHT))  # cria a janela
pygame.display.set_caption("Pac-Man")              # título da barra da janela

# Fonte para o HUD — None usa a fonte padrão do sistema; 28 é o tamanho
font_hud   = pygame.font.SysFont(None, 28)
# Fonte maior para textos de destaque (GAME OVER, título)
font_title = pygame.font.SysFont(None, 64)

# Variáveis de estado do jogo
score  = 0    # pontuação atual
vidas  = 3    # número de vidas do jogador

rodando = True  # controla o game loop — False encerra o jogo

# Game loop: cada iteração gera um frame
while rodando:

    # 1. Tratar eventos
    # pygame.event.get() devolve todos os eventos desde o último frame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:   # usuário clicou no X da janela
            rodando = False
        if event.type == pygame.KEYUP:  # usuário soltou qualquer tecla (Exercício 1)
            rodando = False

    # 2. Verificar consequências  (lógica de jogo — virá nas próximas etapas)

    # 3. Atualizar estado do jogo (movimento, colisões — virá nas próximas etapas)

    # 4. Gerar saídas — desenhar o frame

    window.fill(BLACK)  # apaga o frame anterior; sem isso os objetos deixariam rastro

    # --- Paredes do labirinto (retângulos azuis) ---
    # draw.rect(superfície, cor, (x, y, largura, altura))

    # Borda externa
    pygame.draw.rect(window, BLUE, (  0,   0, WIDTH,  20))  # topo
    pygame.draw.rect(window, BLUE, (  0, 580, WIDTH,  20))  # base
    pygame.draw.rect(window, BLUE, (  0,   0,  20,  600))  # esquerda
    pygame.draw.rect(window, BLUE, (540,   0,  20,  600))  # direita

    # Paredes internas de exemplo
    pygame.draw.rect(window, BLUE, ( 60,  60, 120,  20))
    pygame.draw.rect(window, BLUE, (380,  60, 120,  20))
    pygame.draw.rect(window, BLUE, ( 60, 140,  20, 100))
    pygame.draw.rect(window, BLUE, (480, 140,  20, 100))
    pygame.draw.rect(window, BLUE, (160, 140, 240,  20))
    pygame.draw.rect(window, BLUE, (240, 200,  80,  20))
    pygame.draw.rect(window, BLUE, ( 60, 280, 160,  20))
    pygame.draw.rect(window, BLUE, (340, 280, 160,  20))
    pygame.draw.rect(window, BLUE, (240, 260,  80,  80))  # "casa" dos fantasmas
    pygame.draw.rect(window, BLUE, ( 60, 380, 120,  20))
    pygame.draw.rect(window, BLUE, (380, 380, 120,  20))
    pygame.draw.rect(window, BLUE, (160, 460, 240,  20))
    pygame.draw.rect(window, BLUE, ( 60, 500,  20, 100))
    pygame.draw.rect(window, BLUE, (480, 500,  20, 100))

    # --- Pellets normais (círculos brancos pequenos) ---
    # draw.circle(superfície, cor, (centro_x, centro_y), raio)
    for col in range(7):
        pygame.draw.circle(window, WHITE, (40 + col * 80, 40), 4)
    for col in range(5):
        pygame.draw.circle(window, WHITE, (80 + col * 100, 320), 4)
    for row in range(5):
        pygame.draw.circle(window, WHITE, ( 40, 100 + row * 80), 4)
        pygame.draw.circle(window, WHITE, (520, 100 + row * 80), 4)

    # --- Power pellets (amarelos, maiores) — desenhados por cima dos normais ---
    pygame.draw.circle(window, YELLOW, ( 40,  40), 10)
    pygame.draw.circle(window, YELLOW, (520,  40), 10)
    pygame.draw.circle(window, YELLOW, ( 40, 560), 10)
    pygame.draw.circle(window, YELLOW, (520, 560), 10)

    # Linha separando labirinto do HUD
    pygame.draw.rect(window, YELLOW, (0, 600, WIDTH, 4))

    # --- HUD: score e vidas (Exercício 3 — texto em posições diferentes) ---
    # font.render(texto, antialias, cor) cria uma imagem com o texto
    # blit(imagem, (x, y)) desenha essa imagem na posição (x, y) — canto superior esquerdo

    texto_score = font_hud.render(f"SCORE: {score}", True, WHITE)
    window.blit(texto_score, (10, 618))  # canto inferior esquerdo do HUD

    texto_vidas = font_hud.render(f"VIDAS: {vidas}", True, YELLOW)
    window.blit(texto_vidas, (420, 618))  # canto inferior direito do HUD

    # Título centralizado no meio da área do labirinto (texto em posição diferente)
    texto_titulo = font_title.render("PAC-MAN", True, YELLOW)
    # get_rect(center=...) calcula o rect centrado em (x, y)
    rect_titulo = texto_titulo.get_rect(center=(WIDTH // 2, 300))
    window.blit(texto_titulo, rect_titulo)

    pygame.display.update()  # envia o frame desenhado para a tela

# Finalização
pygame.quit()  # fecha todos os recursos do pygame
sys.exit()     # encerra o processo Python
