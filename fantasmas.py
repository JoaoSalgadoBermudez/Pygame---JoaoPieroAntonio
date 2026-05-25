import math
import random
import pygame

TILE_SIZE     = 20
MAZE_OFFSET_Y = 40
SPEED         = 2
_MAZE_WIDTH   = 28 * TILE_SIZE
_TELEPORT_ROW = 14

_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# Estados de cada fantasma
IN_HOUSE = 0   # quicando dentro da casinha, aguardando liberação
EXITING  = 1   # saindo pela porta em direção ao labirinto
CHASING  = 2   # livre no labirinto (perseguindo ou fugindo se assustado)
EATEN    = 3   # comido — olhinhos voltando para a casinha

# Coordenadas de referência da casinha
_EXIT_X         = 13 * TILE_SIZE                   # coluna central da saída (260px)
_EXIT_Y         = MAZE_OFFSET_Y + 11 * TILE_SIZE   # linha logo fora da porta (260px)
_HOUSE_TOP_Y    = MAZE_OFFSET_Y + 13 * TILE_SIZE   # limite superior do bounce (300px)
_HOUSE_BOT_Y    = MAZE_OFFSET_Y + 15 * TILE_SIZE   # limite inferior do bounce (340px)
_RETURN_X       = 13 * TILE_SIZE                   # coluna alvo ao voltar (260px)
_RETURN_Y       = MAZE_OFFSET_Y + 14 * TILE_SIZE   # centro da casinha (320px)


# ──────────────────────────────────────────────
# Funções de colisão

def _can_move_chasing(x, y, dx, dy):
    import jogo
    shrink = 2
    nx, ny = x + dx * SPEED, y + dy * SPEED
    if dx != 0:
        borda_x = nx + TILE_SIZE - 1 if dx > 0 else nx
        t1 = jogo.tile_at(borda_x, ny + shrink)
        t2 = jogo.tile_at(borda_x, ny + TILE_SIZE - 1 - shrink)
    else:
        borda_y = ny + TILE_SIZE - 1 if dy > 0 else ny
        t1 = jogo.tile_at(nx + shrink, borda_y)
        t2 = jogo.tile_at(nx + TILE_SIZE - 1 - shrink, borda_y)
    # bloqueia paredes E a porta — fantasma solto não pode reentrar na casinha
    return t1 not in ('#', '-') and t2 not in ('#', '-')


def _dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def _tile_aligned(ghost):
    return (
        ghost.rect.x % TILE_SIZE == 0 and
        (ghost.rect.y - MAZE_OFFSET_Y) % TILE_SIZE == 0
    )


# ──────────────────────────────────────────────
# Escolha de direção

def _choose_dir(ghost, tx, ty):
    reverse  = (-ghost.dx, -ghost.dy)
    best_dir = None
    best_dist = float('inf')

    for dx, dy in _DIRS:
        if (dx, dy) == reverse:
            continue
        if _can_move_chasing(ghost.rect.x, ghost.rect.y, dx, dy):
            nx = ghost.rect.centerx + dx * TILE_SIZE
            ny = ghost.rect.centery + dy * TILE_SIZE
            d  = _dist(nx, ny, tx, ty)
            if d < best_dist:
                best_dist = d
                best_dir  = (dx, dy)

    # fallback: se todas as direções não-reversas bloqueadas, aceita a reversa
    if best_dir is None:
        rdx, rdy = reverse
        if _can_move_chasing(ghost.rect.x, ghost.rect.y, rdx, rdy):
            best_dir = (rdx, rdy)

    return best_dir


def _choose_dir_scared(ghost):
    reverse = (-ghost.dx, -ghost.dy)
    opcoes  = [
        (dx, dy) for dx, dy in _DIRS
        if (dx, dy) != reverse and _can_move_chasing(ghost.rect.x, ghost.rect.y, dx, dy)
    ]
    if opcoes:
        return random.choice(opcoes)
    rdx, rdy = reverse
    if _can_move_chasing(ghost.rect.x, ghost.rect.y, rdx, rdy):
        return (rdx, rdy)
    return None


# ──────────────────────────────────────────────
# Movimentação por estado

def _move_in_house(ghost):
    ghost.dx = 0
    if ghost.dy == 0:
        ghost.dy = -1
    if ghost.rect.y <= _HOUSE_TOP_Y:
        ghost.dy = 1
    elif ghost.rect.y >= _HOUSE_BOT_Y:
        ghost.dy = -1
    ghost.rect.y += ghost.dy * SPEED


