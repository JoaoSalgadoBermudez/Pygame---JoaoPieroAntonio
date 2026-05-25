import pygame
import sys
import math
import array  # gerar buffers de áudio sem dependências externas
from fantasmas import mover_blinky, mover_pinky, mover_inky, mover_clyde, IN_HOUSE, EXITING, CHASING, EATEN
import medo

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
    "#o####.#####.##.#####.####o#",  # 22
    "#...##.......  .......##...#",  # 23
    "###.##.##.########.##.##.###",  # 24
    "###.##.##.########.##.##.###",  # 25
    "#......##....##....##......#",  # 26
    "#.##########.##.##########.#",  # 27
    "#.##########.##.##########.#",  # 28
    "#..........................#",  # 29
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

def criar_sprite_olhos():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    cx = TILE_SIZE // 2
    r  = TILE_SIZE // 2
    pygame.draw.circle(surf, WHITE, (cx - 4, r - 2), 3)
    pygame.draw.circle(surf, WHITE, (cx + 4, r - 2), 3)
    pygame.draw.circle(surf, BLUE,  (cx - 3, r - 2), 1)
    pygame.draw.circle(surf, BLUE,  (cx + 3, r - 2), 1)
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
    'pellet':         gerar_tom(880,  60),
    'power':          gerar_tom(440, 300),
    'morte':          gerar_tom(200, 700),
    'comer_fantasma': gerar_tom(600, 150),
}

# Ícone de vida usado no HUD — pequeno sprite do Pac-Man (Exercício 17/18)
vida_icon = pygame.transform.scale(criar_sprite_pacman(25), (16, 16))

# Superfícies especiais — criadas uma vez para não recriar todo frame
_surf_medo_azul   = criar_sprite_fantasma((0,   50, 255))
_surf_medo_branco = criar_sprite_fantasma((255, 255, 255))
_surf_olhos       = criar_sprite_olhos()


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
        if (self.next_dx, self.next_dy) != (self.dx, self.dy):
            nx, ny = self.rect.x, self.rect.y
            virou = False

            # Tenta virar na posição atual (sem correção)
            if can_move(nx, ny, self.next_dx, self.next_dy):
                virou = True

            # Se falhou e é uma virada de 90°: tenta um recuo mínimo (máx. SPEED*2 = 4px)
            # para alinhar com a borda do tile. Sem snap para frente — nunca teleporta.
            elif self.dx != 0 and self.next_dy != 0:   # horizontal → vertical
                rem = nx % TILE_SIZE
                if 0 < rem <= SPEED * 2:
                    nx -= rem
                    if can_move(nx, ny, self.next_dx, self.next_dy):
                        self.rect.x = nx
                        virou = True
            elif self.dy != 0 and self.next_dx != 0:   # vertical → horizontal
                rem = (ny - MAZE_OFFSET_Y) % TILE_SIZE
                if 0 < rem <= SPEED * 2:
                    ny -= rem
                    if can_move(nx, ny, self.next_dx, self.next_dy):
                        self.rect.y = ny
                        virou = True

            if virou:
                self.dx, self.dy = self.next_dx, self.next_dy

        if can_move(self.rect.x, self.rect.y, self.dx, self.dy):
            self.rect.x += self.dx * SPEED
            self.rect.y += self.dy * SPEED

        if (self.rect.y - MAZE_OFFSET_Y) // TILE_SIZE == 14:
            if self.rect.right <= 0:
                self.rect.x = WIDTH
            elif self.rect.left >= WIDTH:
                self.rect.x = 0

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

        self.cor   = cor
        self.col0  = col   # coluna inicial — usada para respawnar na casinha
        self.row0  = row
        self.image = criar_sprite_fantasma(cor)
        self.rect  = self.image.get_rect()
        self.rect.x = col * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + row * TILE_SIZE
        self.dx = 0  # direção atual — usada pela IA para não reverter o movimento
        self.dy = 0

    def reset(self):
        # respawna no ponto de saída da casinha já pronto para perseguir
        self.rect.x = 13 * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + 11 * TILE_SIZE
        self.dx     = -1
        self.dy     = 0
        self.estado = CHASING

    def update(self):
        pass


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

# Estados dos fantasmas e tempos de liberação da casinha
_t0 = pygame.time.get_ticks()

blinky.estado = CHASING    # começa fora, persegue imediatamente
blinky.liberado_em = 0
blinky.dx = -1

pinky.estado = IN_HOUSE
pinky.liberado_em = _t0 + 5_000   # sai após 5s
pinky.dy = -1                       # começa subindo na casinha

