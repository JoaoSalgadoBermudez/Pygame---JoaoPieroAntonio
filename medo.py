import pygame

_DURACAO = 8000  # ms que os fantasmas ficam assustados após comer power pellet

_ativo  = False
_inicio = 0


def ativar():
    global _ativo, _inicio
    _ativo  = True
    _inicio = pygame.time.get_ticks()


def ativo():
    global _ativo
    if _ativo and pygame.time.get_ticks() - _inicio > _DURACAO:
        _ativo = False
    return _ativo


def piscando():
    if not _ativo:
        return False
    restante = _DURACAO - (pygame.time.get_ticks() - _inicio)
    return restante < 2000  # pisca nos últimos 2 segundos


def cor_fantasma():
    if piscando() and (pygame.time.get_ticks() // 250) % 2 == 0:
        return (255, 255, 255)   # branco (piscando — aviso que o efeito está acabando)
    return (0, 50, 255)          # azul (assustado)
