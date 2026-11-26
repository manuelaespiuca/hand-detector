<a id="top"></a>

# Hand detector

🇧🇷 [Ler em português](README.md)

A computer vision project written in Python that uses your webcam to track your hands in real time. With [OpenCV](https://opencv.org/) and [MediaPipe](https://ai.google.dev/edge/mediapipe), it recognizes gestures, plays rock, paper, scissors with you, lets you draw in the air, applies filters to an area you frame with your hands and reads letters of the Libras (Brazilian Sign Language) manual alphabet. All of this in a clean interface, with frosted glass buttons on top of the camera image, in two languages (Portuguese and English) that you can switch inside the program itself.

| Info | Details |
|---|---|
| **Interface** | OpenCV window with the camera full screen and frosted glass buttons (Pillow) |
| **Tracking** | MediaPipe Hand Landmarker: 21 points per hand, up to 2 hands |
| **Modes** | gestures, rock paper scissors (jokenpô), drawing, filter and Libras |
| **Libras** | 19 letters: 14 static and 5 with movement |
| **Performance** | camera and detection in separate threads, motion prediction, fps in the terminal |
| **Languages** | Portuguese and English, switched with the `PT` / `EN` button |
| **Python** | 3.10 to 3.12 |

The interface can be switched to English with the `EN` button. The names in the tables below are the Portuguese ones, with the English version next to them.

## Features

### Gestures (`gestos`)
- Make a gesture and its name appears above your hand
- Recognizes: `olá` (open hand / hi), `joinha` (thumbs up), `não curti` (thumbs down), `paz` (peace), `ok`, `rock`, `te amo` (I love you), `hang loose`, `apontando` (pointing), `L`, `mindinho` (pinky), `três` (three), `quatro` (four) and `punho` (fist)
- With both hands, touching the tips of your thumbs and index fingers makes a **heart** (`coração`)
- Raised fingers get a blue dot on the tip
- The result goes through a vote over the last frames, so the name doesn't flicker

### Rock paper scissors (`jokenpô`)
- Show your hand and the "jo · ken · pô!" countdown starts on its own
- On "pô!", make your move; the computer picks at the same time

| Hand | Move |
|---|---|
| closed | rock (`pedra`) |
| open | paper (`papel`) |
| index and middle fingers up | scissors (`tesoura`) |

- The score stays at the top of the screen, and the next round starts on its own if your hand stays in front of the camera

### Drawing (`desenhar`)
| Hand | Action |
|---|---|
| only the index finger up | draws |
| index and middle fingers | moves without drawing |
| closed hand | eraser |
| touch a color dot with your finger | changes the color |

- Six colors in the palette at the top, adjustable brush size
- `S` saves two images to `desenhos/`: the photo with the drawing on top, and just the drawing on a white background

### Filter (`filtro`)
- Make an L with each hand (thumb and index finger), as if framing a photo, and move them apart
- The area between the four fingers gets the effect, with a thin outline around it
- You can do it alone, with your own two hands

| Effect | What it looks like |
|---|---|
| `térmico` | thermal camera colors (the first one) |
| `noturno` | green with grain, night vision style |
| `negativo` | inverted colors |
| `pixel` | pixelated image |
| `contorno` | dark background with only the edges in white |

### Libras (Brazilian Sign Language)
- **Static letters** (A B C D E I L O R S U V W Y): hold the letter until the circle around it fills up
- **Letters with movement** (H J K X Z): make the movement in the air; a blue trail shows the path of your hand

| Letter | How to make it |
|---|---|
| H | index and middle fingers lying flat (horizontal), moving the hand |
| J | pinky up (like the I), drawing a J downwards |
| K | index, middle finger and thumb up, moving the hand up |
| X | index finger hooked, swinging from side to side |
| Z | only the index finger, drawing a Z in the air |

- The letters form a word, shown at the bottom of the screen
- A static letter only counts when the hand is still, so starting a J doesn't write an I by accident

## Interface

- **≡ (bottom left corner):** opens the menu with the 5 modes. Click a mode to switch
- **? (next to ≡):** shows the instructions for the current mode again
- **PT / EN (top left corner):** switches the whole interface between Portuguese and English. The choice is saved in `idioma.txt` and kept for the next time you open it
- **Mode pop-up:** the first time you enter each mode, a window explains what to do. It closes with **ok**, with `Enter` or by holding a **thumbs up** for a moment. While it's open, the mode waits
- **Bottom right corner:** the shortcuts for the current mode (`H` hides them)
- **Quick notices:** short messages at the top (effect changed, drawing saved...) that disappear on their own

### Keys
| Key | What it does |
|---|---|
| `1` to `5` | gestures · rock paper scissors · drawing · filter · Libras |
| `H` | shows or hides the help |
| `F` | full screen |
| `Q` / `Esc` | quit |

| Mode | Keys |
|---|---|
| rock paper scissors | `space` new round · `R` reset score |
| drawing | `C` change color · `+` / `-` brush size · `L` clear · `S` save |
| filter | `E` change effect |
| Libras | `space` separate words · `backspace` delete · `L` clear |

Keys work with or without Caps Lock.

## How to run from the source code

1. Install Python **3.10, 3.11 or 3.12** (MediaPipe sometimes takes a while to support the newest Python version)
2. Create an environment and install the dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   source .venv/bin/activate       # Mac / Linux
   pip install -r requirements.txt
   ```
3. Run:
   ```
   python main.py
   ```

The first time, the program downloads the MediaPipe hand model on its own (`modelos/hand_landmarker.task`, about 7 MB). If you don't have internet, download [this file](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task) and put it in the `modelos/` folder.

### Settings (`app/config.py`)

| Variable | What it's for | Default |
|---|---|---|
| `CAMERA_INDEX` | which camera to use, if there's more than one | `0` |
| `CAMERA_MODO` | `"qualidade"` (1280x720, sharp) or `"fluidez"` (640x480, more fps) | `"qualidade"` |
| `CAMERA_PRIORIZAR_FPS` | fixed exposure: the camera doesn't lose fps in the dark (the image gets darker) | `False` |
| `CAMERA_CLAREAR` | with fixed exposure, how much the program brightens the image | `1.6` |
| `ESPELHAR` | shows the image mirrored | `True` |
| `LARGURA_DETECCAO` | width of the image used for detection (smaller = faster) | `480` |
| `DETECCAO_EM_PARALELO` | the screen doesn't wait for MediaPipe to finish | `True` |
| `PREVER_MOVIMENTO` | moves the skeleton slightly ahead in the direction the hand is going | `True` |
| `MOSTRAR_FPS_TERMINAL` | shows the fps in the terminal every 2 s | `True` |
| `IDIOMA` | language for the first run (`"pt"` or `"en"`); after that, the choice made in the program is used | `"pt"` |
| `TEMPO_LETRA` | seconds holding a Libras letter before it's written | `0.9` |
| `CORES_QUADRO` | colors of the drawing mode palette | 6 pastel tones |

## Performance

While the program runs, the terminal shows something like this every 2 seconds:

```
tela   30 fps  |  câmera   30 fps  |  mãos   24 fps
```

- **tela (screen):** how many times per second the window is drawn
- **câmera (camera):** how many images the webcam is sending
- **mãos (hands):** how many times per second MediaPipe finds the hands

What's already optimized:
- the camera is read in a separate thread, so the program doesn't stall waiting for each image
- detection runs in another thread, on a smaller copy of the image
- each mode only looks for the hands it uses: **gestures** and **filter** look for 2; **rock paper scissors**, **drawing** and **Libras** look for 1 (looking for a second hand that never shows up is expensive)
- the skeleton is moved slightly ahead in the direction of the movement, so it doesn't lag behind the hand
- the interface only redraws the parts of the screen that have something on top

## When something goes wrong

| Situation | What to do |
|---|---|
| "não consegui abrir a câmera" (couldn't open the camera) | close other programs using the webcam (Zoom, Teams, browser) or change `CAMERA_INDEX` |
| "não consegui baixar o modelo" (couldn't download the model) | download the file by hand (link in [How to run](#how-to-run-from-the-source-code)) and put it in `modelos/` |
| camera at ~10 fps | many webcams without MJPG compression are stuck at ~10 fps in 720p; use `CAMERA_MODO = "fluidez"` |
| slow camera in a dark place | turn on a light (in the dark the webcam exposes each frame for longer) or use `CAMERA_PRIORIZAR_FPS = True` |
| low "mãos" (hands) fps | use `LARGURA_DETECCAO = 320`, plug in your laptop and close heavy programs |
| skeleton looks delayed | use `DETECCAO_EM_PARALELO = False` (fps drops, but the skeleton sticks to the hand) |
| `pip install` fails on `mediapipe` | check that your Python is 3.10, 3.11 or 3.12 |
| gesture or letter not recognized | palm facing the camera, the whole hand in frame and good lighting help a lot |

## Project structure

```
.
├── main.py              # entry point
├── requirements.txt
├── README.md            # this README in Portuguese
├── LICENSE              # MIT license
├── .gitignore           # leaves out the model, saved drawings, idioma.txt and caches
├── app/
│   ├── config.py        # camera, performance, colors and timings
│   ├── camera.py        # webcam read in a separate thread
│   ├── rastreador.py    # MediaPipe Hand Landmarker (downloads the model the first time)
│   ├── geometria.py     # raised fingers, curvature and hand distances
│   ├── app.py           # main loop, menu, pop-ups and parallel detection
│   ├── ui.py            # skeleton, text, frosted glass and icons
│   ├── textos.py        # all on-screen text, in Portuguese and English
│   ├── gestos.py        # mode 1 (gestures)
│   ├── jokenpo.py       # mode 2 (rock paper scissors)
│   ├── quadro.py        # mode 3 (drawing)
│   ├── filtro.py        # mode 4 (filter)
│   └── libras.py        # mode 5 (Libras)
├── fontes/              # Poppins font (OFL license)
├── modelos/             # the MediaPipe model is downloaded here (not on GitHub)
├── desenhos/            # drawings saved with S (not on GitHub)
└── visualizacao/        # interface previews
```

## How it works

1. OpenCV reads the webcam and mirrors the image
2. MediaPipe returns 21 points (x, y) for each hand
3. `geometria.py` decides which fingers are up by comparing distances to the wrist, divided by the palm size (so it works both close to and far from the camera)
4. Each mode turns that into a gesture, a move, a stroke, a filter or a letter
5. The interface is drawn with OpenCV (skeleton) and Pillow (text, frosted glass and icons)

## Libraries used

- [`opencv-python`](https://pypi.org/project/opencv-python/): camera, window and skeleton drawing
- [`mediapipe`](https://pypi.org/project/mediapipe/): hand tracking
- [`numpy`](https://pypi.org/project/numpy/): math with the points and images
- [`Pillow`](https://pypi.org/project/pillow/): text with fonts, frosted glass and icons

## Limitations

- Gesture and Libras recognition is rule-based, without a trained network, so it's an approximation. Similar letters (A/S, U/V, D/O) can get mixed up depending on the angle
- The letter Ç is not included yet
- It works best with the palm facing the camera, the whole hand in frame and good lighting

## License

The code of this project is distributed under the [MIT](LICENSE) license: you can use, copy, modify and distribute it, as long as you keep the copyright notice and the license.

The Poppins font (`fontes/` folder) has its own license, the SIL Open Font License 1.1. The hand model belongs to Google MediaPipe and is downloaded from the official website.

Copyright (c) 2026 Manuela Espiúca.

---

<p align="center">
  <a href="#top">↑ back to top</a>
</p>
