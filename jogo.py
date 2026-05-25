import pygame
import sys
import math
from fantasmas import mover_blinky, mover_pinky, mover_inky, mover_clyde, IN_HOUSE, EXITING, CHASING, EATEN
import medo

pygame.init()
pygame.mixer.init(44100, -16, 1, 512)

TILE_SIZE     = 20
COLS          = 28
ROWS          = 31
MAZE_OFFSET_Y = 40
SPEED         = 2
FPS           = 60

WIDTH  = COLS * TILE_SIZE
HEIGHT = ROWS * TILE_SIZE + MAZE_OFFSET_Y + 20

BLACK  = (  0,   0,   0)
WHITE  = (255, 255, 255)
YELLOW = (255, 255,   0)
BLUE   = ( 33,  33, 255)
RED    = (255,   0,   0)
PINK   = (255, 184, 255)
CYAN   = (  0, 255, 255)
ORANGE = (255, 184,  82)

# Mapa original — guardado para restaurar no reinício
_MAZE_ROWS = [
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
    "          #      #          ",  # 14  corredor de teleporte
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
]

maze = [list(row) for row in _MAZE_ROWS]

fullscreen = False
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man")

font_hud   = pygame.font.SysFont(None, 28)
font_title = pygame.font.SysFont(None, 64)
font_press = pygame.font.SysFont(None, 46)
font_small = pygame.font.SysFont(None, 22)


score = 0
vidas = 3

# Rects para detecção de clique/hover — atualizados a cada frame de desenho
_press_start_rect = pygame.Rect(0, 0, 0, 0)
_yes_rect         = pygame.Rect(0, 0, 0, 0)
_no_rect          = pygame.Rect(0, 0, 0, 0)
_go_cursor        = 0   # 0 = YES  /  1 = NO
_fantasmas_comidos_rodada = 0   # fantasmas comidos no efeito da bolinha atual


# ── Sprites ────────────────────────────────────────────────────────────────────

def criar_sprite_pacman(angulo_boca=30):
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    cx = cy = TILE_SIZE // 2
    r  = TILE_SIZE // 2 - 1
    pygame.draw.circle(surf, YELLOW, (cx, cy), r)
    if 0 < angulo_boca < 180:
        steps  = max(3, int(angulo_boca / 5))
        pontos = [(cx, cy)]
        for i in range(steps + 1):
            ang = -angulo_boca + 2 * angulo_boca * i / steps
            pontos.append((
                cx + r * math.cos(math.radians(ang)),
                cy + r * math.sin(math.radians(ang)),
            ))
        pygame.draw.polygon(surf, BLACK, pontos)
    elif angulo_boca >= 180:
        surf.fill((0, 0, 0, 0))   # círculo completo aberto = Pac-Man desaparece
    return surf


def criar_sprite_fantasma(cor):
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    cx   = TILE_SIZE // 2
    r    = TILE_SIZE // 2
    pygame.draw.circle(surf, cor, (cx, r), r)
    pygame.draw.rect  (surf, cor, (0, r, TILE_SIZE, r))
    for i in range(3):
        pygame.draw.circle(surf, BLACK, (3 + i * 7, TILE_SIZE), 3)
    pygame.draw.circle(surf, WHITE, (cx - 4, r - 2), 3)
    pygame.draw.circle(surf, WHITE, (cx + 4, r - 2), 3)
    pygame.draw.circle(surf, BLUE,  (cx - 3, r - 2), 1)
    pygame.draw.circle(surf, BLUE,  (cx + 3, r - 2), 1)
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


# ── Colisão ─────────────────────────────────────────────────────────────────

def tile_at(px, py):
    col = int(px) // TILE_SIZE
    row = (int(py) - MAZE_OFFSET_Y) // TILE_SIZE
    if 0 <= row < ROWS and 0 <= col < COLS:
        return maze[row][col]
    return ' '


def can_move(x, y, dx, dy):
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


# ── Sons ────────────────────────────────────────────────────────────────────

sons = {
    'pellet':       pygame.mixer.Sound('sons/pacman_chomp.wav'),
    'power':        pygame.mixer.Sound('sons/pacman_eatfruit.wav'),
    'morte':        pygame.mixer.Sound('sons/pacman_death.wav'),
    'comer_fantasma': pygame.mixer.Sound('sons/pacman_eatghost.wav'),
    'extra_vida':   pygame.mixer.Sound('sons/pacman_extrapac.wav'),
    'beginning':    pygame.mixer.Sound('sons/pacman_beginning.wav'),
    'intermission': pygame.mixer.Sound('sons/pacman_intermission.wav'),
}
sons['pellet'].set_volume(0.5)  # chomp toca com frequência — volume moderado

