import math
from jogo import TILE_SIZE, MAZE_OFFSET_Y, SPEED
from jogo import can_move

# Direções possíveis:
# direita, esquerda, baixo, cima
_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


# Calcula distância entre 2 pontos
# Decide qual direção deixa o fantasma mais perto do alvo

def _dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


# Verifica se o fantasma está alinhado exatamente em um tile do mapa
# O fantasma só pode escolher uma nova direção quando chega num cruzamento

def _tile_aligned(ghost):
    return (
        ghost.rect.x % TILE_SIZE == 0 and
        (ghost.rect.y - MAZE_OFFSET_Y) % TILE_SIZE == 0
    )



# Escolhe a melhor direção para chegar perto do alvo (tx, ty)
# 1. testa todas as direções possíveis
# 2. ignora a direção reversa
# 3. verifica se pode mover
# 4. calcula qual movimento aproxima mais do alvo

def _choose_dir(ghost, tx, ty):

    # direção oposta à atual
    reverse = (-ghost.dx, -ghost.dy)

    best_dir = None
    best_dist = float('inf')

    # testa cada direção
    for dx, dy in _DIRS:

        # evita dar meia-volta
        if (dx, dy) == reverse:
            continue

        # verifica se a direção é válida
        if can_move(ghost.rect.x, ghost.rect.y, dx, dy):

            # posição futura se andar 1 tile
            nx = ghost.rect.centerx + dx * TILE_SIZE
            ny = ghost.rect.centery + dy * TILE_SIZE

            # distância até o alvo
            d = _dist(nx, ny, tx, ty)

            # guarda a melhor direção
            if d < best_dist:
                best_dist = d
                best_dir = (dx, dy)

    return best_dir



# Move o fantasma
# 1. Se estiver alinhado no tile: escolhe nova direção
# 2. Move continuamente na direção atual

def _move(ghost, tx, ty):

    # só escolhe nova direção em cruzamentos
    if _tile_aligned(ghost):

        direction = _choose_dir(ghost, tx, ty)

        # atualiza direção
        if direction:
            ghost.dx, ghost.dy = direction

    # movimentação contínua
    ghost.rect.x += ghost.dx * SPEED
    ghost.rect.y += ghost.dy * SPEED



# BLINKY (VERMELHO)
# Persegue diretamente o Pac-Man

def mover_blinky(blinky, pacman):

    # alvo = posição atual do Pac-Man
    tx = pacman.rect.centerx
    ty = pacman.rect.centery

    _move(blinky, tx, ty)



# PINKY (ROSA)
# Tenta emboscar o Pac-Man (Mira 4 tiles à frente da direção atual)

def mover_pinky(pinky, pacman):

    tx = pacman.rect.centerx + pacman.dx * 4 * TILE_SIZE
    ty = pacman.rect.centery + pacman.dy * 4 * TILE_SIZE

    _move(pinky, tx, ty)



# INKY (AZUL)
# Usa:
# - posição do Pac-Man
# - direção do Pac-Man
# - posição do Blinky
# Comportamento imprevisível

def mover_inky(inky, pacman, blinky):

    # ponto 2 tiles à frente do Pac-Man
    pivot_x = pacman.rect.centerx + pacman.dx * 2 * TILE_SIZE
    pivot_y = pacman.rect.centery + pacman.dy * 2 * TILE_SIZE

    # vetor baseado no Blinky
    tx = pivot_x + (pivot_x - blinky.rect.centerx)
    ty = pivot_y + (pivot_y - blinky.rect.centery)

    _move(inky, tx, ty)


# CLYDE (LARANJA)

# LONGE: persegue o Pac-Man
# PERTO: foge para o canto inferior esquerdo

def mover_clyde(clyde, pacman):

    # distância até o Pac-Man
    dist = _dist(
        clyde.rect.centerx,
        clyde.rect.centery,
        pacman.rect.centerx,
        pacman.rect.centery
    )

    # se estiver longe → persegue
    if dist > 8 * TILE_SIZE:

        tx = pacman.rect.centerx
        ty = pacman.rect.centery

    # se estiver perto → foge
    else:

        # canto inferior esquerdo
        tx = 0
        ty = MAZE_OFFSET_Y + 30 * TILE_SIZE

    _move(clyde, tx, ty)
