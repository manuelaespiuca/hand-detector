<a id="topo"></a>

# Detector de mãos

🇺🇸 [Read in English](README-en.md)

Projeto de visão computacional escrito em Python que usa a webcam para rastrear as mãos em tempo real. Com [OpenCV](https://opencv.org/) e [MediaPipe](https://ai.google.dev/edge/mediapipe), ele reconhece gestos, joga pedra, papel e tesoura com você, deixa você desenhar no ar, aplica filtros numa área marcada com as mãos e lê letras do alfabeto manual de Libras. Tudo isso numa interface limpa, com botões de vidro fosco por cima da imagem da câmera, e em dois idiomas (português e inglês), trocados dentro do próprio programa.

| Informações | Detalhes |
|---|---|
| **Interface** | janela do OpenCV com a câmera em tela cheia e botões de vidro fosco (Pillow) |
| **Rastreamento** | MediaPipe Hand Landmarker: 21 pontos por mão, até 2 mãos |
| **Modos** | gestos, jokenpô, desenhar, filtro e libras |
| **Libras** | 19 letras: 14 paradas e 5 com movimento |
| **Desempenho** | câmera e detecção em threads separadas, previsão de movimento, fps no terminal |
| **Idiomas** | português e inglês, trocados pelo botão `PT` / `EN` |
| **Python** | 3.10 a 3.12 |

## Funcionalidades

### Gestos
- Faça um gesto e o nome dele aparece em cima da mão
- Reconhece: olá (mão aberta), joinha, não curti, paz, ok, rock, te amo, hang loose, apontando, L, mindinho, três, quatro e punho
- Com as duas mãos, encostar as pontas dos polegares e dos indicadores forma um **coração**
- Os dedos levantados ganham uma bolinha azul na ponta
- O resultado passa por uma votação nos últimos frames, para o nome não ficar piscando

### Jokenpô
- Mostre a mão e a contagem "jo · ken · pô!" começa sozinha
- No "pô!", faça sua jogada; o computador escolhe ao mesmo tempo

| Mão | Jogada |
|---|---|
| fechada | pedra |
| aberta | papel |
| indicador e médio levantados | tesoura |

- O placar fica no topo da tela e a próxima rodada começa sozinha se a mão continuar na frente da câmera

### Desenhar
| Mão | Ação |
|---|---|
| só o indicador levantado | desenha |
| indicador e médio | move sem desenhar |
| mão fechada | borracha |
| passar o dedo numa bolinha de cor | troca a cor |

- Seis cores na paleta do topo, espessura ajustável
- `S` salva duas imagens em `desenhos/`: a foto com o desenho por cima e só o desenho num fundo branco

### Filtro
- Faça um L com cada mão (polegar e indicador), como se estivesse enquadrando uma foto, e afaste uma da outra
- A área entre os quatro dedos ganha o efeito, com um contorno fino em volta
- Dá para fazer sozinho, com as suas duas mãos

| Efeito | Como fica |
|---|---|
| térmico | cores de câmera térmica (é o primeiro) |
| noturno | verde com granulado, estilo visão noturna |
| negativo | cores invertidas |
| pixel | imagem quadriculada |
| contorno | fundo escuro com só as bordas em branco |

### Libras
- **Letras paradas** (A B C D E I L O R S U V W Y): segure a letra até o círculo em volta dela completar
- **Letras com movimento** (H J K X Z): faça o movimento no ar; um rastro azul mostra o caminho da mão

| Letra | Como fazer |
|---|---|
| H | indicador e médio deitados (na horizontal), mexendo a mão |
| J | mindinho levantado (como o I), desenhando um J para baixo |
| K | indicador, médio e polegar levantados, subindo a mão |
| X | indicador em gancho, balançando de um lado para o outro |
| Z | só o indicador, desenhando um Z no ar |

- As letras vão formando uma palavra, que aparece embaixo da tela
- Letra parada só conta com a mão parada, então começar um J não escreve um I sem querer

## Interface

- **≡ (canto inferior esquerdo):** abre o menu com os 5 modos. Clique num modo para trocar
- **? (ao lado do ≡):** mostra de novo as instruções do modo atual
- **PT / EN (canto superior esquerdo):** troca o idioma de toda a interface entre português e inglês. A escolha fica salva em `idioma.txt` e vale na próxima vez que abrir
- **Pop-up do modo:** na primeira vez que você entra em cada modo, aparece uma janela explicando o que fazer. Ela fecha com **ok**, com `Enter` ou fazendo um **joinha** por um instante. Enquanto ela está aberta, o modo espera
- **Canto inferior direito:** os atalhos do modo atual (`H` esconde)
- **Avisos rápidos:** mensagens curtas no topo (efeito trocado, desenho salvo...) que somem sozinhas

### Teclas
| Tecla | O que faz |
|---|---|
| `1` a `5` | gestos · jokenpô · desenhar · filtro · libras |
| `H` | mostra ou esconde a ajuda |
| `F` | tela cheia |
| `Q` / `Esc` | sair |

| Modo | Teclas |
|---|---|
| jokenpô | `espaço` nova rodada · `R` zerar placar |
| desenhar | `C` trocar cor · `+` / `-` espessura · `L` limpar · `S` salvar |
| filtro | `E` trocar efeito |
| libras | `espaço` separar palavra · `backspace` apagar · `L` limpar |

As teclas funcionam com ou sem Caps Lock.

## Como rodar pelo código

1. Instale o Python **3.10, 3.11 ou 3.12** (o MediaPipe às vezes demora a sair para a versão mais nova do Python)
2. Crie um ambiente e instale as dependências:
   ```
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   source .venv/bin/activate       # Mac / Linux
   pip install -r requirements.txt
   ```
3. Rode:
   ```
   python main.py
   ```

Na primeira vez, o programa baixa sozinho o modelo de mãos do MediaPipe (`modelos/hand_landmarker.task`, uns 7 MB). Se não tiver internet, baixe [este arquivo](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task) e coloque na pasta `modelos/`.

### Configuração (`app/config.py`)

| Variável | Para que serve | Padrão |
|---|---|---|
| `CAMERA_INDEX` | qual câmera usar, se houver mais de uma | `0` |
| `CAMERA_MODO` | `"qualidade"` (1280x720, nítido) ou `"fluidez"` (640x480, mais fps) | `"qualidade"` |
| `CAMERA_PRIORIZAR_FPS` | exposição fixa: a câmera não perde fps no escuro (a imagem fica mais escura) | `False` |
| `CAMERA_CLAREAR` | com a exposição fixa, quanto o programa clareia a imagem | `1.6` |
| `ESPELHAR` | mostra a imagem como espelho | `True` |
| `LARGURA_DETECCAO` | largura da imagem usada na detecção (menor = mais rápido) | `480` |
| `DETECCAO_EM_PARALELO` | a tela não espera o MediaPipe terminar | `True` |
| `PREVER_MOVIMENTO` | adianta o esqueleto na direção em que a mão está indo | `True` |
| `MOSTRAR_FPS_TERMINAL` | mostra o fps no terminal a cada 2 s | `True` |
| `IDIOMA` | idioma da primeira vez (`"pt"` ou `"en"`); depois vale o que foi escolhido no programa | `"pt"` |
| `TEMPO_LETRA` | segundos segurando uma letra de Libras para ela ser escrita | `0.9` |
| `CORES_QUADRO` | cores da paleta do modo desenhar | 6 tons pastel |

## Desempenho

Enquanto o programa roda, o terminal mostra a cada 2 segundos algo assim:

```
tela   30 fps  |  câmera   30 fps  |  mãos   24 fps
```

- **tela:** quantas vezes por segundo a janela é desenhada
- **câmera:** quantas imagens a webcam está mandando
- **mãos:** quantas vezes por segundo o MediaPipe encontra as mãos

O que já vem otimizado:
- a câmera é lida numa thread separada, então o programa não fica parado esperando cada imagem
- a detecção roda em outra thread, numa cópia reduzida da imagem
- cada modo procura só as mãos que usa: **gestos** e **filtro** procuram 2; **jokenpô**, **desenhar** e **libras** procuram 1 (procurar uma segunda mão que não aparece custa caro)
- o esqueleto é adiantado um pouquinho na direção do movimento, para não ficar atrás da mão
- a interface só redesenha os pedaços da tela que têm alguma coisa por cima

## Quando algo dá errado

| Situação | O que fazer |
|---|---|
| "não consegui abrir a câmera" | feche outros programas que usam a webcam (Zoom, Teams, navegador) ou troque `CAMERA_INDEX` |
| "não consegui baixar o modelo" | baixe o arquivo à mão (link em [Como rodar](#como-rodar-pelo-código)) e coloque em `modelos/` |
| câmera em ~10 fps | muitas webcams sem compressão MJPG ficam presas em ~10 fps no 720p; use `CAMERA_MODO = "fluidez"` |
| câmera lenta em lugar escuro | acenda uma luz (no escuro a webcam deixa cada foto mais tempo exposta) ou use `CAMERA_PRIORIZAR_FPS = True` |
| "mãos" com fps baixo | use `LARGURA_DETECCAO = 320`, deixe o notebook na tomada e feche programas pesados |
| esqueleto parecendo atrasado | use `DETECCAO_EM_PARALELO = False` (o fps cai, mas o esqueleto fica grudado na mão) |
| `pip install` falha no `mediapipe` | confira se o Python é 3.10, 3.11 ou 3.12 |
| gesto ou letra não reconhecido | palma virada para a câmera, mão inteira no quadro e boa iluminação ajudam muito |

## Estrutura do projeto

```
.
├── main.py              # ponto de entrada
├── requirements.txt
├── README-en.md         # este README em inglês
├── LICENSE              # licença MIT
├── .gitignore           # deixa de fora o modelo, os desenhos salvos, o idioma.txt e caches
├── app/
│   ├── config.py        # câmera, desempenho, cores e tempos
│   ├── camera.py        # webcam lida numa thread separada
│   ├── rastreador.py    # MediaPipe Hand Landmarker (baixa o modelo na primeira vez)
│   ├── geometria.py     # dedos levantados, curvatura e distâncias da mão
│   ├── app.py           # loop principal, menu, pop-ups e detecção em paralelo
│   ├── ui.py            # esqueleto, textos, vidro fosco e ícones
│   ├── textos.py        # todos os textos da tela, em português e em inglês
│   ├── gestos.py        # modo 1
│   ├── jokenpo.py       # modo 2
│   ├── quadro.py        # modo 3 (desenhar)
│   ├── filtro.py        # modo 4
│   └── libras.py        # modo 5
├── fontes/              # fonte Poppins (licença OFL)
├── modelos/             # o modelo do MediaPipe é baixado aqui (não vai para o GitHub)
├── desenhos/            # desenhos salvos com S (não vão para o GitHub)
└── visualizacao/        # prévias da interface
```

## Como funciona

1. O OpenCV lê a webcam e espelha a imagem
2. O MediaPipe devolve 21 pontos (x, y) para cada mão
3. `geometria.py` decide quais dedos estão levantados comparando distâncias até o pulso, divididas pelo tamanho da palma (assim funciona perto e longe da câmera)
4. Cada modo transforma isso num gesto, numa jogada, num traço, num filtro ou numa letra
5. A interface é desenhada com OpenCV (esqueleto) e Pillow (textos, vidro fosco e ícones)

## Bibliotecas usadas

- [`opencv-python`](https://pypi.org/project/opencv-python/): câmera, janela e desenho do esqueleto
- [`mediapipe`](https://pypi.org/project/mediapipe/): rastreamento das mãos
- [`numpy`](https://pypi.org/project/numpy/): contas com os pontos e as imagens
- [`Pillow`](https://pypi.org/project/pillow/): textos com fonte, vidro fosco e ícones

## Limitações

- O reconhecimento de gestos e de Libras é feito por regras, sem uma rede treinada, então é uma aproximação. Letras parecidas (A/S, U/V, D/O) podem se confundir dependendo do ângulo
- O Ç ainda não está incluído
- Funciona melhor com a palma virada para a câmera, a mão inteira no quadro e boa iluminação

## Licença

O código deste projeto é distribuído sob a licença [MIT](LICENSE): você pode usar, copiar, modificar e distribuir, desde que mantenha o aviso de copyright e a licença.

A fonte Poppins (pasta `fontes/`) tem a sua própria licença, a SIL Open Font License 1.1. O modelo de mãos é do Google MediaPipe e é baixado do site oficial.

Copyright (c) 2026 Manuela Espiúca.

---

<p align="center">
  <a href="#topo">↑ voltar ao topo</a>
</p>