vida_icon = pygame.transform.scale(criar_sprite_pacman(25), (16, 16))

_surf_medo_azul   = criar_sprite_fantasma((0,   50, 255))
_surf_medo_branco = criar_sprite_fantasma((255, 255, 255))
_surf_olhos       = criar_sprite_olhos()

# Sprites 3× para tela de início
_SZ = TILE_SIZE * 3

def _escalar(surf):
    return pygame.transform.scale(surf, (_SZ, _SZ))

_start_pacman = _escalar(criar_sprite_pacman(30))
_start_ghosts = [
    _escalar(criar_sprite_fantasma(PINK)),
    _escalar(criar_sprite_fantasma(CYAN)),
    _escalar(criar_sprite_fantasma(ORANGE)),
    _escalar(criar_sprite_fantasma(RED)),
]


# ── Classes ──────────────────────────────────────────────────────────────────

class Pacman(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

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
        self.anim_frame     = 0
        self.last_anim_time = 0
        self.frame_ticks    = 100

        # Frames da animação de morte: boca abre de 30° até sumir
        self.morte_frames = [criar_sprite_pacman(a) for a in range(30, 181, 15)]

        self.dx      = 1
        self.dy      = 0
        self.next_dx = 1
        self.next_dy = 0

        self.image = self.anim_frames[0][(self.dx, self.dy)]
        self.rect  = self.image.get_rect()
        self.rect.x = 13 * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + 23 * TILE_SIZE

    def update(self):
        if (self.next_dx, self.next_dy) != (self.dx, self.dy):
            nx, ny = self.rect.x, self.rect.y
            virou = False

            if can_move(nx, ny, self.next_dx, self.next_dy):
                virou = True
            elif self.dx != 0 and self.next_dy != 0:
                rem = nx % TILE_SIZE
                if 0 < rem <= SPEED * 2:
                    nx -= rem
                    if can_move(nx, ny, self.next_dx, self.next_dy):
                        self.rect.x = nx
                        virou = True
            elif self.dy != 0 and self.next_dx != 0:
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
        pygame.sprite.Sprite.__init__(self)

        self.cor   = cor
        self.col0  = col
        self.row0  = row
        self.image = criar_sprite_fantasma(cor)
        self.rect  = self.image.get_rect()
        self.rect.x = col * TILE_SIZE
        self.rect.y = MAZE_OFFSET_Y + row * TILE_SIZE
        self.dx = 0
        self.dy = 0

    def update(self):
        pass


# ── Sprites e grupos ──────────────────────────────────────────────────────────

player = Pacman()

blinky = Ghost(13, 11, RED)
pinky  = Ghost(13, 14, PINK)
inky   = Ghost(11, 14, CYAN)
clyde  = Ghost(15, 14, ORANGE)

all_sprites = pygame.sprite.Group()
ghosts      = pygame.sprite.Group()

all_sprites.add(player)
all_sprites.add(blinky, pinky, inky, clyde)
ghosts.add     (blinky, pinky, inky, clyde)


# ── Funções de jogo ───────────────────────────────────────────────────────────

def _iniciar_fantasmas():
    agora = pygame.time.get_ticks()

    blinky.rect.x = 13 * TILE_SIZE
    blinky.rect.y = MAZE_OFFSET_Y + 11 * TILE_SIZE
    blinky.dx, blinky.dy = -1, 0
    blinky.estado = CHASING
    blinky.liberado_em = 0

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


def _reiniciar_tudo():
    global score, vidas, maze
    score          = 0
    vidas          = 3
    maze           = [list(row) for row in _MAZE_ROWS]
    medo._ativo    = False
    player.reset()
    _iniciar_fantasmas()


def _aguardar_jingle():
    channel = sons['beginning'].play()
    pygame.event.clear()
    while channel and channel.get_busy():
        clock.tick(FPS)
        quit_req = False
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                quit_req = True
            if evt.type == pygame.KEYUP and evt.key == pygame.K_ESCAPE:
                quit_req = True
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_F11:
                    _toggle_fullscreen()
                elif evt.key == pygame.K_RIGHT:
                    player.next_dx, player.next_dy =  1,  0
                elif evt.key == pygame.K_LEFT:
                    player.next_dx, player.next_dy = -1,  0
                elif evt.key == pygame.K_UP:
                    player.next_dx, player.next_dy =  0, -1
                elif evt.key == pygame.K_DOWN:
                    player.next_dx, player.next_dy =  0,  1
        if quit_req:
            channel.stop()
            return False
        window.fill(BLACK)
        for row, linha in enumerate(maze):
            for col, tile in enumerate(linha):
                x  = col * TILE_SIZE
                y  = MAZE_OFFSET_Y + row * TILE_SIZE
                cx = x + TILE_SIZE // 2
                cy = y + TILE_SIZE // 2
                if tile == '#':
                    pygame.draw.rect(window, BLUE, (x, y, TILE_SIZE, TILE_SIZE))
                elif tile == '.':
                    pygame.draw.circle(window, WHITE, (cx, cy), 2)
                elif tile == 'o':
                    pygame.draw.circle(window, YELLOW, (cx, cy), 5)
                elif tile == '-':
                    pygame.draw.rect(window, PINK, (x, cy - 1, TILE_SIZE, 2))
        for g in ghosts:
            window.blit(g.image, g.rect)
        window.blit(player.image, player.rect)
        window.blit(font_hud.render("1UP",      True, WHITE), (10,  4))
        window.blit(font_hud.render(str(score), True, WHITE), (10, 20))
        for i in range(vidas):
            window.blit(vida_icon, (8 + i * 20, HEIGHT - 18))
        ready = font_hud.render("GET READY!", True, YELLOW)
        window.blit(ready, ready.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.update()
    pygame.event.clear()
    return True


def pellets_remaining():
    return sum(tile in ('.', 'o') for row in maze for tile in row)


def _toggle_fullscreen():
    global window, fullscreen
    fullscreen = not fullscreen
    flags = (pygame.FULLSCREEN | pygame.SCALED) if fullscreen else 0
    window = pygame.display.set_mode((WIDTH, HEIGHT), flags)


# ── Funções de desenho ────────────────────────────────────────────────────────

def _overlay_escuro():
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 170))
    window.blit(ov, (0, 0))


