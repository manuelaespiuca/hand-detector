"""Rastreamento das mãos com MediaPipe Tasks (Hand Landmarker)."""
import sys
import urllib.request

import cv2
import numpy as np

from . import config
from .geometria import Mao


def garantir_modelo() -> None:
    """Baixa o modelo na primeira execução (uns 7 MB)."""
    if config.MODELO.exists() and config.MODELO.stat().st_size > 1_000_000:
        return
    config.MODELO.parent.mkdir(parents=True, exist_ok=True)
    print("baixando o modelo de mãos do MediaPipe (só na primeira vez)...")
    try:
        urllib.request.urlretrieve(config.MODELO_URL, config.MODELO)
        print("modelo salvo em", config.MODELO)
    except Exception as erro:  # sem internet, firewall etc.
        print("\nnão consegui baixar o modelo:", erro)
        print("baixe manualmente este arquivo:\n ", config.MODELO_URL)
        print("e coloque em:\n ", config.MODELO)
        sys.exit(1)


class Rastreador:
    def __init__(self, max_maos: int = config.MAX_MAOS):
        garantir_modelo()
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        self._mp = mp
        self._vision = vision
        self._mp_python = mp_python
        # um detector para 1 mão e outro para 2 mãos (criados quando precisar).
        # Procurar só 1 mão é bem mais leve: com 2, o MediaPipe fica procurando
        # a segunda mão o tempo todo enquanto ela não aparece.
        self._detectores = {}
        self.maos_desejadas = max_maos
        self._ultimo_ts = -1
        self._anteriores: dict[str, np.ndarray] = {}

    def _detector(self, n):
        if n not in self._detectores:
            opcoes = self._vision.HandLandmarkerOptions(
                base_options=self._mp_python.BaseOptions(model_asset_path=str(config.MODELO)),
                running_mode=self._vision.RunningMode.VIDEO,
                num_hands=n,
                min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._detectores[n] = self._vision.HandLandmarker.create_from_options(opcoes)
        return self._detectores[n]

    def detectar(self, frame_bgr: np.ndarray, ts_ms: int, tamanho=None) -> list[Mao]:
        """tamanho=(w, h) da imagem original, quando frame_bgr já vem reduzida."""
        # o MediaPipe exige timestamps sempre crescentes
        ts_ms = max(ts_ms, self._ultimo_ts + 1)
        self._ultimo_ts = ts_ms

        h, w = frame_bgr.shape[:2]
        if tamanho is not None:
            w_orig, h_orig = tamanho
        else:
            w_orig, h_orig = w, h
        # detecta numa cópia menor: os pontos voltam normalizados (0 a 1),
        # então depois é só multiplicar pelo tamanho da imagem original
        if w > config.LARGURA_DETECCAO:
            pequena = cv2.resize(frame_bgr, (config.LARGURA_DETECCAO, int(h * config.LARGURA_DETECCAO / w)),
                                 interpolation=cv2.INTER_AREA)
        else:
            pequena = frame_bgr
        rgb = cv2.cvtColor(pequena, cv2.COLOR_BGR2RGB)
        imagem = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        resultado = self._detector(self.maos_desejadas).detect_for_video(imagem, ts_ms)

        maos = []
        usados = set()
        for i, pontos in enumerate(resultado.hand_landmarks):
            pts = np.array([[p.x * w_orig, p.y * h_orig] for p in pontos], dtype=np.float32)
            lado = resultado.handedness[i][0].category_name if resultado.handedness else "?"
            mao_id = lado if lado not in usados else f"{lado}{i}"
            usados.add(mao_id)
            maos.append(Mao(self._suavizar(mao_id, pts), lado, mao_id))

        for chave in list(self._anteriores):
            if chave not in usados:
                del self._anteriores[chave]
        return maos

    def _suavizar(self, chave: str, pts: np.ndarray) -> np.ndarray:
        """Média móvel leve para o esqueleto não tremer."""
        anterior = self._anteriores.get(chave)
        if anterior is not None:
            movimento = float(np.abs(pts - anterior).mean())
            peso = 0.45 if movimento < 4 else 0.9    # parado: suaviza; mexendo: segue a mão na hora
            pts = anterior * (1 - peso) + pts * peso
        self._anteriores[chave] = pts
        return pts

    def fechar(self) -> None:
        for d in self._detectores.values():
            d.close()