def _move_exiting(ghost):
    ghost.dy = 0
    # passo 1: centralizar na coluna de saída
    if ghost.rect.x < _EXIT_X:
        ghost.rect.x = min(ghost.rect.x + SPEED, _EXIT_X)
        ghost.dx = 1
        return
    if ghost.rect.x > _EXIT_X:
        ghost.rect.x = max(ghost.rect.x - SPEED, _EXIT_X)
        ghost.dx = -1
        return
    # passo 2: subir até sair pela porta
    ghost.dx, ghost.dy = 0, -1
    ghost.rect.y -= SPEED
    if ghost.rect.y <= _EXIT_Y:
        ghost.rect.x = _EXIT_X
        ghost.rect.y = _EXIT_Y
        ghost.estado = CHASING
        ghost.dx, ghost.dy = -1, 0


def _move_eaten(ghost):
    # Olhinhos viajam de volta à casinha sem verificar colisões
    speed = SPEED * 4

    # passo 1: alinhar à coluna 13
    if ghost.rect.x != _RETURN_X:
        step = min(speed, abs(ghost.rect.x - _RETURN_X))
        if ghost.rect.x < _RETURN_X:
            ghost.rect.x += step
            ghost.dx, ghost.dy = 1, 0
        else:
            ghost.rect.x -= step
            ghost.dx, ghost.dy = -1, 0
        return

    # passo 2: descer até o centro da casinha (linha 14)
    ghost.dx = 0
    if ghost.rect.y != _RETURN_Y:
        step = min(speed, abs(ghost.rect.y - _RETURN_Y))
        if ghost.rect.y < _RETURN_Y:
            ghost.rect.y += step
            ghost.dy = 1
        else:
            ghost.rect.y -= step
            ghost.dy = -1
        return

    # chegou: regenera dentro da casinha com breve espera antes de sair
    ghost.estado = IN_HOUSE
    ghost.dx, ghost.dy = 0, -1
    ghost.liberado_em = pygame.time.get_ticks() + 3000


def _move_chasing(ghost, tx, ty):
    import medo

    assustado = medo.ativo()

    # Fantasmas assustados se movem na metade da velocidade.
    # Para manter o alinhamento com a grade, sempre movemos SPEED=2 pixels,
    # mas pulamos 1 frame a cada 2 quando assustados.
    # (usar speed=1 quebraria o alinhamento ao alternar com speed=2)
    if assustado:
        ghost._scared_skip = not getattr(ghost, '_scared_skip', False)
        if not ghost._scared_skip:
            return
    else:
        ghost._scared_skip = False

    if _tile_aligned(ghost):
        direction = _choose_dir_scared(ghost) if assustado else _choose_dir(ghost, tx, ty)
        if direction:
            ghost.dx, ghost.dy = direction

    ghost.rect.x += ghost.dx * SPEED
    ghost.rect.y += ghost.dy * SPEED

    # teleporte pelo corredor da linha 14
    if (ghost.rect.y - MAZE_OFFSET_Y) // TILE_SIZE == _TELEPORT_ROW:
        if ghost.rect.right <= 0:
            ghost.rect.x = _MAZE_WIDTH
        elif ghost.rect.left >= _MAZE_WIDTH:
            ghost.rect.x = -ghost.rect.width


def _move(ghost, tx, ty):
    if ghost.estado == IN_HOUSE:
        if pygame.time.get_ticks() >= ghost.liberado_em:
            ghost.estado = EXITING
        else:
            _move_in_house(ghost)
    elif ghost.estado == EXITING:
        _move_exiting(ghost)
    elif ghost.estado == EATEN:
        _move_eaten(ghost)
    else:  # CHASING
        _move_chasing(ghost, tx, ty)


# ──────────────────────────────────────────────
# Funções públicas de movimento por fantasma

def mover_blinky(blinky, pacman):
    _move(blinky, pacman.rect.centerx, pacman.rect.centery)


def mover_pinky(pinky, pacman):
    tx = pacman.rect.centerx + pacman.dx * 4 * TILE_SIZE
    ty = pacman.rect.centery + pacman.dy * 4 * TILE_SIZE
    _move(pinky, tx, ty)


def mover_inky(inky, pacman, blinky):
    pivot_x = pacman.rect.centerx + pacman.dx * 2 * TILE_SIZE
    pivot_y = pacman.rect.centery + pacman.dy * 2 * TILE_SIZE
    tx = pivot_x + (pivot_x - blinky.rect.centerx)
    ty = pivot_y + (pivot_y - blinky.rect.centery)
    _move(inky, tx, ty)


def mover_clyde(clyde, pacman):
    dist = _dist(
        clyde.rect.centerx, clyde.rect.centery,
        pacman.rect.centerx, pacman.rect.centery,
    )
    if dist > 8 * TILE_SIZE:
        tx, ty = pacman.rect.centerx, pacman.rect.centery
    else:
        tx, ty = 0, MAZE_OFFSET_Y + 30 * TILE_SIZE
    _move(clyde, tx, ty)
