# Kit de edição @oduduslv — guia de uso no CapCut

Tudo aqui usa a mesma identidade do seu link na bio e do media kit:
**azul quase preto (navy) + azul claro de acento + letra Archivo larga e pesada + números em fonte "mono"**.
A ideia é que qualquer vídeo seu seja reconhecido em 1 segundo, mesmo sem ver o @.

```
kit-edicao/
├── luts/        5 filtros de cor (.cube)
├── sons/        8 efeitos sonoros (.wav, 48 kHz)
├── fontes/      5 fontes da marca (.ttf, uso comercial liberado)
├── overlays/    selos DIA 01–30, tarjas de cupom, cartão final, guia de zona segura (.png)
├── previews/    imagens de antes/depois para você comparar
└── gerar_kit.py o "código-fonte" de tudo (para eu ajustar e gerar de novo)
```

---

## 1. Paleta (copie os códigos no seletor de cor do CapCut)

| Uso | Cor | Código |
|---|---|---|
| Fundo / contorno das letras | navy escuro | `#060D1A` |
| Caixas e tarjas | navy | `#0A1A33` |
| **Acento** (palavra destacada, números, selo) | azul claro | `#7FA8EE` |
| Botão / chamada para ação | azul forte | `#2F6FE4` |
| Texto principal | branco | `#FFFFFF` |

Regra: **no máximo 1 palavra em azul por frase**. Se tudo é destaque, nada é.

---

## 2. LUTs (filtro de cor)

Veja `previews/comparativo_luts.jpg` para o antes/depois em capas suas.

| Arquivo | Quando usar |
|---|---|
| `ODUDU_01_Base` | **Padrão.** Fala pra câmera, rotina, casa. Se estiver em dúvida, é esse. |
| `ODUDU_02_Shape` | Pose, antes/depois, atualização da série. Mais contraste, pele mais dourada, marca mais a definição. |
| `ODUDU_03_Academia` | Treino com luz branca/LED que deixa a imagem esverdeada. Esfria e limpa. |
| `ODUDU_04_Corrida` | Externa com sol. Céu mais azul, sol mais quente. |
| `ODUDU_05_Mente` | Vídeo calmo, reflexão, "mente no lugar". Mais apagado e frio. |

**Como importar (CapCut no computador):**
1. Selecione o clipe → painel **Ajustar** → **LUT** → **Importar LUT** → escolha o `.cube`.
2. Comece com a **intensidade em 70–80%**. Em vídeo muito escuro, baixe para 50%.
3. Corrija **exposição primeiro**, LUT depois. LUT não conserta vídeo estourado ou escuro demais.
4. Aplique a LUT numa **camada de ajuste** que cobre o vídeo inteiro, assim todos os cortes ficam iguais.

**No celular:** pela minha última informação, o app do CapCut não importa arquivo `.cube`
(confira na sua versão: Ajustar → procure "LUT"). Se não tiver, há dois caminhos:
- editar a cor no computador; ou
- usar os valores aproximados abaixo em **Ajustar** e salvar o projeto como modelo (seção 6).
  Eles chegam perto da `01_Base`, não ficam idênticos:

| Ajuste | Base | Shape |
|---|---|---|
| Contraste | +12 | +22 |
| Saturação | −10 | −15 |
| Temperatura | −5 | 0 |
| Matiz (tint) | +3 | +3 |
| Sombras | −5 | −12 |
| Realces | −8 | −8 |
| Desbotar / Fade | +4 | +2 |

---

## 3. Fontes

Instale as 5 fontes da pasta `fontes/` (no computador: duplo clique → **Instalar**; depois feche e abra o CapCut).
No celular, o CapCut costuma ter **Texto → Fonte → importar** (ícone de pasta); envie os `.ttf` para o celular antes.

| Fonte | Para quê |
|---|---|
| **Archivo Expanded Black** | Títulos, gancho, legenda falada |
| Archivo Expanded ExtraBold | Subtítulo, segunda linha do título |
| Archivo Bold / SemiBold | Textos pequenos, explicação embaixo de um número |
| **JetBrains Mono Bold** | Números: tempo, carga, peso, "DIA 07/30", cupom |

---

## 4. Os 3 estilos de texto (veja `previews/estilos_legenda.jpg`)

Faça cada um uma vez, ajuste até gostar e **salve como predefinição/estilo** no painel de texto. Depois é só aplicar.

### 4.1 Título / gancho (primeiros 1–2 s)
- Fonte: Archivo Expanded Black, **MAIÚSCULAS**
- Cor: branco `#FFFFFF`, palavra principal em `#7FA8EE`
- Contorno: `#060D1A`, espessura média (≈ 10–15 no CapCut)
- Linha de cima (opcional): número em JetBrains Mono azul, ex.: `50 MIN`
- Posição: terço de cima da tela, mas abaixo da faixa vermelha do guia de zona segura
- Animação de entrada: **Zoom in / "Pop"** curto (0,2–0,3 s). Sem animação de saída.
- Som: `04_anilha_impacto_metalico` ou `05_impacto_grave` no frame em que o texto entra

