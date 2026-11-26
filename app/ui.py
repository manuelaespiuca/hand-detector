"""Desenho da interface: esqueleto (OpenCV) + textos e pílulas (Pillow)."""
import functools
import math
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import config
from .geometria import CONEXOES, PONTAS, Mao

PESOS = {"regular": "Poppins-Regular.ttf", "medio": "Poppins-Medium.ttf", "negrito": "Poppins-Bold.ttf"}


def desfocar_rapido(img, sigma):
    """Desfoque forte barato: reduz a imagem, desfoca pouco e amplia de novo.
    Fica praticamente igual a um GaussianBlur grande, mas bem mais rápido."""
    h, w = img.shape[:2]
    f = 4 if min(h, w) >= 16 else 1
    if f == 1:
        return cv2.GaussianBlur(img, (0, 0), sigma)
    pequeno = cv2.resize(img, (max(1, w // f), max(1, h // f)), interpolation=cv2.INTER_AREA)
    pequeno = cv2.GaussianBlur(pequeno, (0, 0), max(sigma / f, 0.8))
    return cv2.resize(pequeno, (w, h), interpolation=cv2.INTER_LINEAR)


@functools.lru_cache(maxsize=64)
def mascara_arredondada(lw, lh, raio, escala=4):
    """Máscara arredondada suave (desenhada maior e reduzida). Guardada em cache:
    o mesmo botão usa a mesma máscara em todo frame, sem desenhar de novo."""
    im = Image.new("L", (lw * escala, lh * escala), 0)
    ImageDraw.Draw(im).rounded_rectangle((0, 0, lw * escala - 1, lh * escala - 1),
                                         radius=raio * escala, fill=255)
    m = np.asarray(im.resize((lw, lh), Image.LANCZOS), np.float32) / 255.0
    m.setflags(write=False)
    return m


def bgr(rgb):
    return (rgb[2], rgb[1], rgb[0])


class Fontes:
    def __init__(self):
        self._cache = {}

    def __call__(self, tamanho: int, peso: str = "medio"):
        chave = (tamanho, peso)
        if chave not in self._cache:
            try:
                self._cache[chave] = ImageFont.truetype(str(config.PASTA_FONTES / PESOS[peso]), tamanho)
            except OSError:
                self._cache[chave] = ImageFont.load_default(size=tamanho)
        return self._cache[chave]


# ---------------------------------------------------------------- esqueleto

def desenhar_esqueleto(frame, mao: Mao, cores_pontas=None):
    """Linhas brancas finas e pontinhos, como na referência."""
    p = mao.pts.astype(int)
    h, w = frame.shape[:2]
    # trabalha só no retângulo em volta da mão (muito mais rápido que a imagem inteira)
    x0, y0 = max(int(p[:, 0].min()) - 10, 0), max(int(p[:, 1].min()) - 10, 0)
    x1, y1 = min(int(p[:, 0].max()) + 11, w), min(int(p[:, 1].max()) + 11, h)
    if x1 > x0 and y1 > y0:
        roi = frame[y0:y1, x0:x1]
        camada = roi.copy()
        q = p - (x0, y0)
        for a, b in CONEXOES:
            cv2.line(camada, tuple(q[a]), tuple(q[b]), (255, 255, 255), 2, cv2.LINE_AA)
        cv2.addWeighted(camada, 0.75, roi, 0.25, 0, dst=roi)

    for i, (x, y) in enumerate(p):
        if i in PONTAS:
            continue
        cv2.circle(frame, (x, y), 3, (255, 255, 255), -1, cv2.LINE_AA)

    for n, i in enumerate(PONTAS):
        x, y = p[i]
        cor = cores_pontas[n] if cores_pontas and cores_pontas[n] else config.BRANCO
        cv2.circle(frame, (x, y), 6, bgr(cor), -1, cv2.LINE_AA)
        cv2.circle(frame, (x, y), 6, (255, 255, 255), 1, cv2.LINE_AA)


# ---------------------------------------------------------------- camada de textos

class Camada:
    """Tudo que é texto/pílula translúcida é desenhado aqui e depois mesclado no frame."""

    def __init__(self, fontes: Fontes):
        self.fontes = fontes
        self.img = None
        self.d = None
        self._medidas = {}
        self.w = self.h = 0

    def comecar(self, w, h):
        self.w, self.h = w, h
        self.vidros = []     # áreas de "vidro fosco" (desfocam o que está atrás)
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def vidro(self, caixa, raio, alfa=1.0):
        """Fundo de vidro fosco: desfoca bastante o que está atrás, com borda de luz e sombrinha.
        Tudo é desenhado direto no frame em _aplicar_vidros (com bordas suavizadas)."""
        self.vidros.append((caixa, raio, alfa))

    @staticmethod
    def _forma(lw, lh, raio, escala=4):
        """Máscara arredondada suave, guardada em cache (ver mascara_arredondada)."""
        return mascara_arredondada(int(lw), int(lh), int(round(raio)), escala)

    def _aplicar_vidros(self, frame):
        h, w = frame.shape[:2]
        for (x0, y0, x1, y1), raio, opac in self.vidros:
            x0, y0 = max(int(round(x0)), 0), max(int(round(y0)), 0)
            x1, y1 = min(int(round(x1)), w), min(int(round(y1)), h)
            lw, lh = x1 - x0, y1 - y0
            if lw < 4 or lh < 4:
                continue
            raio = min(raio, lw / 2, lh / 2)
            forma = self._forma(lw, lh, raio)

            # 1) sombra suave, com a mesma forma arredondada, um pouco abaixo
            m = 22
            sx0, sy0, sx1, sy1 = max(x0 - m, 0), max(y0 - m, 0), min(x1 + m, w), min(y1 + m, h)
            sombra = np.zeros((sy1 - sy0, sx1 - sx0), np.float32)
            oy = 4
            ty0, tx0 = y0 - sy0 + oy, x0 - sx0
            fh = max(0, min(lh, sombra.shape[0] - ty0))
            sombra[ty0:ty0 + fh, tx0:tx0 + lw] = forma[:fh]
            sombra = desfocar_rapido(sombra, 7)[..., None]
            area = frame[sy0:sy1, sx0:sx1].astype(np.float32)
            frame[sy0:sy1, sx0:sx1] = (area * (1 - 0.30 * opac * sombra)).astype(np.uint8)

            # 2) vidro: desfoque forte do que está atrás
            ax0, ay0, ax1, ay1 = max(x0 - m, 0), max(y0 - m, 0), min(x1 + m, w), min(y1 + m, h)
            borrado = desfocar_rapido(frame[ay0:ay1, ax0:ax1], 20)
            borrado = borrado[y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0].astype(np.float32)

            # 3) véu que se adapta ao fundo: fundo escuro -> véu claro; fundo claro -> véu escurinho
            #    (assim o texto branco continua legível em qualquer lugar)
            luz = float(borrado.mean())
            topo_baixo = np.linspace(1.0, 0.75, lh, dtype=np.float32)[:, None, None]
            if luz < 150:
                vidro = borrado + (255 - borrado) * (0.22 * topo_baixo)
            else:
                vidro = borrado * (1 - 0.20 * topo_baixo) + 255 * 0.04

            a = forma[..., None] * opac
            regiao = frame[y0:y1, x0:x1].astype(np.float32)
            regiao = regiao * (1 - a) + vidro * a

            # 4) borda de luz: mais forte em cima, quase sumindo embaixo
            interna = self._forma(lw - 2, lh - 2, max(raio - 1, 0))
            anel = np.array(forma)
            anel[1:-1, 1:-1] -= interna
            anel = np.clip(anel, 0, 1)
            brilho = np.linspace(0.65, 0.18, lh, dtype=np.float32)[:, None]
            anel = (anel * brilho)[..., None] * opac
            regiao = regiao * (1 - anel) + 255 * anel
            frame[y0:y1, x0:x1] = np.clip(regiao, 0, 255).astype(np.uint8)

    def aplicar(self, frame_bgr):
        if self.vidros:
            self._aplicar_vidros(frame_bgr)
        # em vez de converter a imagem inteira, mistura só os quadradinhos (80x80)
        # onde a camada de textos tem alguma coisa desenhada
        camada = np.asarray(self.img)
        alfa = camada[:, :, 3]
        T = 80
        h, w = alfa.shape
        for ty in range(0, h, T):
            linha = alfa[ty:ty + T]
            if not linha.any():
                continue
            for tx in range(0, w, T):
                a = linha[:, tx:tx + T]
                if not a.any():
                    continue
                a16 = a.astype(np.uint16)[..., None]
                cor = camada[ty:ty + T, tx:tx + T, 2::-1].astype(np.uint16)   # RGB -> BGR
                dst = frame_bgr[ty:ty + T, tx:tx + T]
                dst[:] = ((dst.astype(np.uint16) * (255 - a16) + cor * a16 + 127) // 255).astype(np.uint8)
        return frame_bgr

    # medidas -------------------------------------------------------------
    def medir(self, texto, fonte):
        chave = (texto, id(fonte))
        if chave not in self._medidas:
            x0, y0, x1, y1 = self.d.textbbox((0, 0), texto, font=fonte)
            if len(self._medidas) > 2000:
                self._medidas.clear()
            self._medidas[chave] = (x1 - x0, y1 - y0)
        return self._medidas[chave]

    # elementos -----------------------------------------------------------
    def texto(self, xy, texto, tamanho=16, cor=config.BRANCO, alfa=255, peso="medio", ancora="la"):
        self.d.text(xy, texto, font=self.fontes(tamanho, peso), fill=(*cor, alfa), anchor=ancora)

    def flutuante(self, x, y, texto, cor, tamanho=22, peso="medio", alfa=255):
        """Palavra solta sobre a imagem com sombrinha suave (estilo da referência)."""
        fonte = self.fontes(tamanho, peso)
        tw, th = self.medir(texto, fonte)
        x = min(max(x, tw / 2 + 8), self.w - tw / 2 - 8)
        y = min(max(y, th + 8), self.h - 8)
        self.d.text((x + 1, y + 2), texto, font=fonte, fill=(0, 0, 0, int(alfa * 0.22)), anchor="ms")
        self.d.text((x, y), texto, font=fonte, fill=(*cor, alfa), anchor="ms")

    def pilula(self, x, y, partes, tamanho=14, ancora="esquerda", fundo=(18, 18, 22, 120), pad=(14, 8), espaco=None):
        """partes: lista de (texto, cor_rgb, alfa) ou ('●', cor, alfa) para bolinhas.
        Retorna a caixa (x0, y0, x1, y1). As caixas de cada parte ficam em self.caixas_partes."""
        fonte = self.fontes(tamanho)
        espaco = int(tamanho * 0.7) if espaco is None else espaco
        larguras = []
        for txt, _, _ in partes:
            if txt == "●":
                larguras.append(tamanho * 0.55)
            elif txt == "≡":
                larguras.append(tamanho * 1.0)
            elif txt == "★":
                larguras.append(tamanho * 0.9)
            else:
                larguras.append(self.medir(txt, fonte)[0])
        largura = sum(larguras) + espaco * (len(partes) - 1) + pad[0] * 2
        altura = tamanho + pad[1] * 2 + 4
        if ancora == "direita":
            x -= largura
        elif ancora == "centro":
            x -= largura / 2
        caixa = (x, y, x + largura, y + altura)
        if isinstance(fundo, tuple) and fundo and fundo[0] == "vidro":
            self.vidro(caixa, altura / 2, fundo[1])
        elif fundo == "vidro":
            self.vidro(caixa, altura / 2)
        else:
            self.d.rounded_rectangle(caixa, radius=altura / 2, fill=fundo)
        cx = x + pad[0]
        meio = y + altura / 2
        self.caixas_partes = []
        for (txt, cor, alfa), lw in zip(partes, larguras):
            self.caixas_partes.append((cx - espaco / 2, y, cx + lw + espaco / 2, y + altura))
            if txt == "●":
                r = tamanho * 0.27
                self.d.ellipse((cx, meio - r, cx + 2 * r, meio + r), fill=(*cor, alfa))
            elif txt == "★":
                self.estrela(cx + lw / 2, meio, tamanho * 0.45, cor, alfa)
            elif txt == "≡":  # ícone de menu: três tracinhos
                for dy in (-tamanho * 0.32, 0, tamanho * 0.32):
                    self.d.line((cx, meio + dy, cx + lw, meio + dy), fill=(*cor, alfa), width=2)
            else:
                self.d.text((cx, meio), txt, font=fonte, fill=(*cor, alfa), anchor="lm")
            cx += lw + espaco
        return caixa

    def estrela(self, x, y, raio, cor=config.BRANCO, alfa=255):
        """Estrela lisa: desenhada 4x maior e reduzida, com as pontas levemente arredondadas."""
        S = 4
        lado = int(math.ceil(raio * 2 + 4))
        im = Image.new("RGBA", (lado * S, lado * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = lado * S / 2
        R = raio * S * 0.92
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = R if i % 2 == 0 else R * 0.47
            pts.append((c + r * math.cos(ang), c + r * math.sin(ang)))
        preenchimento = (*cor, alfa)
        d.polygon(pts, fill=preenchimento)
        # contorno grossinho com junção redonda = pontas suaves, sem bico serrilhado
        d.line(pts + [pts[0]], fill=preenchimento, width=max(2, int(R * 0.16)), joint="curve")
        im = im.resize((lado, lado), Image.LANCZOS)
        self.img.alpha_composite(im, (int(round(x - lado / 2)), int(round(y - lado / 2))))

    # ---------------------------------------------------------- ícones de teclas
    ICONES = {"espaço": 18, "backspace": 14}

    def _icone(self, x, meio, t, alfa):
        """Ícone desenhado em tamanho 4x e reduzido: traço liso, pontas arredondadas."""
        S = 4
        w, h = self.ICONES[t], 12
        im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cor = (255, 255, 255, alfa)
        lw = int(1.6 * S)

        def traco(pts):
            pts = [(px * S, py * S) for px, py in pts]
            d.line(pts, fill=cor, width=lw, joint="curve")
            r = lw / 2
            for px, py in (pts[0], pts[-1]):
                d.ellipse((px - r, py - r, px + r, py + r), fill=cor)

        cy = h / 2
        if t == "backspace":      # ←
            traco([(1.5, cy), (w - 1.5, cy)])
            traco([(5.5, cy - 4), (1.5, cy), (5.5, cy + 4)])
        elif t == "espaço":       # ␣
            traco([(1.5, cy - 2), (1.5, cy + 2.5), (w - 1.5, cy + 2.5), (w - 1.5, cy - 2)])
        im = im.resize((w, h), Image.LANCZOS)
        self.img.alpha_composite(im, (int(round(x)), int(round(meio - h / 2))))

    def largura_tecla(self, t, tamanho=12):
        """Largura de uma tecla: ícone (espaço, backspace) ou texto."""
        if t in self.ICONES:
            return self.ICONES[t]
        return self.medir(t, self.fontes(tamanho))[0]

    def tecla(self, x, meio, t, tamanho=12, alfa=245):
        """Desenha a tecla a partir de x, centralizada na altura 'meio'.
        espaço e backspace viram o ícone do teclado; o resto é texto."""
        cor = (255, 255, 255, alfa)
        if t in self.ICONES:
            self._icone(x, meio, t, alfa)
        else:
            self.d.text((x, meio), t, font=self.fontes(tamanho), fill=cor, anchor="lm")
        return self.largura_tecla(t, tamanho)

    def linha_atalho(self, x, meio, tecla, desc, tamanho=12, alfa=165, direita=False):
        """'tecla  •  descrição' numa linha; com direita=True, x é a borda direita."""
        sep = "  •  "
        fonte = self.fontes(tamanho)
        total = self.largura_tecla(tecla, tamanho) + self.medir(sep + desc, fonte)[0] + 2
        if direita:
            x -= total
        x += self.tecla(x, meio, tecla, tamanho, alfa) + 2
        self.d.text((x, meio), sep + desc, font=fonte, fill=(255, 255, 255, alfa), anchor="lm")
        return total

    def arco(self, x, y, raio, progresso, cor=config.BRANCO, alfa=230, largura=3):
        caixa = (x - raio, y - raio, x + raio, y + raio)
        self.d.ellipse(caixa, outline=(255, 255, 255, 50), width=largura)
        if progresso > 0:
            self.d.arc(caixa, -90, -90 + 360 * min(progresso, 1), fill=(*cor, alfa), width=largura)

    def bolinha(self, x, y, raio, cor, alfa=255, contorno=None, largura=2):
        self.d.ellipse((x - raio, y - raio, x + raio, y + raio), fill=(*cor, alfa),
                       outline=contorno, width=largura if contorno else 0)

    def anel(self, x, y, raio, cor, alfa=255, largura=2):
        self.d.ellipse((x - raio, y - raio, x + raio, y + raio), outline=(*cor, alfa), width=largura)


class Avisos:
    """Avisos rápidos numa pílula de vidro no topo, no meio da tela: aparecem e somem sozinhos.
    Usado para mostrar o modo escolhido (com a instrução dele), "salvo em...", o efeito do filtro etc."""

    def __init__(self):
        self.partes = []
        self.inicio = 0.0
        self.ate = 0.0

    def mostrar(self, texto, duracao=1.8, partes=None):
        self.partes = partes or [(texto, config.BRANCO, 245)]
        self.inicio = time.monotonic()
        self.ate = self.inicio + duracao

    def desenhar(self, camada: Camada, y=22):
        agora = time.monotonic()
        restante = self.ate - agora
        if restante <= 0:
            return
        # entra rápido e sai devagar
        opac = min(1.0, (agora - self.inicio) / 0.18, restante / 0.45)
        partes = [(t, cor, int(a * opac)) for t, cor, a in self.partes]
        camada.pilula(camada.w / 2, y, partes, tamanho=13, ancora="centro",
                      fundo=("vidro", opac), pad=(16, 8), espaco=10)
