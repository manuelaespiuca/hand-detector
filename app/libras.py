"""Modo libras: reconhece letras do alfabeto manual e monta palavras.

Letras paradas (segure até o círculo completar):
    A B C D E I L O R S U V W Y
Letras com movimento (faça o movimento, não precisa segurar):
    H  indicador e médio deitados (na horizontal), mexendo a mão
    J  mindinho levantado (como o I) desenhando um J para baixo
    K  indicador, médio e polegar levantados, subindo a mão
    X  indicador em gancho, balançando de um lado para o outro
    Z  só o indicador, desenhando um Z no ar

O reconhecimento é feito por regras (sem rede treinada), então é uma
aproximação. Funciona melhor com a palma virada para a câmera e boa luz.
"""
import time
from collections import Counter, deque

import cv2
import numpy as np

from . import config
from .textos import t
from .geometria import Mao
from .ui import bgr

JANELA_MOVIMENTO = 1.2    # segundos de rastro analisados
ESPERA_DINAMICA = 1.2     # intervalo mínimo entre duas letras com movimento


def deitado(m: Mao) -> bool:
    """Indicador apontando mais para o lado do que para cima/baixo."""
    dx = m.pts[8][0] - m.pts[5][0]
    dy = m.pts[8][1] - m.pts[5][1]
    return abs(dx) > abs(dy) * 1.3


def gancho(m: Mao) -> bool:
    """Indicador dobrado em gancho e os outros dedos fechados (letra X)."""
    return (0.45 < m.curvatura(1) < 0.85 and m.d(8, 0) > 1.25
            and all(m.d(t, 0) < 1.2 for t in (12, 16, 20)))


def classificar(m: Mao) -> str | None:
    p, i, me, a, mi = m.dedos
    curv = [m.curvatura(n) for n in range(1, 5)]       # indicador..mindinho
    pontas = [8, 12, 16, 20]

    media = sum(m.d(t, 0) for t in pontas) / 4   # pontas longe do pulso = dedos não fechados na palma

    # O: todas as pontas encostando no polegar, dedos curvados
    if media > 1.15 and all(m.d(4, t) < 0.5 for t in pontas[:3]) and m.d(4, 20) < 0.7 and max(curv) < 0.92:
        return "O"

    # C: dedos curvados em arco, polegar afastado das pontas
    if (not any([i, me, a, mi]) or max(curv) < 0.9) and all(0.45 < c < 0.9 for c in curv):
        if 0.45 < m.d(4, 8) < 1.3 and m.d(8, 0) > 1.1 and m.d(4, 5) > 0.5:
            return "C"

    padrao = (i, me, a, mi)

    if padrao == (False, False, False, False):
        if gancho(m):
            return None             # é o X (letra com movimento)
        if media > 1.2 and not p:
            return "E"              # dedos dobrados, sem fechar na palma
        if m.d(4, 5) < m.d(4, 9):   # polegar do lado do indicador
            return "A"
        return "S"                  # polegar atravessado na frente dos dedos

    if padrao == (True, True, True, True):
        if not p and m.d(8, 20) < 1.05:
            return "B"
        return None

    if padrao == (True, False, False, False):
        if p:
            return "L"
        if m.d(4, 12) < 0.55:
            return "D"
        return None

    if padrao == (False, False, False, True):
        return "Y" if p else "I"

    if padrao == (True, True, False, False):
        if deitado(m) or p:
            return None             # H (deitado) ou K (com polegar): letras com movimento
        # R: indicador e médio cruzados (a ordem das pontas inverte a das bases)
        bases = m.pts[5][0] - m.pts[9][0]
        topos = m.pts[8][0] - m.pts[12][0]
        if bases * topos < 0:
            return "R"
        return "U" if m.d(8, 12) < 0.42 else "V"

    if padrao == (True, True, True, False):
        return "W"

    return None


def forma_movimento(m: Mao) -> tuple[str, int] | None:
    """Formato de mão que pode virar letra com movimento + ponto a seguir."""
    p, i, me, a, mi = m.dedos
    padrao = (i, me, a, mi)
    if padrao == (False, False, False, True) and not p:
        return "J", 20
    if padrao == (True, False, False, False) and not p:
        return "Z", 8   # parado vira D; desenhando no ar vira Z
    if padrao == (True, True, False, False) and deitado(m):
        return "H", 8
    if padrao == (True, True, False, False) and p and not deitado(m):
        return "K", 8
    if padrao == (False, False, False, False) and gancho(m):
        return "X", 8
    return None