### 4.2 Legenda falada (legenda automática)
- Gere com **Texto → Legendas automáticas**, depois aplique o estilo em todas de uma vez
- Fonte: Archivo Expanded Black, maiúsculas, **2–4 palavras por vez**, no máximo 2 linhas
- Cor: branco; **palavra-chave** em `#7FA8EE` (use o destaque de palavra/"karaokê" com essa cor, se a sua versão tiver)
- Contorno `#060D1A`, sem sombra
- Posição: ~62–68 % da altura da tela (logo acima da área da legenda do Reels)
- Animação: nenhuma ou "pop" bem sutil. Som `02_pop_legenda` **só** nas palavras-chave, não em todas

### 4.3 Número / resultado
- Fonte: JetBrains Mono Bold, grande, branco (ou azul se for O número do vídeo)
- Linha de explicação embaixo: Archivo Bold, menor, branco
- Etiqueta opcional: caixa `#7FA8EE` com texto `#060D1A` (ex.: `DIA 21 / 30`)
- Som: `05_impacto_grave` (resultado) ou `03_tick_contador` (contagem, repetições)

---

## 5. Efeitos sonoros

Importe os `.wav` como qualquer áudio (Áudio → Importar / Do dispositivo). Todos estão com pico em −1 dB.

| Arquivo | Quando | Volume sugerido |
|---|---|---|
| `01_whoosh_transicao` | Troca de cena/bloco. **Comece 0,3 s antes do corte.** | −14 dB |
| `02_pop_legenda` | Palavra-chave aparecendo | −18 dB |
| `03_tick_contador` | Selo DIA, contagem, repetições | −16 dB |
| `04_anilha_impacto_metalico` | Título entrando, "som da academia" da marca | −12 dB |
| `05_impacto_grave` | Revelação: resultado, "depois" | −10 dB |
| `06_riser_antes_depois` | Tensão antes do corte. **Termina exatamente no corte** (dura 2 s) | −14 dB |
| `07_ding_cupom` | Tarja de cupom aparecendo | −14 dB |
| `08_assinatura_final` | **Sempre** no cartão final. É a sua "vinheta". | −10 dB |

Mixagem padrão: **voz** perto de 0 dB, **música** de 18 a 22 dB abaixo da voz quando você fala
(pode subir quando não tem fala), **efeitos** pelos valores acima. Máximo de ~1 efeito a cada 2 s.

---

## 6. Overlays (PNG transparente, 1080×1920)

- `overlays/dia/dia_01.png` … `dia_30.png` — selo da **série 30 dias**, no mesmo visual do card do seu site.
  Coloque como sobreposição do início ao fim, sem redimensionar (já está na posição certa). Entrada + `03_tick_contador`.
- `overlays/cupom_darklab.png` e `cupom_alphaco.png` — tarja de cupom `ODUDU`, 3–4 s, com `07_ding_cupom`.
- `overlays/cartao_final.png` — tela final de 1,5 s com `08_assinatura_final`.
- `overlays/GUIA_zona_segura_nao_exportar.png` — **só para conferir**: coloque por cima enquanto edita,
  nenhum texto deve ficar na faixa vermelha (lá fica a interface do Reels/TikTok). **Apague antes de exportar.**

---

## 7. O segredo da padronização: um projeto-modelo

Em vez de montar tudo do zero a cada vídeo:

1. Crie um projeto chamado **`MODELO ODUDU`** em 9:16 com:
   camada de ajuste com `ODUDU_01_Base` (80 %) · um título de exemplo no estilo 4.1 ·
   uma legenda no estilo 4.2 · o selo `dia_01.png` · o `cartao_final.png` + `08_assinatura_final` no fim ·
   o guia de zona segura numa camada desligada.
2. A cada vídeo novo: **duplique o modelo**, troque os clipes, troque o selo do dia, troque os textos.

### Estrutura padrão de um vídeo da série

| Tempo | O que | Som |
|---|---|---|
| 0–1,5 s | Gancho (estilo 4.1) + selo DIA entrando | anilha + tick |
| 1,5 s → | Conteúdo com legenda falada (4.2) | pop nas palavras-chave, whoosh entre blocos |
| antes/depois | 2 s de riser → corte seco → número (4.3) | riser → impacto grave |
| quando citar | Tarja do cupom | ding |
| últimos 1,5 s | Cartão final | assinatura |

---

## 8. Quer mudar algo?

Tudo é gerado por `gerar_kit.py`. Me diga, por exemplo, "a LUT Shape ficou laranja demais",
"quero o selo maior", "a série agora é de 60 dias" ou "quero um som de whoosh mais grave",
que eu ajusto e gero de novo.
