"""Modo gestos: reconhece o gesto de cada mão e mostra o nome flutuando."""
from collections import Counter, deque

from . import config, textos
from .textos import t
from .geometria import Mao, dist

def classificar(m: Mao) -> str:
    p, i, me, a, mi = m.dedos
    contagem = sum(m.dedos)

    # ok: polegar e indicador formando um círculo, os outros levantados
    if m.d(4, 8) < 0.35 and me and a and mi:
        return "ok"

    padrao = (p, i, me, a, mi)
    if padrao == (False, False, False, False, False):
        return "punho"
    if padrao == (True, False, False, False, False):
        # polegar pra cima ou pra baixo? (y menor = mais alto na tela)
        if m.pts[4][1] < m.pts[2][1] - 0.3 * m.escala:
            return "joinha"
        if m.pts[4][1] > m.pts[2][1] + 0.3 * m.escala:
            return "não curti"
        return "punho"
    nomes = {
        (True, True, True, True, True): "oi",
        (False, True, True, False, False): "paz",
        (False, True, False, False, False): "apontando",
        (False, True, False, False, True): "rock",
        (True, True, False, False, True): "te amo",
        (True, False, False, False, True): "hang loose",
        (True, True, False, False, False): "L",
        (False, True, True, True, False): "três",
        (True, True, True, False, False): "três",
        (False, True, True, True, True): "quatro",
        (False, False, False, False, True): "mindinho",
    }
    return nomes.get(padrao, f"{contagem} dedo" + ("s" if contagem != 1 else ""))


def coracao(m1: Mao, m2: Mao) -> bool:
    """Coração com as duas mãos: pontas dos polegares e dos indicadores se tocando."""
    escala = (m1.escala + m2.escala) / 2
    return (dist(m1.pts[4], m2.pts[4]) < 0.55 * escala
            and dist(m1.pts[8], m2.pts[8]) < 0.55 * escala)


class ModoGestos:
    chave = "gestos"

    @property
    def nome(self):
        return t("modo.gestos")

    @property
    def instrucao(self):
        return t("instr.gestos")

    @property
    def atalhos(self):
        return []
    cor = config.MENTA
    max_maos = 2   # quantas mãos o MediaPipe procura neste modo

    def __init__(self):
        self.historico: dict[str, deque] = {}
        self.estavel: dict[str, str] = {}
        self.tem_coracao = False
        self._coracao_hist = deque(maxlen=6)

    def atualizar(self, maos: list[Mao], t: float):
        for m in maos:
            h = self.historico.setdefault(m.id, deque(maxlen=7))
            h.append(classificar(m))
            self.estavel[m.id] = Counter(h).most_common(1)[0][0]
        ids = {m.id for m in maos}
        for k in list(self.historico):
            if k not in ids:
                del self.historico[k]
                self.estavel.pop(k, None)

        self._coracao_hist.append(len(maos) == 2 and coracao(maos[0], maos[1]))
        self.tem_coracao = sum(self._coracao_hist) >= 4

    def cores_pontas(self, m: Mao):
        return [config.AZUL_APAGADO if up else None for up in m.dedos]

    def desenhar_frame(self, frame, maos):
        pass

    def desenhar_ui(self, c, maos: list[Mao]):
        if self.tem_coracao:
            m1, m2 = maos
            x = (m1.pts[8][0] + m2.pts[8][0]) / 2
            y = min(m1.pts[:, 1].min(), m2.pts[:, 1].min()) - 26
            c.flutuante(x, y, t("g.coração"), config.AZUL_APAGADO, tamanho=34)
            return

        for m in maos:
            gesto = self.estavel.get(m.id, "")
            if not gesto:
                continue
            x, y = m.topo
            c.flutuante(x, y - 22, textos.gesto(gesto), config.AZUL_APAGADO, tamanho=32)

    def dica(self, maos):
        return "tente fazer um coração com as duas mãos"

    def tecla(self, k: int, avisos) -> bool:
        return False
