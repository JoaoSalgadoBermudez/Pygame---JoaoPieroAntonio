import pygame
import sys
import math
import array  # gerar buffers de áudio sem dependências externas

pygame.init()
pygame.mixer.init(44100, -16, 1, 512)  # 44100 Hz, 16-bit signed, mono, buffer 512

TILE_SIZE     = 20    # cada tile do labirinto em pixels
COLS          = 28    # colunas do labirinto
ROWS          = 31    # linhas do labirinto
MAZE_OFFSET_Y = 40    # espaço de HUD acima do labirinto
SPEED         = 2     # pixels movidos por frame
FPS           = 60    # frames por segundo — limita a velocidade do loop em qualquer máquina

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
# list(row) torna cada linha mutável — necessário para apagar pellets comidos
maze = [list(row) for row in [
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
]]

window = pygame.display.set_mode((WIDTH, HEIGHT))  # cria a janela
pygame.display.set_caption("Pac-Man")              # título da barra da janela

font_hud   = pygame.font.SysFont(None, 28)  # fonte para score e vidas
font_title = pygame.font.SysFont(None, 64)  # fonte para GAME OVER, tela inicial, etc.

score = 0
vidas = 3

# --- Funções auxiliares de sprite ---
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

# --- Funções de colisão com o labirinto ---

def tile_at(px, py):
    # Converte coordenada de pixel para tile e retorna o caractere no MAZE_STR
    col = int(px) // TILE_SIZE
    row = (int(py) - MAZE_OFFSET_Y) // TILE_SIZE
    if 0 <= row < ROWS and 0 <= col < COLS:
        return maze[row][col]
    return ' '  # fora dos limites do mapa = espaço vazio

def can_move(x, y, dx, dy):
    # Verifica as duas extremidades da borda frontal do hitbox.
    # shrink=2: margem interna para passar por corredores sem travar nas bordas
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

# --- Sons ---
# pygame.mixer.Sound(buffer=) aceita um array de amostras no mesmo formato do mixer.
# Equivalente a pygame.mixer.Sound('arquivo.wav') — só a fonte dos dados muda.

def gerar_tom(freq, duracao_ms, volume=0.4):
    taxa = 44100
    n    = int(taxa * duracao_ms / 1000)
    buf  = array.array('h', [0] * n)
    for i in range(n):
        fade     = min(1.0, (n - i) / (taxa * 0.02 + 1))  # fade out nos últimos ~20ms
        buf[i]   = int(volume * 32767 * fade * math.sin(2 * math.pi * freq * i / taxa))
    return pygame.mixer.Sound(buffer=buf)

# Exercícios 13 e 14 — sons organizados em dicionário (assets)
sons = {
    'pellet': gerar_tom(880, 60),    # waka curto e agudo
    'power':  gerar_tom(440, 300),   # power pellet — mais grave e longo
    'morte':  gerar_tom(200, 700),   # morte — grave e lento
}


