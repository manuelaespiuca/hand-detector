"""Modo filtro: as duas mãos abrem uma "janela" com efeito (câmera térmica etc.).

Faça um L com cada mão (polegar + indicador). A área entre os quatro dedos
ganha o filtro. Troque o efeito com a tecla E.
"""
import cv2
import numpy as np

from . import config
from .textos import t
from .geometria import Mao
from .ui import bgr


def termico(frame):
    cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cinza = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(cinza)
    return cv2.applyColorMap(cinza, cv2.COLORMAP_JET)


def noturno(frame):
    cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cinza = cv2.equalizeHist(cinza)
    verde = np.zeros_like(frame)
    verde[..., 1] = cinza
    verde[..., 0] = (cinza * 0.25).astype(np.uint8)
    ruido = np.random.randint(0, 28, cinza.shape, dtype=np.uint8)
    verde[..., 1] = cv2.add(verde[..., 1], ruido)
    return verde


def negativo(frame):
    return 255 - frame


def pixel(frame):
    h, w = frame.shape[:2]
    pequeno = cv2.resize(frame, (w // 18, h // 18), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(pequeno, (w, h), interpolation=cv2.INTER_NEAREST)


def contorno(frame):
    cinza = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    bordas = cv2.Canny(cinza, 50, 120)
    bordas = cv2.dilate(bordas, np.ones((2, 2), np.uint8))
    saida = np.full_like(frame, 20)
    saida[bordas > 0] = (255, 255, 255)
    return saida


EFEITOS = [("térmico", termico), ("noturno", noturno), ("negativo", negativo),
           ("pixel", pixel), ("contorno", contorno)]


class ModoFiltro:
    chave = "filtro"

    @property
    def nome(self):
        return t("modo.filtro")

    @property
    def instrucao(self):
        return t("instr.filtro")

    @property
    def atalhos(self):
        return [("e", t("at.trocar_efeito"))]
    cor = config.AMARELO
    max_maos = 2   # quantas mãos o MediaPipe procura neste modo

    def __init__(self):
        self.efeito = 0
        self.poligono = None

    def atualizar(self, maos: list[Mao], t: float):
        if len(maos) < 2:
            self.poligono = None
            return
        # mão da esquerda e da direita na tela
        a, b = sorted(maos[:2], key=lambda m: m.pts[0][0])
        pontos = np.array([a.pts[8], a.pts[4], b.pts[4], b.pts[8]], dtype=np.float32)
        casca = cv2.convexHull(pontos)
        area = cv2.contourArea(casca)
        self.poligono = casca.astype(np.int32) if area > 1500 else None

    def desenhar_frame(self, frame, maos):
        if self.poligono is None:
            return
        h, w = frame.shape[:2]
        mascara = np.zeros((h, w), np.uint8)
        cv2.fillPoly(mascara, [self.poligono], 255, cv2.LINE_AA)
        mascara = cv2.GaussianBlur(mascara, (0, 0), 1.5)

        x, y, bw, bh = cv2.boundingRect(self.poligono)
        x0, y0 = max(x - 4, 0), max(y - 4, 0)
        x1, y1 = min(x + bw + 4, w), min(y + bh + 4, h)
        if x1 - x0 < 4 or y1 - y0 < 4:
            return
        recorte = frame[y0:y1, x0:x1]
        efeito = EFEITOS[self.efeito][1](recorte)
        a = (mascara[y0:y1, x0:x1].astype(np.float32) / 255.0)[..., None]
        frame[y0:y1, x0:x1] = (recorte * (1 - a) + efeito * a).astype(np.uint8)
        # contorno fininho em azul apagado
        cv2.polylines(frame, [self.poligono], True, bgr(config.AZUL_APAGADO), 2, cv2.LINE_AA)

    def cores_pontas(self, m: Mao):
        return [config.AZUL_APAGADO if up else None for up in m.dedos]

    def desenhar_ui(self, c, maos):
        pass   # sem texto: o próprio filtro já mostra o efeito

    def dica(self, maos):
        if len(maos) < 2:
            return "faça um L com as duas mãos"
        return f"efeito: {EFEITOS[self.efeito][0]} · e troca"

    def tecla(self, k: int, avisos) -> bool:
        if k == ord("e"):
            self.efeito = (self.efeito + 1) % len(EFEITOS)
            avisos.mostrar(t("f." + EFEITOS[self.efeito][0]))
            return True
        return False
