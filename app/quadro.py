"""Modo desenhar no ar.

  só o indicador levantado ......... desenha
  indicador + médio ................ mover sem desenhar
  mão fechada ...................... borracha
  passar o dedo numa bolinha de cor  troca a cor
"""
import time
from datetime import datetime

import cv2
import numpy as np

from . import config
from .textos import t
from .geometria import Mao, dist
from .ui import bgr

RAIO_COR = 13
ESPACO_COR = 40
TEMPO_ESCOLHA = 0.45


class ModoQuadro:
    chave = "desenhar"

    @property
    def nome(self):
        return t("modo.desenhar")

    @property
    def instrucao(self):
        return t("instr.desenhar")

    @property
    def atalhos(self):
        return [("c", t("at.trocar_cor")), ("+/-", t("at.espessura")), ("l", t("at.limpar")), ("s", t("at.salvar"))]
    cor = config.ROSA
    max_maos = 1   # quantas mãos o MediaPipe procura neste modo

    def __init__(self, w=config.LARGURA, h=config.ALTURA):
        self.w, self.h = w, h
        self.tinta = np.zeros((h, w, 3), np.uint8)
        self.mascara = np.zeros((h, w), np.uint8)
        self.cor_idx = 0
        self.espessura = 6
        self.estado: dict[str, dict] = {}   # por mão: último ponto, ação...
        self._hover = None                  # (indice_cor, desde)
        self.ultimo_frame = None

    # ---------------------------------------------------------------- paleta
    def posicoes_cores(self):
        n = len(config.CORES_QUADRO)
        x0 = self.w / 2 - (n - 1) * ESPACO_COR / 2
        return [(x0 + k * ESPACO_COR, 40) for k in range(n)]

    @property
    def cor(self):
        return config.CORES_QUADRO[self.cor_idx]

    def _ajustar_tamanho(self, frame):
        h, w = frame.shape[:2]
        if (w, h) != (self.w, self.h):
            self.w, self.h = w, h
            self.tinta = np.zeros((h, w, 3), np.uint8)
            self.mascara = np.zeros((h, w), np.uint8)

    # ---------------------------------------------------------------- lógica
    def atualizar(self, maos: list[Mao], t: float):
        agora = time.monotonic()
        vistos = set()
        hover_agora = None

        for m in maos:
            vistos.add(m.id)
            st = self.estado.setdefault(m.id, {"ultimo": None, "suave": None, "acao": "", "conta": {}})
            p, i, me, a, mi = m.dedos

            if not any([i, me, a, mi]):
                acao = "apagar"
            elif i and not me and not a and not mi:
                acao = "desenhar"
            elif i and me and not a and not mi:
                acao = "mover"
            else:
                acao = "parado"

            # exige 3 frames seguidos para trocar de ação (evita riscos acidentais)
            conta = st["conta"]
            conta[acao] = conta.get(acao, 0) + 1
            for k in list(conta):
                if k != acao:
                    conta[k] = 0
            if acao != st["acao"] and conta[acao] >= 3:
                st["acao"] = acao
                st["ultimo"] = None
            acao = st["acao"]

            ponta = m.pts[8]
            if st["suave"] is None or dist(st["suave"], ponta) > 120:
                st["suave"] = ponta.copy()
                st["ultimo"] = None
            else:
                st["suave"] = st["suave"] * 0.45 + ponta * 0.55
            x, y = st["suave"]

            # escolher cor passando o dedo na paleta
            if acao in ("desenhar", "mover"):
                for k, (cx, cy) in enumerate(self.posicoes_cores()):
                    if dist((x, y), (cx, cy)) < RAIO_COR + 12:
                        hover_agora = k
            na_paleta = hover_agora is not None and y < 80

            if acao == "desenhar" and not na_paleta:
                ponto = (int(x), int(y))
                if st["ultimo"] is not None:
                    cv2.line(self.tinta, st["ultimo"], ponto, bgr(self.cor), self.espessura, cv2.LINE_AA)
                    cv2.line(self.mascara, st["ultimo"], ponto, 255, self.espessura, cv2.LINE_AA)
                st["ultimo"] = ponto
            elif acao == "apagar":
                cx, cy = m.centro_palma
                r = int(m.escala * 0.75)
                cv2.circle(self.tinta, (int(cx), int(cy)), r, (0, 0, 0), -1)
                cv2.circle(self.mascara, (int(cx), int(cy)), r, 0, -1)
                st["ultimo"] = None
            else:
                st["ultimo"] = None

        for k in list(self.estado):
            if k not in vistos:
                del self.estado[k]

        if hover_agora is None:
            self._hover = None
        elif self._hover is None or self._hover[0] != hover_agora:
            self._hover = (hover_agora, agora)
        elif agora - self._hover[1] >= TEMPO_ESCOLHA:
            self.cor_idx = hover_agora

    # ---------------------------------------------------------------- desenho
    def desenhar_frame(self, frame, maos):
        self._ajustar_tamanho(frame)
        if self.mascara.any():
            a = (self.mascara.astype(np.float32) / 255.0)[..., None]
            frame[:] = (frame * (1 - a) + self.tinta * a).astype(np.uint8)
        self.ultimo_frame = frame.copy()

    def cores_pontas(self, m: Mao):
        return [config.AZUL_APAGADO if up else None for up in m.dedos]

    def desenhar_ui(self, c, maos: list[Mao]):
        agora = time.monotonic()
        # paleta
        for k, (x, y) in enumerate(self.posicoes_cores()):
            cor = config.CORES_QUADRO[k]
            if k == self.cor_idx:
                c.anel(x, y, RAIO_COR + 5, config.BRANCO, alfa=230, largura=2)
            c.bolinha(x, y, RAIO_COR, cor, alfa=240)
            if self._hover and self._hover[0] == k and k != self.cor_idx:
                c.arco(x, y, RAIO_COR + 6, (agora - self._hover[1]) / TEMPO_ESCOLHA, largura=2)

        # cursores
        for m in maos:
            st = self.estado.get(m.id)
            if not st or st["suave"] is None:
                continue
            x, y = st["suave"]
            acao = st["acao"]
            if acao == "desenhar":
                c.bolinha(x, y, self.espessura / 2 + 2, self.cor, alfa=255, contorno=(255, 255, 255, 230))
            elif acao == "mover":
                c.anel(x, y, self.espessura / 2 + 9, self.cor, alfa=220, largura=2)
            elif acao == "apagar":
                cx, cy = m.centro_palma
                c.anel(cx, cy, m.escala * 0.75, config.BRANCO, alfa=170, largura=2)
                c.flutuante(cx, cy - m.escala * 0.75 - 10, t("d.borracha"), config.AZUL_APAGADO, tamanho=16, alfa=230)

    def dica(self, maos):
        return f"1 dedo desenha · 2 dedos movem · punho apaga · pincel {self.espessura}"

    # ---------------------------------------------------------------- teclas
    def tecla(self, k: int, avisos) -> bool:
        if k == ord("c"):
            self.cor_idx = (self.cor_idx + 1) % len(config.CORES_QUADRO)
            return True
        if k in (ord("+"), ord("=")):
            self.espessura = min(self.espessura + 2, 30)
            return True
        if k in (ord("-"), ord("_")):
            self.espessura = max(self.espessura - 2, 2)
            return True
        if k == ord("l"):
            self.tinta[:] = 0
            self.mascara[:] = 0
            return True
        if k == ord("s"):
            config.PASTA_DESENHOS.mkdir(parents=True, exist_ok=True)
            nome = datetime.now().strftime("desenho_%Y%m%d_%H%M%S")
            # foto com o desenho por cima + só o desenho num fundo branco
            if self.ultimo_frame is not None:
                cv2.imwrite(str(config.PASTA_DESENHOS / f"{nome}_foto.png"), self.ultimo_frame)
            a = (self.mascara.astype(np.float32) / 255.0)[..., None]
            branco = np.full_like(self.tinta, 255)
            so_desenho = (branco * (1 - a) + self.tinta * a).astype(np.uint8)
            cv2.imwrite(str(config.PASTA_DESENHOS / f"{nome}.png"), so_desenho)
            avisos.mostrar(t("d.salvo", nome=nome), 2.5)
            return True
        return False
