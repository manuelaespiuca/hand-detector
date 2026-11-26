"""Funções de geometria da mão (21 pontos do MediaPipe).

Índices:  0 pulso | polegar 1-4 | indicador 5-8 | médio 9-12 | anelar 13-16 | mindinho 17-20
"""
from dataclasses import dataclass, field

import numpy as np

PONTAS = [4, 8, 12, 16, 20]
PIPS = [3, 6, 10, 14, 18]
MCPS = [2, 5, 9, 13, 17]

CONEXOES = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


def dist(a, b) -> float:
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


@dataclass
class Mao:
    pts: np.ndarray            # (21, 2) em pixels
    lado: str = "?"            # "Left" / "Right" segundo o MediaPipe
    id: str = ""               # identificador estável entre frames
    _cache: dict = field(default_factory=dict, repr=False)

    @property
    def escala(self) -> float:
        """Tamanho da palma (pulso -> base do dedo médio). Usado para normalizar."""
        if "escala" not in self._cache:
            self._cache["escala"] = max(dist(self.pts[0], self.pts[9]), 1.0)
        return self._cache["escala"]

    @property
    def dedos(self) -> list[bool]:
        """[polegar, indicador, médio, anelar, mindinho] -> levantado?"""
        if "dedos" not in self._cache:
            self._cache["dedos"] = dedos_levantados(self.pts)
        return self._cache["dedos"]

    def curvatura(self, dedo: int) -> float:
        """1.0 = dedo reto, ~0.4 = dedo bem dobrado. dedo: 1..4"""
        base = MCPS[dedo]
        p = self.pts
        caminho = dist(p[base], p[base + 1]) + dist(p[base + 1], p[base + 2]) + dist(p[base + 2], p[base + 3])
        return dist(p[base], p[base + 3]) / max(caminho, 1e-6)

    def d(self, a: int, b: int) -> float:
        """Distância entre dois pontos, normalizada pelo tamanho da palma."""
        return dist(self.pts[a], self.pts[b]) / self.escala

    @property
    def topo(self) -> tuple[float, float]:
        """Ponto logo acima da mão (para colocar rótulos)."""
        xs, ys = self.pts[:, 0], self.pts[:, 1]
        return float((xs.min() + xs.max()) / 2), float(ys.min())

    @property
    def centro_palma(self) -> tuple[float, float]:
        c = self.pts[[0, 5, 9, 13, 17]].mean(axis=0)
        return float(c[0]), float(c[1])


def dedos_levantados(p: np.ndarray) -> list[bool]:
    escala = max(dist(p[0], p[9]), 1.0)

    # polegar: ponta longe da base do indicador e mais longe do mindinho que a junta
    polegar = (
        dist(p[4], p[5]) > 0.55 * escala
        and dist(p[4], p[17]) > dist(p[3], p[17]) * 1.02
    )

    outros = []
    for ponta, pip in zip(PONTAS[1:], PIPS[1:]):
        outros.append(dist(p[0], p[ponta]) > dist(p[0], p[pip]) * 1.12)

    return [polegar] + outros
