"""Modo jokenpô — pedra, papel e tesoura contra o computador.

Mostre a mão: começa a contagem "jo · ken · pô!". No "pô!", faça sua jogada.
  mão fechada ......... pedra
  mão aberta .......... papel
  indicador + médio ... tesoura
"""
import random
import time
from collections import Counter, deque

from . import config
from .textos import t
from .geometria import Mao
from .gestos import classificar

JOGADAS = ["pedra", "papel", "tesoura"]
GANHA_DE = {"pedra": "tesoura", "papel": "pedra", "tesoura": "papel"}
TEMPO_SILABA = 0.65
TEMPO_RESULTADO = 2.8


def jogada(m: Mao) -> str | None:
    g = classificar(m)
    if g == "punho":
        return "pedra"
    if g in ("oi", "quatro"):
        return "papel"
    if g == "paz":
        return "tesoura"
    return None


class ModoJokenpo:
    chave = "jokenpo"

    @property
    def nome(self):
        return t("modo.jokenpo")

    @property
    def instrucao(self):
        return t("instr.jokenpo")

    @property
    def atalhos(self):
        return [("espaço", t("at.nova_rodada")), ("r", t("at.zerar_placar"))]
    cor = config.AZUL_APAGADO
    max_maos = 1   # quantas mãos o MediaPipe procura neste modo

    def __init__(self):
        self.placar = [0, 0]           # você, computador
        self.estado = "espera"
        self.desde = time.monotonic()
        self.historico = deque(maxlen=10)
        self.sua = None
        self.minha = None
        self.resultado = ""
        self.atual = None              # jogada que está aparecendo agora

    def _ir(self, estado):
        self.estado = estado
        self.desde = time.monotonic()

    def atualizar(self, maos: list[Mao], t: float):
        agora = time.monotonic()
        decorrido = agora - self.desde
        m = maos[0] if maos else None
        self.atual = jogada(m) if m else None

        if self.estado == "espera":
            # mão parada na tela por um instante: começa a rodada
            if m is None:
                self.desde = agora
            elif decorrido > 0.8:
                self.historico.clear()
                self._ir("contagem")

        elif self.estado == "contagem":
            # guarda o que a mão mostra perto do "pô!"
            if decorrido > TEMPO_SILABA * 2.5:
                self.historico.append(self.atual)
            if decorrido > TEMPO_SILABA * 3 + 0.35:
                self._decidir()
                self._ir("resultado")

        elif self.estado == "resultado":
            if decorrido > TEMPO_RESULTADO:
                self._ir("espera")

    def _decidir(self):
        validas = [j for j in self.historico if j]
        self.minha = random.choice(JOGADAS)
        if not validas:
            self.sua = None
            self.resultado = "j.nao_vi"
            return
        self.sua = Counter(validas).most_common(1)[0][0]
        if self.sua == self.minha:
            self.resultado = "j.empate"
        elif GANHA_DE[self.sua] == self.minha:
            self.resultado = "j.ganhou"
            self.placar[0] += 1
        else:
            self.resultado = "j.perdeu"
            self.placar[1] += 1

    def cores_pontas(self, m: Mao):
        return [config.AZUL_APAGADO if up else None for up in m.dedos]

    def desenhar_frame(self, frame, maos):
        pass

    def desenhar_ui(self, c, maos: list[Mao]):
        azul = config.AZUL_APAGADO
        cx = c.w / 2
        decorrido = time.monotonic() - self.desde

        # placar discreto no topo
        c.texto((cx, 35), t("j.placar", a=self.placar[0], b=self.placar[1]),
                tamanho=13, alfa=200, ancora="mm")

        # contagem e resultado ficam numa faixa fixa no alto, longe das mãos
        if self.estado == "contagem":
            silabas = t("j.silabas")
            k = min(int(decorrido / TEMPO_SILABA), 2)
            fase = (decorrido - k * TEMPO_SILABA) / TEMPO_SILABA
            alfa = int(255 * max(0.35, 1 - fase * 0.6)) if k < 2 else 255
            c.flutuante(cx, 150, silabas[k], azul, tamanho=64, alfa=alfa)

        elif self.estado == "resultado":
            c.flutuante(cx, 140, t(self.resultado), azul, tamanho=44)
            sua = t("j." + self.sua) if self.sua else "?"
            c.texto((cx, 172), t("j.jogadas", sua=sua, minha=t("j." + self.minha)),
                    tamanho=14, alfa=210, ancora="mm")
            return

        # fora do resultado: mostra o que a mão está fazendo
        if maos and self.atual:
            x, y = maos[0].topo
            c.flutuante(x, y - 22, t("j." + self.atual), azul, tamanho=30, alfa=200)

    def dica(self, maos):
        return self.instrucao

    def tecla(self, k: int, avisos) -> bool:
        if k == 32:
            self.historico.clear()
            self._ir("contagem")
            return True
        if k == ord("r"):
            self.placar = [0, 0]
            return True
        return False
