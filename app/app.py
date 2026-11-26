"""Loop principal: câmera -> mãos -> modo atual -> interface."""
import sys
import threading
import time

import cv2
import numpy as np

from . import config, textos
from .textos import t
from .camera import Camera
from .gestos import ModoGestos, classificar
from .jokenpo import ModoJokenpo
from .libras import ModoLibras
from .filtro import ModoFiltro
from .quadro import ModoQuadro
from .geometria import Mao
from .ui import Avisos, Camada, Fontes, desenhar_esqueleto

JANELA = "detector de maos"          # nome interno (sem acento, o OpenCV não gosta)
TITULO = "detector de mãos"          # nome que aparece em cima da janela

# o que aparece no pop-up de cada modo está em textos.py ("pop.<modo>")
TEMPO_JOINHA = 0.7      # segurar o joinha por esse tempo também confirma o pop-up


def tecla(t: str) -> str:
    """Letra da tecla em maiúscula (C, L, S...); nomes como espaço e backspace ficam como estão."""
    return t.upper() if len(t) == 1 else t




class Interface:
    """Monta a tela inteira. Separado da câmera para dar pra testar sem webcam."""

    def __init__(self):
        self.modos = [ModoGestos(), ModoJokenpo(), ModoQuadro(), ModoFiltro(), ModoLibras()]
        self.atual = 0
        self.avisos = Avisos()
        self.camada = Camada(Fontes())
        self.alvos = []              # áreas clicáveis: (caixa, "menu" | "painel" | índice do modo)
        self.menu_aberto = False
        self.dicas = True            # textinho do canto inferior direito
        self._tem_mao = False
        self.popup = None           # {'inicio', 'saindo', 'joinha_desde'}
        self.vistos = set()         # modos cujo pop-up já apareceu (só aparece na 1ª vez)
        self.abrir_popup()          # ao abrir o programa já explica o modo inicial
        self.fechar_menu_em = 0.0

    @property
    def modo(self):
        return self.modos[self.atual]

    def compor(self, frame, maos):
        h, w = frame.shape[:2]
        modo = self.modo
        if self.popup is None:
            modo.atualizar(maos, time.monotonic())   # com o pop-up aberto, o modo espera
        else:
            self._joinha(maos)

        modo.desenhar_frame(frame, maos)
        for m in maos:
            desenhar_esqueleto(frame, m, modo.cores_pontas(m))

        c = self.camada
        c.comecar(w, h)
        self._escurecer = 0.0
        modo.desenhar_ui(c, maos)
        self.alvos = []
        self._menu(c)
        self._estrela(c, maos)
        self._dicas(c)
        self._popup(c)
        # no desenhar (paleta) e no jokenpô (placar) o topo está ocupado: o aviso desce um pouco
        y_aviso = 66 if isinstance(modo, ModoQuadro) else 48 if isinstance(modo, ModoJokenpo) else 22
        self.avisos.desenhar(c, y=y_aviso)
        if self._escurecer > 0:
            frame[:] = (frame * (1 - self._escurecer)).astype(frame.dtype)
        return c.aplicar(frame)

    # ------------------------------------------------------------ menu
    def _menu(self, c):
        agora = time.monotonic()
        if self.menu_aberto and agora > self.fechar_menu_em:
            self.menu_aberto = False

        # botão ≡
        # botão ≡ no canto inferior esquerdo
        by1 = c.h - 18
        botao = (18, by1 - 33, 58, by1)
        c.vidro(botao, 16)
        meio = by1 - 16.5
        for dy in (-4.5, 0, 4.5):
            c.d.line((30, meio + dy, 46, meio + dy), fill=(255, 255, 255, 230), width=2)
        self.alvos.append((botao, "menu"))

        # botão ? ao lado: mostra de novo as instruções do modo atual
        ajuda = (botao[2] + 8, botao[1], botao[2] + 8 + 33, botao[3])
        c.vidro(ajuda, 16.5)
        c.texto(((ajuda[0] + ajuda[2]) / 2, meio + 1), "?", tamanho=15, alfa=235, ancora="mm")
        self.alvos.append((ajuda, "instrucoes"))

        # botão de idioma no canto superior esquerdo: mostra o idioma atual (PT / EN); clicar troca
        fonte = c.fontes(12)
        lw = c.medir("PT", fonte)[0] + 24
        idioma_bt = (18, 18, 18 + lw, 18 + 33)        # canto superior esquerdo
        c.vidro(idioma_bt, 16.5)
        c.texto(((idioma_bt[0] + idioma_bt[2]) / 2, 18 + 17.5), textos.idioma.upper(), tamanho=12, alfa=235, ancora="mm")
        self.alvos.append((idioma_bt, "idioma"))
        if not self.menu_aberto:
            return

        # só os modos (os atalhos ficam no canto inferior direito)
        item = 34
        largura = max(170, max(c.medir(m.nome, c.fontes(13))[0] for m in self.modos) + 70)
        altura = len(self.modos) * item + 12
        x0, y0 = 18, botao[1] - 7 - altura          # o menu abre para cima
        c.vidro((x0, y0, x0 + largura, y0 + altura), 16)

        for k, m in enumerate(self.modos):
            y = y0 + 6 + k * item
            cy = y + item / 2
            ativo = k == self.atual
            if ativo:
                c.d.rounded_rectangle((x0 + 5, y + 2, x0 + largura - 5, y + item - 2), radius=12, fill=(255, 255, 255, 38))
            c.estrela(x0 + 22, cy, 6.5, alfa=255 if ativo else 120)
            c.texto((x0 + 36, cy), m.nome, tamanho=13, alfa=255 if ativo else 130, ancora="lm")
            c.texto((x0 + largura - 16, cy), str(k + 1), tamanho=11, alfa=110, ancora="rm")
            self.alvos.append(((x0, y, x0 + largura, y + item), k))

        # clicar dentro do painel (fora dos modos) não fecha o menu
        self.alvos.append(((x0, y0, x0 + largura, y0 + altura), "painel"))

    # ------------------------------------------------------------ aviso de baixo
    def _estrela(self, c, maos):
        """Embaixo só aparece um aviso quando nenhuma mão está na tela."""
        self._tem_mao = bool(maos)
        # nesta versão o canto inferior esquerdo é do menu;
        # a instrução aparece como aviso quando você escolhe o modo

    # ------------------------------------------------------------ dicas do canto direito
    def _dicas(self, c):
        if not self.dicas:
            c.texto((c.w - 20, c.h - 22), "H  •  " + t("at.ajuda"), tamanho=12, alfa=120, ancora="rs")
            return
        linhas = [(tecla(k), d) for k, d in self.modo.atalhos]
        linhas += [("H", t("at.esconder_ajuda")), ("Q", t("at.sair"))]
        for n, (k, d) in enumerate(reversed(linhas)):
            # espaço e backspace aparecem com o ícone da tecla
            c.linha_atalho(c.w - 20, c.h - 26 - n * 17, k, d, alfa=165, direita=True)


    # ------------------------------------------------------------ ações
    def trocar_modo(self, k):
        self.atual = k
        self.menu_aberto = False
        if k not in self.vistos:      # o pop-up só aparece na primeira vez em cada modo
            self.abrir_popup()

    # ------------------------------------------------------------ pop-up do modo
    def abrir_popup(self):
        self.popup = {"inicio": time.monotonic(), "saindo": None, "joinha_desde": None}
        self.vistos.add(self.atual)

    def fechar_popup(self):
        if self.popup and self.popup["saindo"] is None:
            self.popup["saindo"] = time.monotonic()

    def _joinha(self, maos):
        """Fazer joinha por um instante também confirma o pop-up."""
        if not self.popup or self.popup["saindo"]:
            return
        tem = any(classificar(m) == "joinha" for m in maos)
        if not tem:
            self.popup["joinha_desde"] = None
        elif self.popup["joinha_desde"] is None:
            self.popup["joinha_desde"] = time.monotonic()
        elif time.monotonic() - self.popup["joinha_desde"] >= TEMPO_JOINHA:
            self.fechar_popup()

    def _popup(self, c):
        if not self.popup:
            return
        agora = time.monotonic()
        p = self.popup
        opac = min(1.0, (agora - p["inicio"]) / 0.2)
        if p["saindo"] is not None:
            opac = min(opac, 1 - (agora - p["saindo"]) / 0.25)
            if opac <= 0:
                self.popup = None
                return
        opac = max(opac, 0.0)

        # escurece um pouco a câmera para o pop-up chamar atenção (aplicado em compor)
        self._escurecer = 0.30 * opac

        linhas = t("pop." + self.modo.chave)
        f_txt = c.fontes(14)
        largura = max([300] + [c.medir(l, f_txt)[0] + 64 for l in linhas])
        altura = 26 + 30 + 14 + len(linhas) * 24 + 22 + 38 + 24
        x0, y0 = c.w / 2 - largura / 2, c.h / 2 - altura / 2
        caixa = (x0, y0, x0 + largura, y0 + altura)
        c.vidro(caixa, 22, opac)

        # título: ★ nome do modo
        y = y0 + 26 + 15
        tw = c.medir(self.modo.nome, c.fontes(20))[0]
        tx = c.w / 2 - (tw + 26) / 2
        c.estrela(tx + 8, y, 8, alfa=int(255 * opac))
        c.texto((tx + 26, y), self.modo.nome, tamanho=20, alfa=int(255 * opac), ancora="lm")
        y += 15 + 14

        # instruções, uma por linha
        for linha in linhas:
            y += 12
            c.texto((c.w / 2, y), linha, tamanho=14, alfa=int(225 * opac), ancora="mm")
            y += 12
        y += 22

        # botão ok (cheio, em azul apagado); enche de branco enquanto você segura o joinha
        bw, bh = 132, 38
        bx0 = c.w / 2 - bw / 2
        botao = (bx0, y, bx0 + bw, y + bh)
        c.d.rounded_rectangle(botao, radius=bh / 2, fill=(*config.AZUL_APAGADO, int(225 * opac)))
        if p["joinha_desde"] and p["saindo"] is None:
            prog = min(1.0, (agora - p["joinha_desde"]) / TEMPO_JOINHA)
            if prog > 0.02:
                c.d.rounded_rectangle((bx0, y, bx0 + max(bh, bw * prog), y + bh), radius=bh / 2,
                                      fill=(255, 255, 255, int(70 * opac)))
        c.texto((c.w / 2, y + bh / 2), "ok", tamanho=15, alfa=int(255 * opac), ancora="mm")
        self.alvos.insert(0, (botao, "ok"))

    def abrir_menu(self, duracao=8.0):
        self.menu_aberto = True
        self.fechar_menu_em = time.monotonic() + duracao

    def clique(self, x, y):
        if self.popup:
            for (x0, y0, x1, y1), alvo in self.alvos:
                if alvo == "ok" and x0 <= x <= x1 and y0 <= y <= y1:
                    self.fechar_popup()
            return
        for (x0, y0, x1, y1), alvo in self.alvos:
            if x0 <= x <= x1 and y0 <= y <= y1:
                if alvo == "menu":
                    if self.menu_aberto:
                        self.menu_aberto = False
                    else:
                        self.abrir_menu()
                elif alvo == "idioma":
                    self.trocar_idioma()
                elif alvo == "instrucoes":
                    self.menu_aberto = False
                    self.abrir_popup()
                elif alvo == "painel":
                    self.abrir_menu()                  # mexeu no menu: dá mais tempo
                else:
                    self.trocar_modo(alvo)
                return
        self.menu_aberto = False      # clicou fora: fecha

    def trocar_idioma(self):
        textos.trocar_idioma()
        self.avisos.mostrar(t("idioma_trocado"), 1.2)

    def tecla(self, k):
        """Retorna False quando é para sair."""
        if 65 <= k <= 90:              # aceita a letra maiúscula também
            k += 32
        if k in (ord("q"), 27):
            return False
        if ord("1") <= k < ord("1") + len(self.modos):
            self.trocar_modo(k - ord("1"))
        elif self.popup:
            if k in (13, 10):            # Enter confirma o pop-up
                self.fechar_popup()
        elif k == ord("h"):
            self.dicas = not self.dicas
        else:
            self.modo.tecla(k, self.avisos)
        return True


