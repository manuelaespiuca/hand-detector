"""Configurações gerais. Mude à vontade."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# idioma inicial ("pt" ou "en"); depois a escolha feita no programa fica salva em idioma.txt
IDIOMA = "pt"

# câmera
CAMERA_INDEX = 0          # troque para 1, 2... se tiver mais de uma câmera
LARGURA = 1280
ALTURA = 720
ESPELHAR = True           # imagem como espelho (mais natural)

# rastreamento
# a detecção roda numa imagem menor (bem mais rápido; a precisão quase não muda)
LARGURA_DETECCAO = 480   # o MediaPipe reduz internamente para ~200 px; 480 já sobra
DETECCAO_EM_PARALELO = True   # a tela não espera o MediaPipe (fps bem maior)
PREVER_MOVIMENTO = True       # adianta o esqueleto na direção em que a mão está indo (menos atraso)
MOSTRAR_FPS_TERMINAL = True   # mostra no terminal: fps da tela, da câmera e da detecção
# "qualidade" = 1280x720 nítido (webcams sem MJPG ficam em ~10 fps nesse modo)
# "fluidez"   = 640x480 com bem mais fps, imagem inteira (sem zoom), um pouco menos nítida
CAMERA_MODO = "qualidade"
CAMERA_PRIORIZAR_FPS = False  # True = exposição fixa (30 fps mesmo no escuro, imagem mais escura)
CAMERA_EXPOSICAO = -6         # usado só com CAMERA_PRIORIZAR_FPS (mais perto de 0 = mais claro)
CAMERA_CLAREAR = 1.6          # com CAMERA_PRIORIZAR_FPS, clareia a imagem no programa (1.0 = não mexe)
MAX_MAOS = 2
MODELO = RAIZ / "modelos" / "hand_landmarker.task"
MODELO_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

# pastas
PASTA_FONTES = RAIZ / "fontes"
PASTA_DESENHOS = RAIZ / "desenhos"

# paleta pastel (RGB)
MENTA = (142, 214, 165)
ROSA = (246, 168, 196)
VERMELHO = (232, 96, 112)
AZUL = (140, 196, 245)
LILAS = (192, 170, 245)
AMARELO = (248, 214, 120)
BRANCO = (255, 255, 255)
AZUL_APAGADO = (148, 170, 196)   # pontas dos dedos levantados

PASTEIS = [MENTA, ROSA, AZUL, AMARELO, LILAS, VERMELHO]

# cores do quadro (a primeira é a inicial)
CORES_QUADRO = [ROSA, AZUL, MENTA, AMARELO, LILAS, BRANCO]

# libras: quanto tempo segurar a letra para ela entrar no texto (segundos)
TEMPO_LETRA = 0.9