def _render_outlined(font, text, color, outline_color, cx, cy):
    outline = font.render(text, True, outline_color)
    inner   = font.render(text, True, color)
    r = inner.get_rect(center=(cx, cy))
    for dx, dy in [(-3,-3),(-3,0),(-3,3),(0,-3),(0,3),(3,-3),(3,0),(3,3)]:
        window.blit(outline, (r.x + dx, r.y + dy))
    window.blit(inner, r)


def _desenhar_tela_inicio():
    global _press_start_rect
    agora  = pygame.time.get_ticks()
    cx     = WIDTH // 2

    # Layout: pacman + dots + ghosts
    n_dots    = 5
    dot_w     = 8
    dot_gap   = 22
    ghost_gap = 12
    row_w = _SZ + 30 + (n_dots * dot_w + (n_dots - 1) * dot_gap) + 30 + (4 * _SZ + 3 * ghost_gap)
    x0    = (WIDTH - row_w) // 2
    sy    = HEIGHT // 2 - _SZ // 2 - 30

    # Pac-Man
    window.blit(_start_pacman, (x0, sy))
    refl_pm = pygame.transform.flip(_start_pacman, False, True)
    refl_pm.set_alpha(55)
    window.blit(refl_pm, (x0, sy + _SZ))

    # Pontos
    dx0   = x0 + _SZ + 30
    dot_y = sy + _SZ // 2 - dot_w // 2
    for i in range(n_dots):
        pygame.draw.rect(window, WHITE, (dx0 + i * (dot_w + dot_gap), dot_y, dot_w, dot_w))

    # Fantasmas
    gx0 = dx0 + n_dots * dot_w + (n_dots - 1) * dot_gap + 30
    for i, g_surf in enumerate(_start_ghosts):
        gx = gx0 + i * (_SZ + ghost_gap)
        window.blit(g_surf, (gx, sy))
        refl_g = pygame.transform.flip(g_surf, False, True)
        refl_g.set_alpha(55)
        window.blit(refl_g, (gx, sy + _SZ))

    # Título
    titulo = font_title.render("PAC-MAN", True, YELLOW)
    window.blit(titulo, titulo.get_rect(center=(cx, HEIGHT // 5)))

    # "PRESS START" — sempre calcula o rect; só desenha na metade "ligada" do blink
    press_surf_ref = font_press.render("PRESS START", True, YELLOW)
    _press_start_rect = press_surf_ref.get_rect(center=(cx, HEIGHT * 3 // 4))

    mouse_pos   = pygame.mouse.get_pos()
    hover       = _press_start_rect.collidepoint(mouse_pos)
    press_color = WHITE if hover else YELLOW

    if (agora // 500) % 2 == 0 or hover:
        press_surf = font_press.render("PRESS START", True, press_color)
        window.blit(press_surf, _press_start_rect)

    # Dica de tela cheia
    hint = font_small.render("F11 — tela cheia", True, (100, 100, 100))
    window.blit(hint, hint.get_rect(center=(cx, HEIGHT - 14)))


def _desenhar_game_over():
    global _yes_rect, _no_rect
    cx = WIDTH // 2

    # Bola vermelha com X
    ball_cy = HEIGHT // 2 - 98
    ball_r  = 26
    pygame.draw.circle(window, (180, 0, 0), (cx, ball_cy), ball_r)
    pygame.draw.circle(window, (230, 50, 50), (cx - 8, ball_cy - 8), 9)   # reflexo
    pygame.draw.line(window, BLACK, (cx - 15, ball_cy - 15), (cx + 15, ball_cy + 15), 5)
    pygame.draw.line(window, BLACK, (cx + 15, ball_cy - 15), (cx - 15, ball_cy + 15), 5)
    pygame.draw.circle(window, (210, 0, 0), (cx, ball_cy), ball_r, 3)      # aro

    # "GAME OVER" com contorno preto
    _render_outlined(font_title, "GAME OVER", RED, BLACK, cx, HEIGHT // 2 - 40)

    # "DO YOU WANT CONTINUE?"
    q = font_small.render("DO YOU WANT CONTINUE?", True, WHITE)
    window.blit(q, q.get_rect(center=(cx, HEIGHT // 2 + 18)))

    # YES / NO  (amarelo = selecionado)
    yes_color = YELLOW if _go_cursor == 0 else WHITE
    no_color  = YELLOW if _go_cursor == 1 else WHITE

    # Hover pelo mouse
    mouse_pos = pygame.mouse.get_pos()
    if _yes_rect.collidepoint(mouse_pos):
        yes_color = YELLOW
    if _no_rect.collidepoint(mouse_pos):
        no_color  = YELLOW

    yes_surf  = font_hud.render("YES", True, yes_color)
    no_surf   = font_hud.render("NO",  True, no_color)
    _yes_rect = yes_surf.get_rect(center=(cx - 55, HEIGHT // 2 + 52))
    _no_rect  = no_surf.get_rect(center=(cx + 55,  HEIGHT // 2 + 52))
    window.blit(yes_surf, _yes_rect)
    window.blit(no_surf,  _no_rect)

    # Triângulo cursor ▲ abaixo da opção selecionada
    sel = _yes_rect if _go_cursor == 0 else _no_rect
    tri_cx = sel.centerx
    tri_y  = HEIGHT // 2 + 74
    pygame.draw.polygon(window, YELLOW,
                        [(tri_cx, tri_y), (tri_cx - 8, tri_y + 14), (tri_cx + 8, tri_y + 14)])

    # Dica de teclado
    hint = font_small.render("◄ ► mover   ENTER confirmar", True, (90, 90, 90))
    window.blit(hint, hint.get_rect(center=(cx, HEIGHT // 2 + 105)))


# ── Estados ──────────────────────────────────────────────────────────────────

clock = pygame.time.Clock()

QUIT      = 0
PLAYING   = 1
DYING     = 2
GAME_OVER = 3
START     = 4
STARTING  = 5   # jingle tocando antes do jogo começar

state       = START
dying_start = 0


# ── Game loop ─────────────────────────────────────────────────────────────────

while state != QUIT:

    clock.tick(FPS)

    # 1. Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state = QUIT

        if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
            state = QUIT

        # Clique do mouse
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == START and _press_start_rect.collidepoint(event.pos):
                _reiniciar_tudo()
                state = STARTING
            elif state == GAME_OVER:
                if _yes_rect.collidepoint(event.pos):
                    _reiniciar_tudo()
                    state = STARTING
                elif _no_rect.collidepoint(event.pos):
                    state = START

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                _toggle_fullscreen()

            if state == START:
                _reiniciar_tudo()
                state = STARTING

            if state == PLAYING:
                if event.key == pygame.K_RIGHT:
                    player.next_dx, player.next_dy =  1,  0
                elif event.key == pygame.K_LEFT:
                    player.next_dx, player.next_dy = -1,  0
                elif event.key == pygame.K_UP:
                    player.next_dx, player.next_dy =  0, -1
                elif event.key == pygame.K_DOWN:
                    player.next_dx, player.next_dy =  0,  1

            if state == GAME_OVER:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    _go_cursor = 0
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    _go_cursor = 1
                elif event.key == pygame.K_RETURN:
                    if _go_cursor == 0:
                        _reiniciar_tudo()
                        state = STARTING
                    else:
                        state = START

    # 2. Tocar jingle e aguardar antes de começar
    if state == STARTING:
        if not _aguardar_jingle():
            state = QUIT
        else:
            _iniciar_fantasmas()   # re-inicia timers com hora correta (após a jingle)
            state = PLAYING

    # 3. Verificar consequências
    if state == PLAYING:

        col_pm = player.rect.centerx // TILE_SIZE
        row_pm = (player.rect.centery - MAZE_OFFSET_Y) // TILE_SIZE
        if 0 <= row_pm < ROWS and 0 <= col_pm < COLS:
            t = maze[row_pm][col_pm]
            if t == '.':
                maze[row_pm][col_pm] = ' '
                score += 10
                if sons['pellet'].get_num_channels() == 0:
                    sons['pellet'].play()
            elif t == 'o':
                maze[row_pm][col_pm] = ' '
                score += 50
                sons['power'].play()
                medo.ativar()
                _fantasmas_comidos_rodada = 0   # nova bolinha — zera a contagem

        if pellets_remaining() == 0:
            maze = [list(row) for row in _MAZE_ROWS]
            medo._ativo = False
            _fantasmas_comidos_rodada = 0
            player.reset()
            _iniciar_fantasmas()
            sons['intermission'].play()

        colisoes = pygame.sprite.spritecollide(player, ghosts, False)
        if colisoes:
            if medo.ativo():
                for g in colisoes:
                    if g.estado == CHASING:
                        _fantasmas_comidos_rodada += 1
                        score += 200 * _fantasmas_comidos_rodada
                        g.estado = EATEN
                        sons['comer_fantasma'].play()
                        if _fantasmas_comidos_rodada == 4:
                            vidas += 1
                            sons['extra_vida'].play()
                            _fantasmas_comidos_rodada = 0
            else:
                if any(g.estado == CHASING for g in colisoes):
                    sons['morte'].play()
                    vidas      -= 1
                    state       = DYING
                    dying_start = pygame.time.get_ticks()

    if state == DYING:
        if pygame.time.get_ticks() - dying_start > 1500:
            if vidas > 0:
                player.reset()
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
                _go_cursor = 0
                state = GAME_OVER

    # 4. Atualizar sprites
    if state == PLAYING:
        all_sprites.update()
        mover_blinky(blinky, player)
        mover_pinky(pinky, player)
        mover_inky(inky, player, blinky)
        mover_clyde(clyde, player)

    # 5. Desenhar
    window.fill(BLACK)

    if state == START:
        _desenhar_tela_inicio()

    else:
        # Labirinto
        for row, linha in enumerate(maze):
            for col, tile in enumerate(linha):
                x  = col * TILE_SIZE
                y  = MAZE_OFFSET_Y + row * TILE_SIZE
                cx = x + TILE_SIZE // 2
                cy = y + TILE_SIZE // 2

                if tile == '#':
                    pygame.draw.rect(window, BLUE, (x, y, TILE_SIZE, TILE_SIZE))
                elif tile == '.':
                    pygame.draw.circle(window, WHITE, (cx, cy), 2)
                elif tile == 'o':
                    pygame.draw.circle(window, YELLOW, (cx, cy), 5)
                elif tile == '-':
                    pygame.draw.rect(window, PINK, (x, cy - 1, TILE_SIZE, 2))

        # Fantasmas e Pac-Man
        for g in ghosts:
            if g.estado == EATEN:
                window.blit(_surf_olhos, g.rect)
            elif medo.ativo() and g.estado == CHASING:
                surf = _surf_medo_branco if medo.piscando() and (pygame.time.get_ticks() // 250) % 2 == 0 else _surf_medo_azul
                window.blit(surf, g.rect)
            else:
                window.blit(g.image, g.rect)

        if state == DYING:
            frame_idx = (pygame.time.get_ticks() - dying_start) // 130
            if frame_idx < len(player.morte_frames):
                window.blit(player.morte_frames[frame_idx], player.rect)
        else:
            window.blit(player.image, player.rect)

        # HUD
        window.blit(font_hud.render("1UP",      True, WHITE), (10,  4))
        window.blit(font_hud.render(str(score), True, WHITE), (10, 20))
        for i in range(vidas):
            window.blit(vida_icon, (8 + i * 20, HEIGHT - 18))

        # Overlay de GAME OVER
        if state == GAME_OVER:
            _overlay_escuro()
            _desenhar_game_over()

    pygame.display.update()

pygame.quit()
sys.exit()