class DeteccaoEmParalelo:
    """Roda o MediaPipe numa thread separada.

    A tela não espera a detecção terminar: ela sempre mostra a imagem mais nova da câmera
    com as últimas mãos encontradas. Para o esqueleto não ficar "atrasado", ele é
    adiantado um pouquinho na direção em que a mão está indo (PREVER_MOVIMENTO).
    """

    def __init__(self, rastreador, inicio):
        self.rastreador = rastreador
        self.inicio = inicio
        self._frame = None
        self._tamanho = None
        self._maos, self._t = [], 0.0
        self._anteriores, self._t_ant = {}, 0.0
        self.deteccoes = 0
        self._novo = threading.Event()
        self._lock = threading.Lock()
        self._rodando = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def enviar(self, frame):
        """Manda uma cópia reduzida (é só disso que o MediaPipe precisa)."""
        h, w = frame.shape[:2]
        if w > config.LARGURA_DETECCAO:
            pequena = cv2.resize(frame, (config.LARGURA_DETECCAO, int(h * config.LARGURA_DETECCAO / w)),
                                 interpolation=cv2.INTER_AREA)
        else:
            pequena = frame.copy()
        with self._lock:
            self._frame, self._tamanho = pequena, (w, h)
        self._novo.set()

    def _loop(self):
        while self._rodando:
            if not self._novo.wait(timeout=0.5):
                continue
            self._novo.clear()
            with self._lock:
                frame, tamanho = self._frame, self._tamanho
            if frame is None:
                continue
            maos = self.rastreador.detectar(frame, int((time.monotonic() - self.inicio) * 1000), tamanho)
            agora = time.monotonic()
            with self._lock:
                self._anteriores = {m.id: m.pts for m in self._maos}
                self._t_ant = self._t
                self._maos, self._t = maos, agora
                self.deteccoes += 1

    @property
    def maos(self):
        with self._lock:
            maos, t, ant, t_ant = list(self._maos), self._t, self._anteriores, self._t_ant
        if not config.PREVER_MOVIMENTO or t_ant <= 0 or t - t_ant <= 0:
            return maos
        # adianta cada mão pela velocidade que ela tinha entre as duas últimas detecções
        dt = min(time.monotonic() - t, 0.08)
        previstas = []
        for m in maos:
            if m.id in ant:
                v = (m.pts - ant[m.id]) / (t - t_ant)
                if float(np.abs(v).max()) < 4000:         # ignora saltos absurdos
                    m = Mao(m.pts + v * dt * 0.8, m.lado, m.id)
            previstas.append(m)
        return previstas

    def parar(self):
        self._rodando = False
        self._novo.set()
        self._thread.join(timeout=1.0)