inky.estado = IN_HOUSE
inky.liberado_em = _t0 + 12_000   # sai após 12s
inky.dy = 1                         # começa descendo

clyde.estado = IN_HOUSE
clyde.liberado_em = _t0 + 20_000  # sai após 20s
clyde.dy = -1

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
                medo.ativar()

        # Colisão com fantasmas
        colisoes = pygame.sprite.spritecollide(player, ghosts, False)
        if colisoes:
            if medo.ativo():
                for g in colisoes:
                    if g.estado == CHASING:
                        score += 200
                        g.estado = EATEN   # olhinhos voltam para a casinha
                        sons['comer_fantasma'].play()
            else:
                # só morre se bater em fantasma solto (não na casinha ou a caminho dela)
                if any(g.estado == CHASING for g in colisoes):
                    sons['morte'].play()
                    vidas      -= 1
                    state       = DYING
                    dying_start = pygame.time.get_ticks()

    if state == DYING:
        if pygame.time.get_ticks() - dying_start > 1500:
            if vidas > 0:
                player.reset()

                # Reinicia todos os fantasmas para as posições e estados iniciais
                agora = pygame.time.get_ticks()

                blinky.rect.x = 13 * TILE_SIZE
                blinky.rect.y = MAZE_OFFSET_Y + 11 * TILE_SIZE
                blinky.dx, blinky.dy = -1, 0
                blinky.estado = CHASING

                pinky.rect.x = 13 * TILE_SIZE
                pinky.rect.y = MAZE_OFFSET_Y + 14 * TILE_SIZE
                pinky.dx, pinky.dy = 0, -1
                pinky.estado = IN_HOUSE
                pinky.liberado_em = agora + 5_000

                inky.rect.x = 11 * TILE_SIZE
                inky.rect.y = MAZE_OFFSET_Y + 14 * TILE_SIZE
                inky.dx, inky.dy = 0, 1
                inky.estado = IN_HOUSE
                inky.liberado_em = agora + 12_000

                clyde.rect.x = 15 * TILE_SIZE
                clyde.rect.y = MAZE_OFFSET_Y + 14 * TILE_SIZE
                clyde.dx, clyde.dy = 0, -1
                clyde.estado = IN_HOUSE
                clyde.liberado_em = agora + 20_000

                state = PLAYING
            else:
                state = GAME_OVER

    # 3. Atualizar estado do jogo — chama update() de todos os sprites do grupo de uma vez
    if state == PLAYING:
        all_sprites.update()
        mover_blinky(blinky, player)           # Blinky persegue direto o Pac-Man
        mover_pinky(pinky, player)             # Pinky mira 4 tiles à frente do Pac-Man
        mover_inky(inky, player, blinky)       # Inky usa vetor Blinky→Pac-Man duplicado
        mover_clyde(clyde, player)             # Clyde persegue se longe, foge se perto

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
    for g in ghosts:
        if g.estado == EATEN:
            window.blit(_surf_olhos, g.rect)
        elif medo.ativo() and g.estado == CHASING:
            surf = _surf_medo_branco if medo.piscando() and (pygame.time.get_ticks() // 250) % 2 == 0 else _surf_medo_azul
            window.blit(surf, g.rect)
        else:
            window.blit(g.image, g.rect)
    piscar = (pygame.time.get_ticks() // 150) % 2 == 0  # alterna visível/invisível
    if state != DYING or piscar:
        window.blit(player.image, player.rect)

    # --- GAME OVER ---
    if state == GAME_OVER:
        txt = font_title.render("GAME OVER", True, RED)
        window.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        sub = font_hud.render("ENTER para sair", True, WHITE)
        window.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

    # --- HUD: score no topo, ícones de vida na base ---
    # "1UP" + pontuação no canto superior esquerdo (layout clássico do Pac-Man)
    window.blit(font_hud.render("1UP",    True, WHITE), (10,  4))
    window.blit(font_hud.render(str(score), True, WHITE), (10, 20))

    # Ícones de vida: um sprite de Pac-Man por vida restante (Exercício 17/18)
    # Exercício 17 — no Pac-Man o score persiste entre mortes; zera apenas ao reiniciar
    for i in range(vidas):
        window.blit(vida_icon, (8 + i * 20, HEIGHT - 18))

    pygame.display.update()  # envia o frame desenhado para a tela

# Finalização
pygame.quit()  # fecha todos os recursos do pygame
sys.exit()     # encerra o processo Python