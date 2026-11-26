"""Textos da interface em português e em inglês.

O idioma troca com o botão PT/EN (canto superior esquerdo),
e a escolha fica salva no arquivo idioma.txt, na pasta do projeto.

Os nomes internos (gestos, jogadas, efeitos) continuam em português no código;
só o que aparece na tela passa por aqui.
"""
from . import config

IDIOMAS = ("pt", "en")
_ARQUIVO = config.RAIZ / "idioma.txt"

TEXTOS = {
    "pt": {
        # modos
        "modo.gestos": "gestos",
        "modo.jokenpo": "jokenpô",
        "modo.desenhar": "desenhar",
        "modo.filtro": "filtro",
        "modo.libras": "libras",
        # instruções curtas (canto / aviso)
        "instr.gestos": "faça um gesto com a mão",
        "instr.jokenpo": "faça sua jogada no pô!",
        "instr.desenhar": ["1 dedo  •  desenha", "2 dedos  •  movem", "punho  •  apaga"],
        "instr.filtro": "faça um L com as duas mãos",
        "instr.libras": "segure a letra · H J K X Z: faça o movimento",
        # pop-up de cada modo
        "pop.gestos": ["faça um gesto com a mão", "o nome dele aparece em cima da mão"],
        "pop.jokenpo": ["mostre a mão e espere o jo · ken · pô!", "mão fechada  •  pedra", "mão aberta  •  papel",
                        "indicador e médio  •  tesoura"],
        "pop.desenhar": ["1 dedo  •  desenha", "2 dedos  •  movem", "punho  •  apaga",
                         "passe o dedo numa cor para trocar"],
        "pop.filtro": ["faça um L com as duas mãos", "a área entre os dedos ganha o efeito", "E  •  troca o efeito"],
        "pop.libras": ["segure a letra até o círculo completar", "H J K X Z: faça o movimento no ar"],
        # atalhos
        "at.esconder_ajuda": "esconder ajuda",
        "at.ajuda": "ajuda",
        "at.sair": "sair",
        "at.idioma": "english",
        "at.nova_rodada": "nova rodada",
        "at.zerar_placar": "zerar placar",
        "at.trocar_cor": "trocar cor",
        "at.espessura": "espessura",
        "at.limpar": "limpar",
        "at.salvar": "salvar",
        "at.trocar_efeito": "trocar efeito",
        "at.separar_palavra": "separar palavra",
        "at.apagar": "apagar",
        # gestos (nome interno -> tela)
        "g.ok": "ok", "g.punho": "punho", "g.joinha": "joinha", "g.não curti": "não curti",
        "g.oi": "olá", "g.paz": "paz", "g.apontando": "apontando", "g.rock": "rock",
        "g.te amo": "te amo", "g.hang loose": "hang loose", "g.L": "L", "g.três": "três",
        "g.quatro": "quatro", "g.mindinho": "mindinho", "g.coração": "coração",
        "g.dedos": "{n} dedos", "g.dedo": "1 dedo",
        # jokenpô
        "j.pedra": "pedra", "j.papel": "papel", "j.tesoura": "tesoura",
        "j.silabas": ["jo", "ken", "pô!"],
        "j.placar": "você {a}   ·   {b} computador",
        "j.jogadas": "você: {sua}   ·   computador: {minha}",
        "j.ganhou": "você ganhou!", "j.perdeu": "computador ganhou", "j.empate": "empate",
        "j.nao_vi": "não vi sua jogada",
        # desenhar
        "d.borracha": "borracha",
        "d.salvo": "salvo em desenhos/{nome}.png",
        # filtro
        "f.térmico": "térmico", "f.noturno": "noturno", "f.negativo": "negativo",
        "f.pixel": "pixel", "f.contorno": "contorno",
        # libras
        "l.texto_limpo": "texto limpo",
        # geral
        "ok": "ok",
        "idioma_trocado": "português",
    },
    "en": {
        "modo.gestos": "gestures",
        "modo.jokenpo": "rock paper scissors",
        "modo.desenhar": "draw",
        "modo.filtro": "filter",
        "modo.libras": "libras",
        "instr.gestos": "make a gesture with your hand",
        "instr.jokenpo": "make your move on scissors!",
        "instr.desenhar": ["1 finger  •  draws", "2 fingers  •  move", "fist  •  erases"],
        "instr.filtro": "make an L with both hands",
        "instr.libras": "hold the letter · H J K X Z: make the movement",
        "pop.gestos": ["make a gesture with your hand", "its name appears above your hand"],
        "pop.jokenpo": ["show your hand and wait for rock · paper · scissors!", "closed hand  •  rock",
                        "open hand  •  paper", "index and middle fingers  •  scissors"],
        "pop.desenhar": ["1 finger  •  draws", "2 fingers  •  move", "fist  •  erases",
                         "touch a color with your finger to change it"],
        "pop.filtro": ["make an L with both hands", "the area between your fingers gets the effect",
                       "E  •  changes the effect"],
        "pop.libras": ["hold the letter until the circle fills up", "H J K X Z: make the movement in the air"],
        "at.esconder_ajuda": "hide help",
        "at.ajuda": "help",
        "at.sair": "quit",
        "at.idioma": "português",
        "at.nova_rodada": "new round",
        "at.zerar_placar": "reset score",
        "at.trocar_cor": "change color",
        "at.espessura": "brush size",
        "at.limpar": "clear",
        "at.salvar": "save",
        "at.trocar_efeito": "change effect",
        "at.separar_palavra": "next word",
        "at.apagar": "delete",
        "g.ok": "ok", "g.punho": "fist", "g.joinha": "thumbs up", "g.não curti": "thumbs down",
        "g.oi": "hi", "g.paz": "peace", "g.apontando": "pointing", "g.rock": "rock on",
        "g.te amo": "i love you", "g.hang loose": "hang loose", "g.L": "L", "g.três": "three",
        "g.quatro": "four", "g.mindinho": "pinky", "g.coração": "heart",
        "g.dedos": "{n} fingers", "g.dedo": "1 finger",
        "j.pedra": "rock", "j.papel": "paper", "j.tesoura": "scissors",
        "j.silabas": ["rock", "paper", "scissors!"],
        "j.placar": "you {a}   ·   {b} computer",
        "j.jogadas": "you: {sua}   ·   computer: {minha}",
        "j.ganhou": "you win!", "j.perdeu": "computer wins", "j.empate": "tie",
        "j.nao_vi": "didn't see your move",
        "d.borracha": "eraser",
        "d.salvo": "saved to desenhos/{nome}.png",
        "f.térmico": "thermal", "f.noturno": "night vision", "f.negativo": "negative",
        "f.pixel": "pixel", "f.contorno": "outline",
        "l.texto_limpo": "text cleared",
        "ok": "ok",
        "idioma_trocado": "english",
    },
}


def _carregar():
    try:
        valor = _ARQUIVO.read_text(encoding="utf-8").strip().lower()
        if valor in IDIOMAS:
            return valor
    except OSError:
        pass
    return config.IDIOMA if config.IDIOMA in IDIOMAS else "pt"


idioma = _carregar()


def t(chave, **valores):
    """Texto da chave no idioma atual (cai no português se faltar)."""
    texto = TEXTOS[idioma].get(chave, TEXTOS["pt"].get(chave, chave))
    if valores and isinstance(texto, str):
        texto = texto.format(**valores)
    return texto


def gesto(nome):
    """Nome do gesto na tela. Ex.: 'joinha' -> 'thumbs up' em inglês."""
    if nome.endswith(" dedos"):
        return t("g.dedos", n=nome.split()[0])
    if nome == "1 dedo":
        return t("g.dedo")
    return t("g." + nome)


def trocar_idioma():
    """Alterna entre português e inglês e lembra a escolha para a próxima vez."""
    global idioma
    idioma = "en" if idioma == "pt" else "pt"
    try:
        _ARQUIVO.write_text(idioma, encoding="utf-8")
    except OSError:
        pass
    return idioma
