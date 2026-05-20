import pygame   # biblioteca principal do jogo
import sys      # usado para encerrar o programa de forma limpa

# -----------------------------------------------------------------------------
# INICIALIZAÇÃO
# Tudo antes do game loop: preparar pygame, janela e variáveis.
# -----------------------------------------------------------------------------

pygame.init()   # inicia todos os módulos do pygame (obrigatório!)

# Tamanho da janela
# O labirinto clássico do Pac-Man tem 28 colunas × 31 linhas de tiles.
# Usando tiles de 20×20 px → 560 px de largura.
# Deixamos 80 px extras na altura para o HUD (score, vidas).
WIDTH  = 560    # largura da janela em pixels
HEIGHT = 680    # altura da janela em pixels (600 labirinto + 80 HUD)

# Cores (valores RGB: vermelho, verde, azul — cada um de 0 a 255)
BLACK  = (0,   0,   0)    # fundo do jogo
WHITE  = (255, 255, 255)  # texto genérico
YELLOW = (255, 255,  0)   # cor do Pac-Man
BLUE   = ( 33,  33, 255)  # cor das paredes do labirinto

# Cria a janela do jogo
# set_mode recebe uma TUPLA (largura, altura)
window = pygame.display.set_mode((WIDTH, HEIGHT))

# Define o título que aparece na barra da janela
pygame.display.set_caption("Pac-Man")

# Variável de controle do game loop:
# enquanto 'rodando' for True, o jogo continua.
rodando = True

# -----------------------------------------------------------------------------
# GAME LOOP (loop principal)
# Repetido enquanto o jogo estiver ativo.
# Cada iteração = 1 frame.
# -----------------------------------------------------------------------------

while rodando:

    # -------------------------------------------------------------------------
    # 1. TRATAR EVENTOS
    # pygame.event.get() retorna todos os eventos desde o último frame.
    # Eventos: clique/movimento de mouse, teclas, botão de fechar janela, etc.
    # -------------------------------------------------------------------------
    for event in pygame.event.get():

        # Usuário clicou no X da janela → encerra o jogo
        if event.type == pygame.QUIT:
            rodando = False

        # Usuário SOLTOU qualquer tecla → encerra o jogo
        # (Exercício 1: fechar o jogo ao apertar qualquer tecla)
        # KEYUP: evento disparado no momento em que a tecla é solta
        if event.type == pygame.KEYUP:
            rodando = False

    # -------------------------------------------------------------------------
    # 2. VERIFICAR CONSEQUÊNCIAS
    # (nesta etapa não há lógica de jogo ainda — virá nas próximas etapas)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 3. ATUALIZAR ESTADO DO JOGO
    # (nesta etapa não há objetos para atualizar ainda)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # 4. GERAR SAÍDAS (desenhar o frame)
    # Tudo que é desenhado fica em memória até o display.update() ser chamado.
    # A ordem dos desenhos importa: o último desenhado fica na frente.
    # -------------------------------------------------------------------------

    # Preenche o fundo com preto antes de desenhar qualquer coisa.
    # Isso apaga o frame anterior (sem isso os objetos deixariam rastro).
    window.fill(BLACK)

    # Área do HUD: faixa amarela fina separando labirinto do placar.
    # draw.rect(superfície, cor, (x, y, largura, altura))
    pygame.draw.rect(window, YELLOW, (0, 600, WIDTH, 4))

    # Atualiza a janela: mostra na tela tudo que foi desenhado acima.
    # Sem essa chamada o jogador nunca vê nada.
    pygame.display.update()

# -----------------------------------------------------------------------------
# FINALIZAÇÃO
# Executado uma única vez depois que o game loop termina.
# -----------------------------------------------------------------------------

pygame.quit()   # fecha todos os recursos do pygame
sys.exit()      # encerra o processo Python de forma limpa