def definir_titulo(texto):
    """Título da janela com acento. No Windows o OpenCV estraga acentos no título,
    então lá o título é trocado direto pela API do Windows."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, JANELA)
            if hwnd:
                ctypes.windll.user32.SetWindowTextW(hwnd, texto)
                return
        except Exception:
            pass
    try:
        cv2.setWindowTitle(JANELA, texto)
    except Exception:
        pass


def rodar():
    from .rastreador import Rastreador

    rastreador = Rastreador()
    cap = Camera()
    tela = Interface()
    tela_cheia = False

    cv2.namedWindow(JANELA, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(JANELA, config.LARGURA, config.ALTURA)

    def mouse(evento, x, y, flags, _):
        if evento == cv2.EVENT_LBUTTONDOWN:
            tela.clique(x, y)

    cv2.setMouseCallback(JANELA, mouse)
    inicio = time.monotonic()
    quadros, marca = 0, time.monotonic()
    cam_marca, det_marca = 0, 0
    titulo_ok = False
    paralelo = DeteccaoEmParalelo(rastreador, inicio) if config.DETECCAO_EM_PARALELO else None

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("a câmera parou de mandar imagens.")
                break
            if config.ESPELHAR:
                frame = cv2.flip(frame, 1)

            rastreador.maos_desejadas = tela.modo.max_maos   # 1 ou 2 mãos, conforme o modo
            if paralelo:
                paralelo.enviar(frame)          # vai uma cópia reduzida para a detecção
                maos = paralelo.maos
            else:
                maos = rastreador.detectar(frame, int((time.monotonic() - inicio) * 1000))
            cv2.imshow(JANELA, tela.compor(frame, maos))
            if not titulo_ok:                   # a janela já existe: troca o título
                definir_titulo(TITULO)
                titulo_ok = True

            # fps no terminal a cada 2 s: tela, câmera e detecção das mãos
            quadros += 1
            agora = time.monotonic()
            if config.MOSTRAR_FPS_TERMINAL and agora - marca >= 2.0:
                dt = agora - marca
                cam = (cap.quadros - cam_marca) / dt
                det = ((paralelo.deteccoes - det_marca) / dt) if paralelo else quadros / dt
                print(f"tela {quadros / dt:4.0f} fps  |  câmera {cam:4.0f} fps  |  mãos {det:4.0f} fps")
                quadros, marca = 0, agora
                cam_marca = cap.quadros
                det_marca = paralelo.deteccoes if paralelo else 0

            k = cv2.waitKey(1) & 0xFF
            if 65 <= k <= 90:          # maiúscula (Caps Lock ou Shift) vale igual à minúscula
                k += 32
            if k != 255:
                if k == ord("f"):
                    tela_cheia = not tela_cheia
                    cv2.setWindowProperty(JANELA, cv2.WND_PROP_FULLSCREEN,
                                          cv2.WINDOW_FULLSCREEN if tela_cheia else cv2.WINDOW_NORMAL)
                elif not tela.tecla(k):
                    break
            # fechar no X da janela
            if cv2.getWindowProperty(JANELA, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        if paralelo:
            paralelo.parar()
        cap.release()
        rastreador.fechar()
        cv2.destroyAllWindows()
