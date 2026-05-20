import pygame
import sys
import math

pygame.init()

TILE_SIZE     = 20    # cada tile do labirinto em pixels
COLS          = 28    # colunas do labirinto
ROWS          = 31    # linhas do labirinto
MAZE_OFFSET_Y = 40    # espaço de HUD acima do labirinto
SPEED         = 2     # pixels movidos por frame

WIDTH  = COLS * TILE_SIZE                          # 560
HEIGHT = ROWS * TILE_SIZE + MAZE_OFFSET_Y + 20    # 680 (620 labirinto + 40 HUD topo + 20 HUD base)

# Cores em RGB
BLACK  = (  0,   0,   0)
WHITE  = (255, 255, 255)
YELLOW = (255, 255,   0)
BLUE   = ( 33,  33, 255)
RED    = (255,   0,   0)
PINK   = (255, 184, 255)
CYAN   = (  0, 255, 255)
ORANGE = (255, 184,  82)

# Mapa do labirinto original do Pac-Man (28 colunas × 31 linhas)
# '#'=parede  '.'=pellet  'o'=power pellet  ' '=vazio  '-'=porta fantasma
MAZE_STR = [
    "############################",  # 0
    "#............##............#",  # 1
    "#.####.#####.##.#####.####.#",  # 2
    "#o####.#####.##.#####.####o#",  # 3
    "#.####.#####.##.#####.####.#",  # 4
    "#..........................#",  # 5
    "#.####.##.########.##.####.#",  # 6
    "#.####.##.########.##.####.#",  # 7
    "#......##....##....##......#",  # 8
    "######.#####.##.#####.######",  # 9
    "     #.#####    #####.#     ",  # 10
    "     #.##          ##.#     ",  # 11
    "     #.## ###--### ##.#     ",  # 12
    "######.## #      # ##.######",  # 13
    "          #      #          ",  # 14  corredor de teleporte (esq ↔ dir)
    "######.## #      # ##.######",  # 15
    "     #.## ######## ##.#     ",  # 16
    "     #.##          ##.#     ",  # 17
    "     #.## ######## ##.#     ",  # 18
    "######.## ######## ##.######",  # 19
    "#............##............#",  # 20
    "#.####.#####.##.#####.####.#",  # 21
    "#o##...#####.##.#####...##o#",  # 22
    "###.##.##....  ....##.##.###",  # 23
    "#......##.########.##......#",  # 24
    "#.##########.##.##########.#",  # 25
    "#..........................#",  # 26
    "#.####.#####.##.#####.####.#",  # 27
    "#.####.#####.##.#####.####.#",  # 28
    "#............##............#",  # 29
    "############################",  # 30
]

window = pygame.display.set_mode((WIDTH, HEIGHT))  # cria a janela
pygame.display.set_caption("Pac-Man")              # título da barra da janela

font_hud   = pygame.font.SysFont(None, 28)  # fonte para score e vidas
font_title = pygame.font.SysFont(None, 64)  # fonte para GAME OVER, tela inicial, etc.

score = 0
vidas = 3

# --- Sprites desenhados programaticamente ---
# pygame.image.load() também retorna um Surface — a interface é idêntica.
# pygame.SRCALPHA cria Surface com canal alpha (transparência), como .convert_alpha()

def criar_sprite_pacman():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    cx = cy = TILE_SIZE // 2
    r  = TILE_SIZE // 2 - 1
    pygame.draw.circle(surf, YELLOW, (cx, cy), r)  # corpo amarelo
    # boca aberta 30° — sprite base virado para a direita
    top    = (cx + r * math.cos(math.radians(-30)), cy + r * math.sin(math.radians(-30)))
    bottom = (cx + r * math.cos(math.radians( 30)), cy + r * math.sin(math.radians( 30)))
    pygame.draw.polygon(surf, BLACK, [(cx, cy), top, bottom])
    return surf

def criar_sprite_fantasma(cor):
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    cx   = TILE_SIZE // 2
    r    = TILE_SIZE // 2
    pygame.draw.circle(surf, cor, (cx, r), r)              # cabeça semicircular
    pygame.draw.rect  (surf, cor, (0, r, TILE_SIZE, r))    # corpo retangular
    for i in range(3):                                      # ondas na base
        pygame.draw.circle(surf, BLACK, (3 + i * 7, TILE_SIZE), 3)
    pygame.draw.circle(surf, WHITE, (cx - 4, r - 2), 3)   # olho esquerdo
    pygame.draw.circle(surf, WHITE, (cx + 4, r - 2), 3)   # olho direito
    pygame.draw.circle(surf, BLUE,  (cx - 3, r - 2), 1)   # pupila esquerda
    pygame.draw.circle(surf, BLUE,  (cx + 3, r - 2), 1)   # pupila direita
    return surf

# Cria os sprites — equivalente a pygame.image.load('arquivo.png').convert_alpha()
_base_pacman = criar_sprite_pacman()

# Quatro rotações do Pac-Man, uma por direção de movimento
# pygame.transform.rotate() gira no sentido anti-horário
pacman_sprites = {
    ( 1,  0): _base_pacman,                                       # direita (base, 0°)
    (-1,  0): pygame.transform.rotate(_base_pacman, 180),         # esquerda
    ( 0, -1): pygame.transform.rotate(_base_pacman,  90),         # cima
    ( 0,  1): pygame.transform.rotate(_base_pacman, 270),         # baixo
}

blinky_img = criar_sprite_fantasma(RED)     # Blinky — vermelho
pinky_img  = criar_sprite_fantasma(PINK)    # Pinky  — rosa
inky_img   = criar_sprite_fantasma(CYAN)    # Inky   — ciano
clyde_img  = criar_sprite_fantasma(ORANGE)  # Clyde  — laranja

