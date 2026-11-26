"""Detector de mãos — gestos, jokenpô, desenho no ar, filtro e libras.

Rode com:  python main.py
Teclas:    1 a 5 trocam de modo · H ajuda · F tela cheia · Q sair
"""
import os
import sys

# acentos certos no terminal (no Windows o padrão estraga "mãos", "câmera"...)
for fluxo in (sys.stdout, sys.stderr):
    try:
        fluxo.reconfigure(encoding="utf-8")
    except Exception:
        pass

# esconde as mensagens técnicas do MediaPipe/TensorFlow no terminal
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

from app.app import rodar  # noqa: E402

if __name__ == "__main__":
    rodar()
