"""Câmera lida numa thread separada.

Assim o programa não fica parado esperando a webcam entregar cada imagem:
enquanto ele desenha a tela, a próxima imagem já está chegando.
O modo da câmera (qualidade ou fluidez) é escolhido em CAMERA_MODO, em app/config.py.
"""
import sys
import threading

import cv2

from . import config


def _fourcc_texto(cap):
    v = int(cap.get(cv2.CAP_PROP_FOURCC))
    return "".join(chr((v >> 8 * i) & 0xFF) for i in range(4)).strip("\x00") or "?"


def _abrir(backend, largura, altura, mjpg):
    cap = cv2.VideoCapture(config.CAMERA_INDEX) if backend is None else cv2.VideoCapture(config.CAMERA_INDEX, backend)
    if not cap.isOpened():
        cap.release()
        return None
    mj = cv2.VideoWriter_fourcc(*"MJPG")
    if mjpg:
        cap.set(cv2.CAP_PROP_FOURCC, mj)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, largura)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, altura)
    if mjpg:
        cap.set(cv2.CAP_PROP_FOURCC, mj)       # alguns drivers só aceitam depois do tamanho
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)        # sempre a imagem mais recente
    if config.CAMERA_PRIORIZAR_FPS:
        # em lugar escuro a webcam aumenta a exposição e cai de fps;
        # com exposição fixa ela mantém o fps (mas a imagem fica mais escura)
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        cap.set(cv2.CAP_PROP_EXPOSURE, config.CAMERA_EXPOSICAO)
    return cap


def abrir_melhor_camera():
    """Abre a webcam no modo escolhido em CAMERA_MODO (app/config.py):
    - "qualidade": 1280x720, imagem nítida (em webcams sem MJPG fica em ~10 fps)
    - "fluidez":   640x480, bem mais fps; a imagem inteira aparece (sem zoom), um pouco menos nítida
    """
    backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else None
    if config.CAMERA_MODO == "fluidez":
        nome, w, h = "fluidez (640x480)", 640, 480
        # a tela passa a ser 4:3 para mostrar a imagem inteira, sem cortar
        config.LARGURA, config.ALTURA = 960, 720
    else:
        nome, w, h = "qualidade (1280x720)", 1280, 720
    cap = _abrir(backend, w, h, True)
    if cap is None:
        print("não consegui abrir a câmera. Feche outros apps que estejam usando a webcam")
        print("ou troque CAMERA_INDEX em app/config.py.")
        sys.exit(1)
    real_w, real_h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"câmera: modo {nome}  ->  {real_w}x{real_h}, {_fourcc_texto(cap)}")
    return cap


def _ajustar(frame):
    """Entrega sempre LARGURA x ALTURA (corta para 16:9 e redimensiona, se precisar)."""
    h, w = frame.shape[:2]
    if (w, h) == (config.LARGURA, config.ALTURA):
        return frame
    alvo = config.LARGURA / config.ALTURA
    if w / h > alvo + 0.01:                     # mais largo: corta as laterais
        nw = int(h * alvo)
        x0 = (w - nw) // 2
        frame = frame[:, x0:x0 + nw]
    elif w / h < alvo - 0.01:                   # mais alto (4:3): corta em cima e embaixo
        nh = int(w / alvo)
        y0 = (h - nh) // 2
        frame = frame[y0:y0 + nh]
    return cv2.resize(frame, (config.LARGURA, config.ALTURA), interpolation=cv2.INTER_LINEAR)


class Camera:
    def __init__(self):
        self.cap = abrir_melhor_camera()
        self.quadros = 0          # contador de imagens recebidas (para medir o fps da câmera)

        self._frame = None
        self._novo = threading.Event()
        self._lock = threading.Lock()
        self._rodando = True
        self._ok = True
        self._thread = threading.Thread(target=self._ler, daemon=True)
        self._thread.start()

    def _ler(self):
        while self._rodando:
            ok, frame = self.cap.read()
            if not ok:
                self._ok = False
                self._novo.set()
                break
            frame = _ajustar(frame)
            if config.CAMERA_PRIORIZAR_FPS and config.CAMERA_CLAREAR != 1.0:
                # exposição fixa deixa a imagem mais escura: clareia um pouco no programa
                frame = cv2.convertScaleAbs(frame, alpha=config.CAMERA_CLAREAR, beta=8)
            with self._lock:
                self._frame = frame
                self.quadros += 1
            self._novo.set()

    def read(self):
        """Espera a próxima imagem e devolve (ok, frame).
        A primeira imagem pode demorar uns segundos para chegar; depois disso,
        só desiste se a câmera ficar 3 s sem mandar nada."""
        limite = 6.0 if self.quadros == 0 else 3.0
        if not self._novo.wait(timeout=limite) or not self._ok:
            return False, None
        self._novo.clear()
        with self._lock:
            return True, self._frame

    def release(self):
        self._rodando = False
        self._thread.join(timeout=1.0)
        self.cap.release()