def tracos(valores):
    """Divide o movimento em traços no mesmo sentido; devolve o tamanho de cada um."""
    sentido, acumulado, lista = 0, 0.0, []
    for v in valores:
        if v == 0:
            continue
        s = 1 if v > 0 else -1
        if s == sentido or sentido == 0:
            acumulado += abs(v)
            sentido = s
        else:
            lista.append(acumulado)
            sentido, acumulado = s, abs(v)
    lista.append(acumulado)
    return lista


def tracos_grandes(valores, minimo):
    """Junta tremidas pequenas e conta só os traços de verdade."""
    return [t for t in tracos(valores) if t >= minimo]


def letra_movimento(rastro) -> str | None:
    """rastro: lista de (t, x, y, escala, forma). Decide se houve J, Z, H, K ou X."""
    if len(rastro) < 8:
        return None
    forma = rastro[-1][4]
    trecho = [r for r in rastro if r[4] == forma]
    if len(trecho) < 8 or len(trecho) < len(rastro) * 0.7:
        return None
    escala = float(np.mean([r[3] for r in trecho]))
    xs = np.array([r[1] for r in trecho]) / escala
    ys = np.array([r[2] for r in trecho]) / escala
    dx, dy = np.diff(xs), np.diff(ys)
    caminho = float(np.hypot(dx, dy).sum())
    total_x, total_y = xs[-1] - xs[0], ys[-1] - ys[0]   # y cresce para baixo

    if forma == "J" and caminho > 0.9 and total_y > 0.3 and abs(total_x) > 0.2:
        return "J"
    grandes = tracos_grandes(dx, 0.25)
    if forma == "Z" and len(grandes) >= 3 and grandes[-1] > 0.6 and total_y > 0.25:
        return "Z"
    if forma == "H" and caminho > 0.7:
        return "H"
    if forma == "K" and total_y < -0.45:
        return "K"
    if forma == "X" and caminho > 0.6 and len(tracos_grandes(dx, 0.12)) >= 3:
        return "X"
    return None


