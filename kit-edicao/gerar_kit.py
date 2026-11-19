"""Gera o kit de edição do @oduduslv: LUTs (.cube), efeitos sonoros (.wav) e overlays (.png).

Rodar de novo recria tudo do zero:  python3 kit-edicao/gerar_kit.py
Depende só de numpy e Pillow.
"""
import colorsys
import os
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))

# Cores da marca (as mesmas do site)
NAVY_FUNDO = (6, 13, 26)      # #060D1A
NAVY = (10, 26, 51)           # #0A1A33
NAVY_2 = (16, 40, 75)         # #10284B
AZUL_CLARO = (127, 168, 238)  # #7FA8EE  (acento)
AZUL_BOTAO = (47, 111, 228)   # #2F6FE4
BRANCO = (230, 236, 245)      # #E6ECF5


# ---------------------------------------------------------------- LUTs
def luma(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def curva_s(x, forca):
    """Curva S suave em torno de 0.5 (forca 0 = nada)."""
    s = x + forca * (x - 0.5) * (1 - np.abs(2 * x - 1)) * 2
    return np.clip(s, 0, 1)


def mascara_pele(rgb):
    """1 onde a cor parece pele (laranja, matiz ~10-45 graus), 0 longe disso."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.max(rgb, -1)
    mn = np.min(rgb, -1)
    sat = (mx - mn) / (mx + 1e-6)
    hue = np.zeros_like(r)
    d = mx - mn + 1e-6
    m = mx == r
    hue[m] = ((g - b)[m] / d[m]) % 6
    m = mx == g
    hue[m] = ((b - r)[m] / d[m]) + 2
    m = mx == b
    hue[m] = ((r - g)[m] / d[m]) + 4
    hue = hue * 60
    perto = np.clip(1 - np.abs(hue - 25) / 25, 0, 1)
    return perto * np.clip(sat * 3, 0, 1) * np.clip((mx - 0.1) * 4, 0, 1)


def mascara_matiz(rgb, centro, largura):
    h = np.zeros(rgb.shape[:-1])
    flat = rgb.reshape(-1, 3)
    hs = np.array([colorsys.rgb_to_hsv(*p)[0] * 360 for p in flat]).reshape(h.shape)
    dist = np.minimum(np.abs(hs - centro), 360 - np.abs(hs - centro))
    mx = np.max(rgb, -1)
    sat = (mx - np.min(rgb, -1)) / (mx + 1e-6)
    return np.clip(1 - dist / largura, 0, 1) * np.clip(sat * 2.5, 0, 1)


def saturar(rgb, fator):
    y = luma(rgb)[..., None]
    return y + (rgb - y) * fator


def graduar(rgb, p):
    """Aplica uma receita p (dict) a uma grade rgb em [0,1]."""
    out = rgb * np.array(p.get("balanco", (1, 1, 1)))           # balanço de branco
    out = out * p.get("exposicao", 1.0)
    out = np.clip(out, 0, 1)

    # tira o verde/amarelo da luz fluorescente e das paredes (exceto pele)
    if p.get("tira_amarelo_verde"):
        pele = mascara_pele(out)[..., None]
        m = mascara_matiz(out, 75, 45)[..., None] * (1 - pele)
        out = out * (1 - m) + saturar(out, 1 - p["tira_amarelo_verde"]) * m

    # contraste (curva S no luma, preservando a cor)
    y0 = luma(out)
    y1 = curva_s(y0, p.get("contraste", 0))
    out = out * ((y1 + 1e-4) / (y0 + 1e-4))[..., None]

    # pretos levantados (look "fosco") e brancos contidos
    preto, branco = p.get("pretos", 0.0), p.get("brancos", 1.0)
    out = preto + out * (branco - preto)

    # split toning: sombras puxadas pro navy da marca, luzes levemente quentes
    y = np.clip(luma(out), 0, 1)[..., None]
    w_sombra = np.clip(1 - y / 0.45, 0, 1) ** 1.5
    w_luz = np.clip((y - 0.55) / 0.45, 0, 1) ** 1.5
    tom_sombra = np.array(p.get("tom_sombra", (0.06, 0.16, 0.36)))
    tom_luz = np.array(p.get("tom_luz", (1.0, 0.92, 0.80)))
    out = out + (tom_sombra - 0.2) * w_sombra * p.get("forca_sombra", 0.0)
    out = out + (tom_luz - 0.9) * w_luz * p.get("forca_luz", 0.0)

    # saturação geral, com a pele protegida e com ajuste próprio
    pele = mascara_pele(np.clip(out, 0, 1))[..., None]
    geral = saturar(out, p.get("saturacao", 1.0))
    da_pele = saturar(out, p.get("saturacao_pele", 1.0))
    out = geral * (1 - pele) + da_pele * pele
    if p.get("pele_quente"):
        out = out + pele * np.array([1, 0.35, -0.6]) * p["pele_quente"]

    # azul da marca um pouco mais vivo (camisetas, céu, LEDs da academia)
    if p.get("azul_vivo"):
        m = mascara_matiz(np.clip(out, 0, 1), 220, 40)[..., None]
        out = out * (1 - m) + saturar(out, 1 + p["azul_vivo"]) * m

    return np.clip(out, 0, 1)


RECEITAS = {
    # Uso diário: o look padrão do perfil. Contraste moderado, sombra navy, pele natural.
    "ODUDU_01_Base": dict(
        balanco=(1.0, 0.985, 1.0), contraste=0.18, pretos=0.025, brancos=0.97,
        forca_sombra=0.22, forca_luz=0.10, saturacao=0.90, saturacao_pele=1.02,
        tira_amarelo_verde=0.35, azul_vivo=0.15,
    ),
    # Shape / antes e depois / pose: mais contraste e pele mais dourada para marcar definição.
    "ODUDU_02_Shape": dict(
        balanco=(1.01, 0.98, 0.98), contraste=0.32, pretos=0.015, brancos=0.98,
        forca_sombra=0.30, forca_luz=0.12, saturacao=0.82, saturacao_pele=1.08,
        pele_quente=0.025, tira_amarelo_verde=0.45, azul_vivo=0.10,
    ),
    # Academia com luz fluorescente/LED: corrige o verde, esfria o ambiente.
    "ODUDU_03_Academia": dict(
        balanco=(1.0, 0.97, 1.01), contraste=0.22, pretos=0.03, brancos=0.96,
        forca_sombra=0.30, forca_luz=0.04, saturacao=0.85, saturacao_pele=1.0,
        tira_amarelo_verde=0.55, azul_vivo=0.25,
    ),
    # Corrida / externa com sol: céu azul vivo, sol quente, sombras navy.
    "ODUDU_04_Corrida": dict(
        balanco=(1.0, 0.99, 0.99), exposicao=0.98, contraste=0.20, pretos=0.02, brancos=0.97,
        forca_sombra=0.25, forca_luz=0.18, saturacao=0.95, saturacao_pele=1.0,
        tira_amarelo_verde=0.20, azul_vivo=0.30,
    ),
    # Mente / reflexão / fala calma: dessaturado, pretos lavados, bem frio.
    "ODUDU_05_Mente": dict(
        balanco=(0.98, 0.99, 1.03), contraste=0.10, pretos=0.06, brancos=0.93,
        forca_sombra=0.40, forca_luz=0.0, saturacao=0.60, saturacao_pele=0.80,
        tira_amarelo_verde=0.30,
    ),
}

N = 33


def grade_lut():
    v = np.linspace(0, 1, N)
    # .cube: vermelho varia mais rápido, depois verde, depois azul
    b, g, r = np.meshgrid(v, v, v, indexing="ij")
    return np.stack([r, g, b], -1)  # forma (B, G, R, 3)


def escrever_cube(nome, receita):
    tab = graduar(grade_lut(), receita).reshape(-1, 3)
    caminho = os.path.join(AQUI, "luts", nome + ".cube")
    with open(caminho, "w") as f:
        f.write(f'TITLE "{nome}"\n# Kit de edicao @oduduslv\nLUT_3D_SIZE {N}\n')
        f.write("DOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n")
        for r, g, b in tab:
            f.write(f"{r:.6f} {g:.6f} {b:.6f}\n")
    return caminho


# ---------------------------------------------------------------- Sons
SR = 48000


def salvar_wav(nome, x, estereo_largura=0.0):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89  # pico em -1 dBFS
    esq = x
    dir_ = x
    if estereo_largura:
        atraso = int(SR * 0.0007 * estereo_largura)
        dir_ = np.concatenate([np.zeros(atraso), x[: len(x) - atraso]])
    pcm = (np.stack([esq, dir_], -1) * 32767).astype("<i2")
    with wave.open(os.path.join(AQUI, "sons", nome + ".wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def t(seg):
    return np.arange(int(SR * seg)) / SR


def env(n, ataque, queda_tau):
    a = int(SR * ataque)
    e = np.exp(-np.arange(n) / (SR * queda_tau))
    if a:
        e[:a] *= np.linspace(0, 1, a)
    return e


def passa_banda_varrendo(ruido, f_ini, f_fim, q=4.0):
    """Filtro de estado variável com frequência central varrendo (whoosh)."""
    n = len(ruido)
    fc = np.geomspace(f_ini, f_fim, n)
    low = band = 0.0
    out = np.empty(n)
    damp = 1 / q
    for i in range(n):
        f = 2 * np.sin(np.pi * fc[i] / SR)
        high = ruido[i] - low - damp * band
        band += f * high
        low += f * band
        out[i] = band
    return out


def gerar_sons():
    rng = np.random.default_rng(7)

    # 1. Whoosh de transição (0,6 s): ruído com filtro subindo e descendo
    d = 0.6
    n = int(SR * d)
    ruido = rng.standard_normal(n)
    sobe = passa_banda_varrendo(ruido[: n // 2], 300, 3500)
    desce = passa_banda_varrendo(ruido[n // 2:], 3500, 600)
    w = np.concatenate([sobe, desce]) * np.sin(np.linspace(0, np.pi, n)) ** 2
    salvar_wav("01_whoosh_transicao", w, estereo_largura=1)

    # 2. Pop de legenda (0,12 s): seno com queda de afinação
    tt = t(0.12)
    f = 900 * np.exp(-tt * 30) + 380
    pop = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.002, 0.025)
    salvar_wav("02_pop_legenda", pop)

    # 3. Tick do contador "DIA XX/30" (0,05 s)
    tt = t(0.05)
    tick = (np.sin(2 * np.pi * 2400 * tt) * 0.6 + rng.standard_normal(len(tt)) * 0.4) * env(len(tt), 0.0005, 0.006)
    salvar_wav("03_tick_contador", tick)

    # 4. Anilha (1,2 s): batida metálica inarmônica, a "cara" da academia
    tt = t(1.2)
    parciais = [(523, 1.0, 0.35), (1347, 0.6, 0.22), (2210, 0.45, 0.15), (3120, 0.3, 0.09), (4480, 0.2, 0.05)]
    anilha = sum(a * np.sin(2 * np.pi * fr * tt) * np.exp(-tt / tau) for fr, a, tau in parciais)
    anilha += rng.standard_normal(len(tt)) * np.exp(-tt / 0.008) * 0.8
    salvar_wav("04_anilha_impacto_metalico", anilha, estereo_largura=0.5)

    # 5. Impacto grave (1,0 s): para revelar o "depois" / número grande na tela
    tt = t(1.0)
    f = 140 * np.exp(-tt * 9) + 42
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.35)
    boom += rng.standard_normal(len(tt)) * np.exp(-tt / 0.015) * 0.5
    boom = np.tanh(boom * 1.8)
    salvar_wav("05_impacto_grave", boom)

    # 6. Riser (2,0 s): tensão antes do antes/depois. Termina seco no tempo 2,0 s.
    d = 2.0
    n = int(SR * d)
    tt = t(d)
    ruido = passa_banda_varrendo(rng.standard_normal(n), 200, 6000, q=2.5)
    f = 180 * (2 ** (tt * 2))
    tom = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    riser = (ruido + tom) * (tt / d) ** 2.2
    riser[-int(SR * 0.004):] *= np.linspace(1, 0, int(SR * 0.004))
    salvar_wav("06_riser_antes_depois", riser, estereo_largura=1)

    # 7. Ding do cupom (0,9 s): duas notas brilhantes (quinta justa)
    tt = t(0.9)
    sino = lambda fr: (np.sin(2 * np.pi * fr * tt) + 0.3 * np.sin(2 * np.pi * fr * 2.76 * tt) * np.exp(-tt / 0.08))
    a = sino(1318.5) * np.exp(-tt / 0.25)
    b = np.concatenate([np.zeros(int(SR * 0.09)), (sino(1975.5) * np.exp(-tt / 0.35))[: len(tt) - int(SR * 0.09)]])
    salvar_wav("07_ding_cupom", (a + b) * env(len(tt), 0.002, 10))

    # 8. Assinatura sonora (1,4 s): três notas subindo + anilha leve. Usar SEMPRE no final.
    tt = t(1.4)
    out = np.zeros(len(tt))
    for i, fr in enumerate([392.0, 523.25, 783.99]):  # Sol, Dó, Sol (sobe uma oitava)
        ini = int(SR * 0.11 * i)
        tn = tt[: len(tt) - ini]
        nota = (np.sin(2 * np.pi * fr * tn) + 0.25 * np.sin(2 * np.pi * fr * 2 * tn)) * env(len(tn), 0.004, 0.18 if i < 2 else 0.5)
        out[ini:] += nota
    ini = int(SR * 0.22)
    out[ini:] += anilha[: len(tt) - ini] * 0.25 / np.max(np.abs(anilha))
    salvar_wav("08_assinatura_final", out, estereo_largura=0.5)


# ---------------------------------------------------------------- Overlays
def fonte(nome, tam):
    return ImageFont.truetype(os.path.join(AQUI, "fontes", nome), tam)


def selo_dia(dia, total=30):
    """Selo "DIA 07/30" com a barrinha de progresso, igual ao card da série no site.
    PNG transparente 1080x1920; o selo fica no canto superior esquerdo, fora da área da interface do Reels."""
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x, y, w, h = 60, 250, 520, 168
    d.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=NAVY + (235,), outline=(30, 58, 102, 255), width=3)
    d.text((x + 32, y + 26), "SÉRIE 30 DIAS", font=fonte("JetBrainsMono-Bold.ttf", 26), fill=BRANCO + (200,))
    d.text((x + 32, y + 58), f"DIA {dia:02d}", font=fonte("Archivo-ExpandedBlack.ttf", 64), fill=BRANCO + (255,))
    num = f"/{total}"
    d.text((x + w - 32, y + 116), num, font=fonte("JetBrainsMono-Bold.ttf", 34), fill=AZUL_CLARO + (255,), anchor="rs")
    # ticks
    tx, ty, gap = x + 32, y + 136, 4
    tw = (w - 64 - gap * (total - 1)) / total
    for i in range(total):
        cor = AZUL_CLARO + (255,) if i < dia else (45, 61, 88, 255)  # navy clareado, opaco
        d.rounded_rectangle((tx + i * (tw + gap), ty, tx + i * (tw + gap) + tw, ty + 10), radius=2, fill=cor)
    return img


def tarja_cupom(marca, linha):
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x, y, w, h = 90, 1260, 900, 200
    d.rounded_rectangle((x, y, x + w, y + h), radius=32, fill=NAVY + (240,), outline=(30, 58, 102, 255), width=3)
    d.text((x + 40, y + 38), marca.upper(), font=fonte("Archivo-ExpandedBlack.ttf", 48), fill=BRANCO + (255,))
    d.text((x + 40, y + 108), linha, font=fonte("Archivo-SemiBold.ttf", 34), fill=(128, 145, 171, 255))
    cx, cy = x + w - 40, y + h / 2
    f = fonte("JetBrainsMono-Bold.ttf", 54)
    bw = d.textlength("ODUDU", font=f) + 56
    d.rounded_rectangle((cx - bw, cy - 50, cx, cy + 50), radius=16, outline=AZUL_CLARO + (255,), width=4)
    d.text((cx - bw / 2, cy), "ODUDU", font=f, fill=AZUL_CLARO + (255,), anchor="mm")
    d.text((cx - bw / 2, cy - 62), "CUPOM", font=fonte("JetBrainsMono-Bold.ttf", 22), fill=AZUL_CLARO + (255,), anchor="ms")
    return img


def cartao_final():
    img = Image.new("RGBA", (1080, 1920), NAVY_FUNDO + (255,))
    # brilho navy no canto, como no site
    yy, xx = np.mgrid[0:1920, 0:1080]
    dist = np.sqrt((xx / 1080) ** 2 + (yy / 1920 / 0.6) ** 2)
    brilho = np.clip(1 - dist / 0.9, 0, 1)[..., None]
    base = np.array(NAVY_FUNDO) * (1 - brilho) + np.array(NAVY_2) * brilho
    img = Image.fromarray(np.dstack([base, np.full((1920, 1080, 1), 255)]).astype("uint8"), "RGBA")
    d = ImageDraw.Draw(img)
    try:
        foto = Image.open(os.path.join(AQUI, "..", "foto.jpg")).convert("RGB").resize((360, 360))
        m = Image.new("L", (360, 360), 0)
        ImageDraw.Draw(m).ellipse((0, 0, 359, 359), fill=255)
        d.ellipse((360 - 10, 640 - 10, 720 + 10, 1000 + 10), outline=AZUL_CLARO, width=6)
        img.paste(foto, (360, 640), m)
    except FileNotFoundError:
        pass
    d.text((540, 1110), "@oduduslv", font=fonte("Archivo-ExpandedBlack.ttf", 92), fill=BRANCO, anchor="mm")
    d.text((540, 1200), "MUSCULAÇÃO · CORRIDA · MENTE", font=fonte("JetBrainsMono-Bold.ttf", 32), fill=AZUL_CLARO, anchor="mm")
    d.rounded_rectangle((220, 1300, 860, 1404), radius=52, fill=AZUL_BOTAO)
    d.text((540, 1350), "SEGUE PRA VER O DIA SEGUINTE", font=fonte("Archivo-Bold.ttf", 34), fill=(255, 255, 255), anchor="mm")
    return img


def zona_segura():
    """Guia (NÃO exportar no vídeo): mostra onde a interface do Reels/TikTok cobre a tela."""
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    vermelho = (255, 60, 60, 90)
    d.rectangle((0, 0, 1080, 220), fill=vermelho)          # topo: nome/abas
    d.rectangle((0, 1920 - 420, 1080, 1920), fill=vermelho)  # baixo: legenda/música
    d.rectangle((1080 - 140, 700, 1080, 1500), fill=vermelho)  # direita: botões
    f = fonte("JetBrainsMono-Bold.ttf", 30)
    d.text((540, 110), "INTERFACE (evitar texto)", font=f, fill=(255, 255, 255, 220), anchor="mm")
    d.text((540, 1920 - 210), "INTERFACE (evitar texto)", font=f, fill=(255, 255, 255, 220), anchor="mm")
    d.rectangle((60, 220, 1080 - 140, 1920 - 420), outline=(127, 168, 238, 200), width=4)
    d.text((80, 240), "ÁREA SEGURA", font=f, fill=(127, 168, 238, 230))
    return img


def gerar_overlays():
    for dia in range(1, 31):
        selo_dia(dia).save(os.path.join(AQUI, "overlays", "dia", f"dia_{dia:02d}.png"))
    tarja_cupom("Dark Lab", "Suplementos que eu uso").save(os.path.join(AQUI, "overlays", "cupom_darklab.png"))
    tarja_cupom("Alpha Co.", "Roupas do meu dia a dia").save(os.path.join(AQUI, "overlays", "cupom_alphaco.png"))
    cartao_final().convert("RGB").save(os.path.join(AQUI, "overlays", "cartao_final.png"))
    zona_segura().save(os.path.join(AQUI, "overlays", "GUIA_zona_segura_nao_exportar.png"))


if __name__ == "__main__":
    for nome, receita in RECEITAS.items():
        print("LUT", escrever_cube(nome, receita))
    gerar_sons()
    print("sons ok")
    gerar_overlays()
    print("overlays ok")