# pygame.transform.scale() seria usado aqui para redimensionar imagens externas (Exercício 4)
# ex: pacman_img = pygame.transform.scale(pacman_img, (TILE_SIZE, TILE_SIZE))

# --- Funções de colisão com o labirinto ---

def tile_at(px, py):
    # Converte coordenada de pixel para tile e retorna o caractere no MAZE_STR
    col = int(px) // TILE_SIZE
    row = (int(py) - MAZE_OFFSET_Y) // TILE_SIZE
    if 0 <= row < ROWS and 0 <= col < COLS:
        return MAZE_STR[row][col]
    return ' '  # fora dos limites do mapa = espaço vazio

def can_move(x, y, dx, dy):
    # Verifica as duas extremidades da borda frontal do hitbox de Pac-Man.
    # shrink=2: margem interna para que Pac-Man passe por corredores sem travar nas bordas
    shrink = 2
    nx, ny = x + dx * SPEED, y + dy * SPEED
    if dx != 0:
        borda_x = nx + TILE_SIZE - 1 if dx > 0 else nx
        return tile_at(borda_x, ny + shrink) != '#' and \
               tile_at(borda_x, ny + TILE_SIZE - 1 - shrink) != '#'
    else:
        borda_y = ny + TILE_SIZE - 1 if dy > 0 else ny
        return tile_at(nx + shrink, borda_y) != '#' and \
               tile_at(nx + TILE_SIZE - 1 - shrink, borda_y) != '#'

# Posição inicial do Pac-Man — coluna 13, linha 23 do labirinto
pacman_x  = 13 * TILE_SIZE
pacman_y  = MAZE_OFFSET_Y + 23 * TILE_SIZE
pacman_dx = 1   # começa se movendo para a direita (Exercício 5 — movimento automático)
pacman_dy = 0

# Posições iniciais dos fantasmas (coluna, linha, sprite)
ghost_positions = [
    (13, 11, blinky_img),  # Blinky — acima da porta da casa
    (13, 14, pinky_img),   # Pinky  — centro da casa
    (11, 14, inky_img),    # Inky   — esquerda da casa
    (15, 14, clyde_img),   # Clyde  — direita da casa
]

rodando = True  # controla o game loop — False encerra o jogo

# Game loop: cada iteração gera um frame
while rodando:

    # 1. Tratar eventos
    # pygame.event.get() devolve todos os eventos desde o último frame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:                              # usuário clicou no X da janela
            rodando = False
        if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:  # ESC encerra
            rodando = False

    # 2. Verificar consequências

    # Move Pac-Man se o próximo passo não colidir com parede
    if can_move(pacman_x, pacman_y, pacman_dx, pacman_dy):
        pacman_x += pacman_dx * SPEED
        pacman_y += pacman_dy * SPEED

    # Teleporte pelo corredor da linha 14 — sai pela esquerda, aparece pela direita (e vice-versa)
    pacman_row = (pacman_y - MAZE_OFFSET_Y) // TILE_SIZE
    if pacman_row == 14:
        if pacman_x + TILE_SIZE <= 0:   # saiu pela esquerda
            pacman_x = WIDTH
        elif pacman_x >= WIDTH:          # saiu pela direita
            pacman_x = 0

    # 3. Atualizar estado do jogo (sprites, animações — virá nas próximas etapas)

    # 4. Gerar saídas — desenhar o frame

    window.fill(BLACK)  # apaga o frame anterior; sem isso os objetos deixariam rastro

    # --- Labirinto ---
    # Percorre o MAZE_STR tile por tile e desenha cada elemento na posição correta
    for row, linha in enumerate(MAZE_STR):
        for col, tile in enumerate(linha):
            x  = col * TILE_SIZE
            y  = MAZE_OFFSET_Y + row * TILE_SIZE
            cx = x + TILE_SIZE // 2
            cy = y + TILE_SIZE // 2

            if tile == '#':
                pygame.draw.rect(window, BLUE, (x, y, TILE_SIZE, TILE_SIZE))       # parede
            elif tile == '.':
                pygame.draw.circle(window, WHITE, (cx, cy), 2)                     # pellet normal
            elif tile == 'o':
                pygame.draw.circle(window, YELLOW, (cx, cy), 5)                    # power pellet
            elif tile == '-':
                pygame.draw.rect(window, PINK, (x, cy - 1, TILE_SIZE, 2))          # porta dos fantasmas

    # --- Pac-Man ---
    # Seleciona o sprite rotacionado de acordo com a direção atual de movimento
    # blit(imagem, (x, y)) — mesmo método de imagens carregadas com image.load()
    window.blit(pacman_sprites[(pacman_dx, pacman_dy)], (pacman_x, pacman_y))

    # --- Fantasmas ---
    for col, row, img in ghost_positions:
        window.blit(img, (col * TILE_SIZE, MAZE_OFFSET_Y + row * TILE_SIZE))

    # --- HUD: score e vidas ---
    # font.render(texto, antialias, cor) cria uma Surface com o texto desenhado
    # blit desenha essa Surface na janela na posição (x, y) — canto superior esquerdo
    texto_score = font_hud.render(f"SCORE: {score}", True, WHITE)
    window.blit(texto_score, (10, 12))

    texto_vidas = font_hud.render(f"VIDAS: {vidas}", True, YELLOW)
    window.blit(texto_vidas, (420, 12))

    pygame.display.update()  # envia o frame desenhado para a tela

# Finalização
pygame.quit()  # fecha todos os recursos do pygame
sys.exit()     # encerra o processo Python