class Pacman(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # inicializa o Sprite base — obrigatório

        # Pré-computa as 4 rotações do sprite; pygame.transform.rotate gira no sentido anti-horário
        base = criar_sprite_pacman()
        self.sprites_dir = {
            ( 1,  0): base,
            (-1,  0): pygame.transform.rotate(base, 180),
            ( 0, -1): pygame.transform.rotate(base,  90),
            ( 0,  1): pygame.transform.rotate(base, 270),
        }

        self.dx      = 1   # direção atual de movimento
        self.dy      = 0
        self.next_dx = 1   # próxima direção solicitada pelo jogador (buffered input)
        self.next_dy = 0

        self.image = self.sprites_dir[(self.dx, self.dy)]  # imagem inicial
        self.rect  = self.image.get_rect()                 # rect define posição e hitbox
        self.rect.x = 13 * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + 23 * TILE_SIZE

    def update(self):
        # Tenta virar para a direção solicitada — só muda se não houver parede nessa direção
        if can_move(self.rect.x, self.rect.y, self.next_dx, self.next_dy):
            self.dx, self.dy = self.next_dx, self.next_dy

        # Move na direção atual se não houver parede na frente
        if can_move(self.rect.x, self.rect.y, self.dx, self.dy):
            self.rect.x += self.dx * SPEED
            self.rect.y += self.dy * SPEED

        # Teleporte pelo corredor da linha 14 — rect.right e rect.left são atributos do Rect
        if (self.rect.y - MAZE_OFFSET_Y) // TILE_SIZE == 14:
            if self.rect.right <= 0:    # saiu pela esquerda
                self.rect.x = WIDTH
            elif self.rect.left >= WIDTH:  # saiu pela direita
                self.rect.x = 0

        # Atualiza a imagem de acordo com a direção atual
        self.image = self.sprites_dir[(self.dx, self.dy)]

    def reset(self):
        self.rect.x            = 13 * TILE_SIZE
        self.rect.y            = MAZE_OFFSET_Y + 23 * TILE_SIZE
        self.dx,      self.dy      = 1, 0
        self.next_dx, self.next_dy = 1, 0


class Ghost(pygame.sprite.Sprite):
    def __init__(self, col, row, cor):
        pygame.sprite.Sprite.__init__(self)  # inicializa o Sprite base — obrigatório

        self.image = criar_sprite_fantasma(cor)  # Surface com o desenho do fantasma
        self.rect  = self.image.get_rect()
        self.rect.x = col * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + row * TILE_SIZE

    def update(self):
        pass  # movimento dos fantasmas virá nas próximas etapas


player = Pacman()

blinky = Ghost(13, 11, RED)    # Blinky — vermelho, acima da porta
pinky  = Ghost(13, 14, PINK)   # Pinky  — rosa, centro da casa
inky   = Ghost(11, 14, CYAN)   # Inky   — ciano, esquerda da casa
clyde  = Ghost(15, 14, ORANGE) # Clyde  — laranja, direita da casa

# Groups (Etapa 8) — pygame.sprite.Group agrupa sprites para atualizar e desenhar de uma vez
all_sprites = pygame.sprite.Group()   # todos os sprites do jogo
ghosts      = pygame.sprite.Group()   # só os fantasmas — útil para colisões depois

all_sprites.add(player)
all_sprites.add(blinky, pinky, inky, clyde)  # add() aceita múltiplos sprites de uma vez
ghosts.add     (blinky, pinky, inky, clyde)  # cada fantasma entra em dois grupos

clock = pygame.time.Clock()  # relógio para controlar a velocidade do loop

rodando = True  # controla o game loop — False encerra o jogo

# Game loop: cada iteração gera um frame
while rodando:

    # clock.tick(FPS) pausa o loop pelo tempo necessário para não ultrapassar FPS frames/s.
    # Sem isso, a velocidade do jogo variaria conforme o hardware. (Exercício 6)
    clock.tick(FPS)

    # 1. Tratar eventos
    # pygame.event.get() devolve todos os eventos desde o último frame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:                                    # usuário clicou no X da janela
            rodando = False
        if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:  # ESC encerra
            rodando = False
        if event.type == pygame.KEYDOWN:  # KEYDOWN: disparado uma vez quando a tecla é pressionada
            if event.key == pygame.K_RIGHT:
                player.next_dx, player.next_dy =  1,  0
            elif event.key == pygame.K_LEFT:
                player.next_dx, player.next_dy = -1,  0
            elif event.key == pygame.K_UP:
                player.next_dx, player.next_dy =  0, -1
            elif event.key == pygame.K_DOWN:
                player.next_dx, player.next_dy =  0,  1

    # 2. Verificar consequências

    # Comer pellets — verifica o tile no centro de Pac-Man
    col_pm = player.rect.centerx // TILE_SIZE
    row_pm = (player.rect.centery - MAZE_OFFSET_Y) // TILE_SIZE
    if 0 <= row_pm < ROWS and 0 <= col_pm < COLS:
        t = maze[row_pm][col_pm]
        if t == '.':
            maze[row_pm][col_pm] = ' '   # remove o pellet do mapa
            score += 10
            sons['pellet'].play()         # Exercício 13 — som ao comer pellet
        elif t == 'o':
            maze[row_pm][col_pm] = ' '   # remove o power pellet do mapa
            score += 50
            sons['power'].play()          # Exercício 13 — som ao comer power pellet

    # Colisão com fantasmas — spritecollide retorna lista de fantasmas que tocaram Pac-Man
    # (Exercício 11 — spritecollide entre um sprite e um grupo)
    if pygame.sprite.spritecollide(player, ghosts, False):
        sons['morte'].play()          # Exercício 13 — som de morte
        vidas -= 1
        player.reset()                # volta para a posição inicial
        if vidas <= 0:
            rodando = False           # game over — tela própria vem na Etapa 16

    # 3. Atualizar estado do jogo — chama update() de todos os sprites do grupo de uma vez
    all_sprites.update()

    # 4. Gerar saídas — desenhar o frame

    window.fill(BLACK)  # apaga o frame anterior; sem isso os objetos deixariam rastro

    # --- Labirinto ---
    # Percorre o MAZE_STR tile por tile e desenha cada elemento na posição correta
    for row, linha in enumerate(maze):
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

    # --- Sprites ---
    # draw() percorre o grupo e chama blit(sprite.image, sprite.rect) em cada um
    all_sprites.draw(window)

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
import pygame
import sys
import math
import array  # gerar buffers de áudio sem dependências externas

pygame.init()
pygame.mixer.init(44100, -16, 1, 512)  # 44100 Hz, 16-bit signed, mono, buffer 512

TILE_SIZE     = 20    # cada tile do labirinto em pixels
COLS          = 28    # colunas do labirinto
ROWS          = 31    # linhas do labirinto
MAZE_OFFSET_Y = 40    # espaço de HUD acima do labirinto
SPEED         = 2     # pixels movidos por frame
FPS           = 60    # frames por segundo — limita a velocidade do loop em qualquer máquina

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
# list(row) torna cada linha mutável — necessário para apagar pellets comidos
maze = [list(row) for row in [
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
    "          #      #          ",  # 14  corredor de teleporte (esq ↔️ dir)
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
]]

window = pygame.display.set_mode((WIDTH, HEIGHT))  # cria a janela
pygame.display.set_caption("Pac-Man")              # título da barra da janela

font_hud   = pygame.font.SysFont(None, 28)  # fonte para score e vidas
font_title = pygame.font.SysFont(None, 64)  # fonte para GAME OVER, tela inicial, etc.

score = 0
vidas = 3

# --- Funções auxiliares de sprite ---
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

# --- Funções de colisão com o labirinto ---

def tile_at(px, py):
    # Converte coordenada de pixel para tile e retorna o caractere no MAZE_STR
    col = int(px) // TILE_SIZE
    row = (int(py) - MAZE_OFFSET_Y) // TILE_SIZE
    if 0 <= row < ROWS and 0 <= col < COLS:
        return maze[row][col]
    return ' '  # fora dos limites do mapa = espaço vazio

def can_move(x, y, dx, dy):
    # Verifica as duas extremidades da borda frontal do hitbox.
    # shrink=2: margem interna para passar por corredores sem travar nas bordas
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

# --- Sons ---
# pygame.mixer.Sound(buffer=) aceita um array de amostras no mesmo formato do mixer.
# Equivalente a pygame.mixer.Sound('arquivo.wav') — só a fonte dos dados muda.

def gerar_tom(freq, duracao_ms, volume=0.4):
    taxa = 44100
    n    = int(taxa * duracao_ms / 1000)
    buf  = array.array('h', [0] * n)
    for i in range(n):
        fade     = min(1.0, (n - i) / (taxa * 0.02 + 1))  # fade out nos últimos ~20ms
        buf[i]   = int(volume * 32767 * fade * math.sin(2 * math.pi * freq * i / taxa))
    return pygame.mixer.Sound(buffer=buf)

# Exercícios 13 e 14 — sons organizados em dicionário (assets)
sons = {
    'pellet': gerar_tom(880, 60),    # waka curto e agudo
    'power':  gerar_tom(440, 300),   # power pellet — mais grave e longo
    'morte':  gerar_tom(200, 700),   # morte — grave e lento
}


class Pacman(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # inicializa o Sprite base — obrigatório

        # Pré-computa as 4 rotações do sprite; pygame.transform.rotate gira no sentido anti-horário
        base = criar_sprite_pacman()
        self.sprites_dir = {
            ( 1,  0): base,
            (-1,  0): pygame.transform.rotate(base, 180),
            ( 0, -1): pygame.transform.rotate(base,  90),
            ( 0,  1): pygame.transform.rotate(base, 270),
        }

        self.dx      = 1   # direção atual de movimento
        self.dy      = 0
        self.next_dx = 1   # próxima direção solicitada pelo jogador (buffered input)
        self.next_dy = 0

        self.image = self.sprites_dir[(self.dx, self.dy)]  # imagem inicial
        self.rect  = self.image.get_rect()                 # rect define posição e hitbox
        self.rect.x = 13 * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + 23 * TILE_SIZE

    def update(self):
        # Tenta virar para a direção solicitada — só muda se não houver parede nessa direção
        if can_move(self.rect.x, self.rect.y, self.next_dx, self.next_dy):
            self.dx, self.dy = self.next_dx, self.next_dy

        # Move na direção atual se não houver parede na frente
        if can_move(self.rect.x, self.rect.y, self.dx, self.dy):
            self.rect.x += self.dx * SPEED
            self.rect.y += self.dy * SPEED

        # Teleporte pelo corredor da linha 14 — rect.right e rect.left são atributos do Rect
        if (self.rect.y - MAZE_OFFSET_Y) // TILE_SIZE == 14:
            if self.rect.right <= 0:    # saiu pela esquerda
                self.rect.x = WIDTH
            elif self.rect.left >= WIDTH:  # saiu pela direita
                self.rect.x = 0

        # Atualiza a imagem de acordo com a direção atual
        self.image = self.sprites_dir[(self.dx, self.dy)]

    def reset(self):
        self.rect.x            = 13 * TILE_SIZE
        self.rect.y            = MAZE_OFFSET_Y + 23 * TILE_SIZE
        self.dx,      self.dy      = 1, 0
        self.next_dx, self.next_dy = 1, 0


class Ghost(pygame.sprite.Sprite):
    def __init__(self, col, row, cor):
        pygame.sprite.Sprite.__init__(self)  # inicializa o Sprite base — obrigatório

        self.image = criar_sprite_fantasma(cor)  # Surface com o desenho do fantasma
        self.rect  = self.image.get_rect()
        self.rect.x = col * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + row * TILE_SIZE

    def update(self):
        pass  # movimento dos fantasmas virá nas próximas etapas


player = Pacman()

blinky = Ghost(13, 11, RED)    # Blinky — vermelho, acima da porta
pinky  = Ghost(13, 14, PINK)   # Pinky  — rosa, centro da casa
inky   = Ghost(11, 14, CYAN)   # Inky   — ciano, esquerda da casa
clyde  = Ghost(15, 14, ORANGE) # Clyde  — laranja, direita da casa

# Groups (Etapa 8) — pygame.sprite.Group agrupa sprites para atualizar e desenhar de uma vez
all_sprites = pygame.sprite.Group()   # todos os sprites do jogo
ghosts      = pygame.sprite.Group()   # só os fantasmas — útil para colisões depois

all_sprites.add(player)
all_sprites.add(blinky, pinky, inky, clyde)  # add() aceita múltiplos sprites de uma vez
ghosts.add     (blinky, pinky, inky, clyde)  # cada fantasma entra em dois grupos

clock = pygame.time.Clock()  # relógio para controlar a velocidade do loop

# Máquina de estados — cada estado define o comportamento do game loop naquele frame
QUIT      = 0   # encerra o loop principal
PLAYING   = 1   # gameplay normal
DYING     = 2   # Pac-Man morreu; aguarda animação antes de respawnar ou game over
GAME_OVER = 3   # sem vidas — mostra tela de game over

state       = PLAYING
dying_start = 0   # momento (ms) em que o estado DYING começou

# Game loop: cada iteração gera um frame
while state != QUIT:

    # clock.tick(FPS) pausa o loop pelo tempo necessário para não ultrapassar FPS frames/s.
    # Sem isso, a velocidade do jogo variaria conforme o hardware. (Exercício 6)
    clock.tick(FPS)

    # 1. Tratar eventos
    # pygame.event.get() devolve todos os eventos desde o último frame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:                                    # usuário clicou no X da janela
            state = QUIT
        if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:  # ESC encerra
            state = QUIT
        if event.type == pygame.KEYDOWN:  # KEYDOWN: disparado uma vez quando a tecla é pressionada
            if state == PLAYING:          # setas só funcionam durante o jogo
                if event.key == pygame.K_RIGHT:
                    player.next_dx, player.next_dy =  1,  0
                elif event.key == pygame.K_LEFT:
                    player.next_dx, player.next_dy = -1,  0
                elif event.key == pygame.K_UP:
                    player.next_dx, player.next_dy =  0, -1
                elif event.key == pygame.K_DOWN:
                    player.next_dx, player.next_dy =  0,  1
            if state == GAME_OVER and event.key == pygame.K_RETURN:  # ENTER reinicia
                state = QUIT

    # 2. Verificar consequências

    if state == PLAYING:

        # Comer pellets — verifica o tile no centro de Pac-Man
        col_pm = player.rect.centerx // TILE_SIZE
        row_pm = (player.rect.centery - MAZE_OFFSET_Y) // TILE_SIZE
        if 0 <= row_pm < ROWS and 0 <= col_pm < COLS:
            t = maze[row_pm][col_pm]
            if t == '.':
                maze[row_pm][col_pm] = ' '
                score += 10
                sons['pellet'].play()
            elif t == 'o':
                maze[row_pm][col_pm] = ' '
                score += 50
                sons['power'].play()

        # Colisão com fantasmas — spritecollide retorna lista de fantasmas que tocaram Pac-Man
        # (Exercício 11 — spritecollide entre um sprite e um grupo)
        if pygame.sprite.spritecollide(player, ghosts, False):
            sons['morte'].play()
            vidas      -= 1
            state       = DYING                       # entra no estado de morte
            dying_start = pygame.time.get_ticks()     # registra o instante da morte

    if state == DYING:
        # Exercício 15 — aguarda duração fixa antes de agir (semelhante ao delay de tiro)
        # pygame.time.get_ticks() retorna ms desde que o pygame foi iniciado
        if pygame.time.get_ticks() - dying_start > 1500:
            if vidas > 0:
                player.reset()   # Exercício 16 — respawna Pac-Man após a animação
                state = PLAYING
            else:
                state = GAME_OVER

    # 3. Atualizar estado do jogo — chama update() de todos os sprites do grupo de uma vez
    if state == PLAYING:
        all_sprites.update()

    # 4. Gerar saídas — desenhar o frame

    window.fill(BLACK)  # apaga o frame anterior; sem isso os objetos deixariam rastro

    # --- Labirinto ---
    # Percorre o MAZE_STR tile por tile e desenha cada elemento na posição correta
    for row, linha in enumerate(maze):
        for col, tile in enumerate(linha):
            x  = col * TILE_SIZE
            y  = MAZE_OFFSET_Y + row * TILE_SIZE
            cx = x + TILE_SIZE // 2
            cy = y + TILE_SIZE // 2

            if tile == '#':
                pygame.draw.rect(window, BLUE, (x, y, TILE_SIZE, TILE_SIZE))   # parede
            elif tile == '.':
                pygame.draw.circle(window, WHITE, (cx, cy), 2)                 # pellet normal
            elif tile == 'o':
                pygame.draw.circle(window, YELLOW, (cx, cy), 5)                # power pellet
            elif tile == '-':
                pygame.draw.rect(window, PINK, (x, cy - 1, TILE_SIZE, 2))      # porta dos fantasmas

    # --- Sprites ---
    # Fantasmas são sempre desenhados; Pac-Man pisca durante DYING (a cada 150ms)
    ghosts.draw(window)
    piscar = (pygame.time.get_ticks() // 150) % 2 == 0  # alterna visível/invisível
    if state != DYING or piscar:
        window.blit(player.image, player.rect)

    # --- GAME OVER ---
    if state == GAME_OVER:
        txt = font_title.render("GAME OVER", True, RED)
        window.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        sub = font_hud.render("ENTER para sair", True, WHITE)
        window.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

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
import pygame
import sys
import math
import array  # gerar buffers de áudio sem dependências externas

pygame.init()
pygame.mixer.init(44100, -16, 1, 512)  # 44100 Hz, 16-bit signed, mono, buffer 512

TILE_SIZE     = 20    # cada tile do labirinto em pixels
COLS          = 28    # colunas do labirinto
ROWS          = 31    # linhas do labirinto
MAZE_OFFSET_Y = 40    # espaço de HUD acima do labirinto
SPEED         = 2     # pixels movidos por frame
FPS           = 60    # frames por segundo — limita a velocidade do loop em qualquer máquina

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
# list(row) torna cada linha mutável — necessário para apagar pellets comidos
maze = [list(row) for row in [
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
    "          #      #          ",  # 14  corredor de teleporte (esq ↔️ dir)
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
]]

window = pygame.display.set_mode((WIDTH, HEIGHT))  # cria a janela
pygame.display.set_caption("Pac-Man")              # título da barra da janela

font_hud   = pygame.font.SysFont(None, 28)  # fonte para score e vidas
font_title = pygame.font.SysFont(None, 64)  # fonte para GAME OVER, tela inicial, etc.

score = 0
vidas = 3

# --- Funções auxiliares de sprite ---
# pygame.image.load() também retorna um Surface — a interface é idêntica.
# pygame.SRCALPHA cria Surface com canal alpha (transparência), como .convert_alpha()

def criar_sprite_pacman(angulo_boca=30):
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    cx = cy = TILE_SIZE // 2
    r  = TILE_SIZE // 2 - 1
    pygame.draw.circle(surf, YELLOW, (cx, cy), r)  # corpo amarelo
    if angulo_boca > 0:  # angulo 0 = boca fechada (círculo completo)
        top    = (cx + r * math.cos(math.radians(-angulo_boca)), cy + r * math.sin(math.radians(-angulo_boca)))
        bottom = (cx + r * math.cos(math.radians( angulo_boca)), cy + r * math.sin(math.radians( angulo_boca)))
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

# --- Funções de colisão com o labirinto ---

def tile_at(px, py):
    # Converte coordenada de pixel para tile e retorna o caractere no MAZE_STR
    col = int(px) // TILE_SIZE
    row = (int(py) - MAZE_OFFSET_Y) // TILE_SIZE
    if 0 <= row < ROWS and 0 <= col < COLS:
        return maze[row][col]
    return ' '  # fora dos limites do mapa = espaço vazio

def can_move(x, y, dx, dy):
    # Verifica as duas extremidades da borda frontal do hitbox.
    # shrink=2: margem interna para passar por corredores sem travar nas bordas
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

# --- Sons ---
# pygame.mixer.Sound(buffer=) aceita um array de amostras no mesmo formato do mixer.
# Equivalente a pygame.mixer.Sound('arquivo.wav') — só a fonte dos dados muda.

def gerar_tom(freq, duracao_ms, volume=0.4):
    taxa = 44100
    n    = int(taxa * duracao_ms / 1000)
    buf  = array.array('h', [0] * n)
    for i in range(n):
        fade     = min(1.0, (n - i) / (taxa * 0.02 + 1))  # fade out nos últimos ~20ms
        buf[i]   = int(volume * 32767 * fade * math.sin(2 * math.pi * freq * i / taxa))
    return pygame.mixer.Sound(buffer=buf)

# Exercícios 13 e 14 — sons organizados em dicionário (assets)
sons = {
    'pellet': gerar_tom(880, 60),    # waka curto e agudo
    'power':  gerar_tom(440, 300),   # power pellet — mais grave e longo
    'morte':  gerar_tom(200, 700),   # morte — grave e lento
}


class Pacman(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # inicializa o Sprite base — obrigatório

        # Frames da animação: boca totalmente aberta → meio → fechada → meio (loop)
        # pygame.transform.rotate gira no sentido anti-horário
        _angulos = [30, 15, 0, 15]
        self.anim_frames = [
            {
                ( 1,  0): f,
                (-1,  0): pygame.transform.rotate(f, 180),
                ( 0, -1): pygame.transform.rotate(f,  90),
                ( 0,  1): pygame.transform.rotate(f, 270),
            }
            for f in (criar_sprite_pacman(a) for a in _angulos)
        ]
        self.anim_frame     = 0    # índice do frame atual
        self.last_anim_time = 0    # ms do último avanço de frame
        self.frame_ticks    = 100  # ms entre cada troca de frame

        self.dx      = 1   # direção atual de movimento
        self.dy      = 0
        self.next_dx = 1   # próxima direção solicitada pelo jogador (buffered input)
        self.next_dy = 0

        self.image = self.anim_frames[0][(self.dx, self.dy)]  # imagem inicial
        self.rect  = self.image.get_rect()                 # rect define posição e hitbox
        self.rect.x = 13 * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + 23 * TILE_SIZE

    def update(self):
        # Tenta virar para a direção solicitada — só muda se não houver parede nessa direção
        if can_move(self.rect.x, self.rect.y, self.next_dx, self.next_dy):
            self.dx, self.dy = self.next_dx, self.next_dy

        # Move na direção atual se não houver parede na frente
        if can_move(self.rect.x, self.rect.y, self.dx, self.dy):
            self.rect.x += self.dx * SPEED
            self.rect.y += self.dy * SPEED

        # Teleporte pelo corredor da linha 14 — rect.right e rect.left são atributos do Rect
        if (self.rect.y - MAZE_OFFSET_Y) // TILE_SIZE == 14:
            if self.rect.right <= 0:    # saiu pela esquerda
                self.rect.x = WIDTH
            elif self.rect.left >= WIDTH:  # saiu pela direita
                self.rect.x = 0

        # Animação — troca de frame a cada frame_ticks ms
        # pygame.time.get_ticks() retorna ms desde que o pygame foi iniciado
        agora = pygame.time.get_ticks()
        if agora - self.last_anim_time > self.frame_ticks:
            self.anim_frame     = (self.anim_frame + 1) % len(self.anim_frames)
            self.last_anim_time = agora

        self.image = self.anim_frames[self.anim_frame][(self.dx, self.dy)]

    def reset(self):
        self.rect.x            = 13 * TILE_SIZE
        self.rect.y            = MAZE_OFFSET_Y + 23 * TILE_SIZE
        self.dx,      self.dy      = 1, 0
        self.next_dx, self.next_dy = 1, 0


class Ghost(pygame.sprite.Sprite):
    def __init__(self, col, row, cor):
        pygame.sprite.Sprite.__init__(self)  # inicializa o Sprite base — obrigatório

        self.image = criar_sprite_fantasma(cor)  # Surface com o desenho do fantasma
        self.rect  = self.image.get_rect()
        self.rect.x = col * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + row * TILE_SIZE

    def update(self):
        pass  # movimento dos fantasmas virá nas próximas etapas


player = Pacman()

blinky = Ghost(13, 11, RED)    # Blinky — vermelho, acima da porta
pinky  = Ghost(13, 14, PINK)   # Pinky  — rosa, centro da casa
inky   = Ghost(11, 14, CYAN)   # Inky   — ciano, esquerda da casa
clyde  = Ghost(15, 14, ORANGE) # Clyde  — laranja, direita da casa

# Groups (Etapa 8) — pygame.sprite.Group agrupa sprites para atualizar e desenhar de uma vez
all_sprites = pygame.sprite.Group()   # todos os sprites do jogo
ghosts      = pygame.sprite.Group()   # só os fantasmas — útil para colisões depois

all_sprites.add(player)
all_sprites.add(blinky, pinky, inky, clyde)  # add() aceita múltiplos sprites de uma vez
ghosts.add     (blinky, pinky, inky, clyde)  # cada fantasma entra em dois grupos

clock = pygame.time.Clock()  # relógio para controlar a velocidade do loop

# Máquina de estados — cada estado define o comportamento do game loop naquele frame
QUIT      = 0   # encerra o loop principal
PLAYING   = 1   # gameplay normal
DYING     = 2   # Pac-Man morreu; aguarda animação antes de respawnar ou game over
GAME_OVER = 3   # sem vidas — mostra tela de game over

state       = PLAYING
dying_start = 0   # momento (ms) em que o estado DYING começou

# Game loop: cada iteração gera um frame
while state != QUIT:

    # clock.tick(FPS) pausa o loop pelo tempo necessário para não ultrapassar FPS frames/s.
    # Sem isso, a velocidade do jogo variaria conforme o hardware. (Exercício 6)
    clock.tick(FPS)

    # 1. Tratar eventos
    # pygame.event.get() devolve todos os eventos desde o último frame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:                                    # usuário clicou no X da janela
            state = QUIT
        if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:  # ESC encerra
            state = QUIT
        if event.type == pygame.KEYDOWN:  # KEYDOWN: disparado uma vez quando a tecla é pressionada
            if state == PLAYING:          # setas só funcionam durante o jogo
                if event.key == pygame.K_RIGHT:
                    player.next_dx, player.next_dy =  1,  0
                elif event.key == pygame.K_LEFT:
                    player.next_dx, player.next_dy = -1,  0
                elif event.key == pygame.K_UP:
                    player.next_dx, player.next_dy =  0, -1
                elif event.key == pygame.K_DOWN:
                    player.next_dx, player.next_dy =  0,  1
            if state == GAME_OVER and event.key == pygame.K_RETURN:  # ENTER reinicia
                state = QUIT

    # 2. Verificar consequências

    if state == PLAYING:

        # Comer pellets — verifica o tile no centro de Pac-Man
        col_pm = player.rect.centerx // TILE_SIZE
        row_pm = (player.rect.centery - MAZE_OFFSET_Y) // TILE_SIZE
        if 0 <= row_pm < ROWS and 0 <= col_pm < COLS:
            t = maze[row_pm][col_pm]
            if t == '.':
                maze[row_pm][col_pm] = ' '
                score += 10
                sons['pellet'].play()
            elif t == 'o':
                maze[row_pm][col_pm] = ' '
                score += 50
                sons['power'].play()

        # Colisão com fantasmas — spritecollide retorna lista de fantasmas que tocaram Pac-Man
        # (Exercício 11 — spritecollide entre um sprite e um grupo)
        if pygame.sprite.spritecollide(player, ghosts, False):
            sons['morte'].play()
            vidas      -= 1
            state       = DYING                       # entra no estado de morte
            dying_start = pygame.time.get_ticks()     # registra o instante da morte

    if state == DYING:
        # Exercício 15 — aguarda duração fixa antes de agir (semelhante ao delay de tiro)
        # pygame.time.get_ticks() retorna ms desde que o pygame foi iniciado
        if pygame.time.get_ticks() - dying_start > 1500:
            if vidas > 0:
                player.reset()   # Exercício 16 — respawna Pac-Man após a animação
                state = PLAYING
            else:
                state = GAME_OVER

    # 3. Atualizar estado do jogo — chama update() de todos os sprites do grupo de uma vez
    if state == PLAYING:
        all_sprites.update()

    # 4. Gerar saídas — desenhar o frame

    window.fill(BLACK)  # apaga o frame anterior; sem isso os objetos deixariam rastro

    # --- Labirinto ---
    # Percorre o MAZE_STR tile por tile e desenha cada elemento na posição correta
    for row, linha in enumerate(maze):
        for col, tile in enumerate(linha):
            x  = col * TILE_SIZE
            y  = MAZE_OFFSET_Y + row * TILE_SIZE
            cx = x + TILE_SIZE // 2
            cy = y + TILE_SIZE // 2

            if tile == '#':
                pygame.draw.rect(window, BLUE, (x, y, TILE_SIZE, TILE_SIZE))   # parede
            elif tile == '.':
                pygame.draw.circle(window, WHITE, (cx, cy), 2)                 # pellet normal
            elif tile == 'o':
                pygame.draw.circle(window, YELLOW, (cx, cy), 5)                # power pellet
            elif tile == '-':
                pygame.draw.rect(window, PINK, (x, cy - 1, TILE_SIZE, 2))      # porta dos fantasmas

    # --- Sprites ---
    # Fantasmas são sempre desenhados; Pac-Man pisca durante DYING (a cada 150ms)
    ghosts.draw(window)
    piscar = (pygame.time.get_ticks() // 150) % 2 == 0  # alterna visível/invisível
    if state != DYING or piscar:
        window.blit(player.image, player.rect)

    # --- GAME OVER ---
    if state == GAME_OVER:
        txt = font_title.render("GAME OVER", True, RED)
        window.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        sub = font_hud.render("ENTER para sair", True, WHITE)
        window.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

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