class ModoLibras:
    chave = "libras"

    @property
    def nome(self):
        return t("modo.libras")

    @property
    def instrucao(self):
        return t("instr.libras")

    @property
    def atalhos(self):
        return [("espaço", t("at.separar_palavra")), ("backspace", t("at.apagar")), ("l", t("at.limpar"))]
    cor = config.AZUL
    max_maos = 1   # quantas mãos o MediaPipe procura neste modo

    def __init__(self):
        self.historico: dict[str, deque] = {}
        self.letra: dict[str, str | None] = {}
        self.texto = ""
        # controle de "segurar a letra"
        self._atual = None
        self._desde = 0.0
        self._ja_escreveu = False
        self._pulso = 0.0
        # letras com movimento
        self.rastro: deque = deque()
        self._dinamica = (None, 0.0)     # (letra, quando)
        self._parada = True

    @property
    def progresso(self) -> float:
        if not self._atual or self._ja_escreveu:
            return 0.0
        return (time.monotonic() - self._desde) / config.TEMPO_LETRA

    def _escrever(self, letra, agora):
        self.texto = (self.texto + letra)[-28:]
        self._pulso = agora

    def atualizar(self, maos: list[Mao], t: float):
        agora = time.monotonic()
        for m in maos:
            h = self.historico.setdefault(m.id, deque(maxlen=8))
            h.append(classificar(m))
            letra, votos = Counter(h).most_common(1)[0]
            self.letra[m.id] = letra if votos >= 5 else None
        ids = {m.id for m in maos}
        for k in list(self.historico):
            if k not in ids:
                del self.historico[k]
                self.letra.pop(k, None)

        # ---- letras com movimento (segue a primeira mão)
        principal_mao = maos[0] if maos else None
        forma = forma_movimento(principal_mao) if principal_mao else None
        if forma:
            nome, ponto = forma
            x, y = principal_mao.pts[ponto]
            self.rastro.append((agora, float(x), float(y), principal_mao.escala, nome))
        else:
            self.rastro.clear()
        while self.rastro and agora - self.rastro[0][0] > JANELA_MOVIMENTO:
            self.rastro.popleft()

        # mão parada? (letra parada só conta sem movimento)
        self._parada = True
        if principal_mao is not None:
            recente = [r for r in self.rastro if agora - r[0] < 0.3]
            if len(recente) >= 3:
                d = np.hypot(recente[-1][1] - recente[0][1], recente[-1][2] - recente[0][2])
                self._parada = d / principal_mao.escala < 0.25

        if agora - self._dinamica[1] > ESPERA_DINAMICA:
            dinamica = letra_movimento(list(self.rastro))
            if dinamica:
                self._dinamica = (dinamica, agora)
                self._escrever(dinamica, agora)
                self.rastro.clear()
                self._atual, self._ja_escreveu = None, False
                return

        # ---- letras paradas: segurar por TEMPO_LETRA
        principal = next((self.letra[m.id] for m in maos if self.letra.get(m.id)), None)
        if principal != self._atual or not self._parada:
            self._atual, self._desde, self._ja_escreveu = principal, agora, False
        elif principal and not self._ja_escreveu and agora - self._desde >= config.TEMPO_LETRA:
            self._escrever(principal, agora)
            self._ja_escreveu = True

    def cores_pontas(self, m: Mao):
        return [config.AZUL_APAGADO if up else None for up in m.dedos]

    def desenhar_frame(self, frame, maos):
        # rastro suave do movimento (ajuda a ver o J, o Z...)
        if len(self.rastro) < 2:
            return
        pts = np.array([[r[1], r[2]] for r in self.rastro], np.int32)
        camada = frame.copy()
        cv2.polylines(camada, [pts], False, bgr(config.AZUL_APAGADO), 3, cv2.LINE_AA)
        cv2.addWeighted(camada, 0.55, frame, 0.45, 0, dst=frame)

    def desenhar_ui(self, c, maos: list[Mao]):
        agora = time.monotonic()
        din, quando = self._dinamica
        mostrar_din = din and agora - quando < 0.9

        for n, m in enumerate(maos):
            x, y = m.topo
            cy = y - 52
            if n == 0 and mostrar_din:
                pulso = max(0.0, 1 - (agora - quando) / 0.4)
                c.arco(x, cy, 34 + 6 * pulso, 1.0, cor=config.MENTA)
                c.flutuante(x, cy + 17, din, config.AZUL_APAGADO, tamanho=46, peso="negrito")
                continue
            if n == 0 and not self._parada:
                continue            # mão em movimento: o rastro já mostra o que está acontecendo
            letra = self.letra.get(m.id)
            if not letra:
                c.flutuante(x, y - 20, "?", config.AZUL_APAGADO, tamanho=26, alfa=140)
                continue
            escreveu = self._ja_escreveu and letra == self._atual
            pulso = max(0.0, 1 - (agora - self._pulso) / 0.4) if escreveu else 0
            cor = config.MENTA if escreveu else config.AZUL
            c.arco(x, cy, 34 + 6 * pulso, 1.0 if escreveu else self.progresso if letra == self._atual else 0, cor=cor)
            c.flutuante(x, cy + 17, letra, config.AZUL_APAGADO, tamanho=46, peso="negrito")

        # texto montado, embaixo no centro
        visivel = self.texto.replace(" ", "·") if self.texto else ""
        cursor = "|" if int(agora * 2) % 2 == 0 else " "
        partes = [(visivel + cursor, config.BRANCO, 255)] if visivel else [("...", config.BRANCO, 190)]
        c.pilula(c.w / 2, c.h - 74, partes, tamanho=22, ancora="centro")

    def dica(self, maos):
        return "A B C D E H I J K L O R S U V W X Y Z"

    def tecla(self, k: int, avisos) -> bool:
        if k == 32:
            self.texto = (self.texto + " ")[-28:]
            return True
        if k in (8, 127):
            self.texto = self.texto[:-1]
            return True
        if k == ord("l"):
            self.texto = ""
            avisos.mostrar(t("l.texto_limpo"))
            return True
        return False
