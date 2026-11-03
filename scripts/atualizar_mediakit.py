"""Busca os números do @oduduslv na API do Instagram e grava o media kit.

Gera `mediakit/dados.json` e as capas dos melhores posts em `mediakit/capas/`.
Roda todo dia pelo GitHub Actions (com IG_ACCESS_TOKEN e IG_USER_ID nos secrets)
ou localmente, passando o caminho de um .env: python scripts/atualizar_mediakit.py caminho/.env

Usa só a biblioteca padrão do Python, e o token nunca é impresso.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "mediakit"
CAPAS = SAIDA / "capas"
VERSAO = "v23.0"
TOP_POSTS = 6
JANELA_POSTS_DIAS = 90


def carregar_env() -> tuple[str, str]:
    if len(sys.argv) > 1:
        for linha in pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.strip().startswith("#"):
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    user = os.environ.get("IG_USER_ID", "").strip()
    if not token or not user:
        sys.exit("Faltam IG_ACCESS_TOKEN e IG_USER_ID.")
    return token, user


TOKEN, USER = carregar_env()


def api(caminho: str, **params) -> dict:
    params = {k: v for k, v in params.items() if v is not None}
    params["access_token"] = TOKEN
    url = f"https://graph.facebook.com/{VERSAO}/{caminho}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"{caminho}: HTTP {e.code} {corpo[:300]}") from None


def total(metricas: str, since: int, until: int) -> dict[str, int]:
    dados = api(f"{USER}/insights", metric=metricas, period="day", metric_type="total_value", since=since, until=until)
    return {m["name"]: m.get("total_value", {}).get("value", 0) for m in dados.get("data", [])}


def demografia(quebra: str) -> list[dict]:
    dados = api(f"{USER}/insights", metric="follower_demographics", period="lifetime",
                metric_type="total_value", breakdown=quebra, timeframe="last_30_days")
    linhas = []
    for m in dados.get("data", []):
        for b in m.get("total_value", {}).get("breakdowns", []):
            for r in b.get("results", []):
                linhas.append({"chave": r["dimension_values"][0], "valor": r["value"]})
    soma = sum(l["valor"] for l in linhas) or 1
    for l in linhas:
        l["pct"] = round(100 * l["valor"] / soma, 1)
    return sorted(linhas, key=lambda l: -l["valor"])


def metricas_post(media: dict) -> dict:
    tipo = media.get("media_product_type")
    conjunto = "reach,views,likes,comments,shares,saved,total_interactions"
    if tipo == "REELS":
        conjunto += ",ig_reels_avg_watch_time"
    try:
        dados = api(f"{media['id']}/insights", metric=conjunto)
    except RuntimeError:
        dados = api(f"{media['id']}/insights", metric="reach,likes,comments,shares,saved,total_interactions")
    return {m["name"]: (m.get("values") or [{}])[0].get("value", 0) for m in dados.get("data", [])}


def baixar(url: str, destino: pathlib.Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as r:
        destino.write_bytes(r.read())


def main() -> None:
    agora = dt.datetime.now(dt.timezone.utc)
    ate = int(agora.timestamp())
    desde = int((agora - dt.timedelta(days=30)).timestamp())

    conta = api(USER, fields="username,followers_count,media_count")
    trinta = total("reach,views,accounts_engaged,total_interactions,likes,comments,shares,saves,profile_views", desde, ate)

    # Posts dos últimos 90 dias com as métricas de cada um
    limite = agora - dt.timedelta(days=JANELA_POSTS_DIAS)
    posts, prox = [], f"{USER}/media"
    params = {"fields": "id,caption,media_type,media_product_type,media_url,thumbnail_url,permalink,timestamp", "limit": 50}
    while prox:
        pagina = api(prox, **params)
        fim = False
        for m in pagina.get("data", []):
            quando = dt.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            if quando < limite:
                fim = True
                break
            m["metricas"] = metricas_post(m)
            posts.append(m)
        prox = None if fim or "next" not in pagina.get("paging", {}) else f"{USER}/media"
        params["after"] = pagina.get("paging", {}).get("cursors", {}).get("after")

    reels = [p for p in posts if p.get("media_product_type") == "REELS"]
    views_reels = [p["metricas"].get("views", 0) for p in reels]
    interacoes = [p["metricas"].get("total_interactions", 0) for p in posts]
    seguidores = conta["followers_count"] or 1

    melhores = sorted(posts, key=lambda p: -(p["metricas"].get("views") or p["metricas"].get("reach", 0)))[:TOP_POSTS]
    CAPAS.mkdir(parents=True, exist_ok=True)
    for velho in CAPAS.glob("*.jpg"):
        velho.unlink()
    top = []
    for i, p in enumerate(melhores, 1):
        url = p.get("thumbnail_url") or p.get("media_url")
        nome = f"{i}.jpg"
        if url:
            baixar(url, CAPAS / nome)
        legenda = (p.get("caption") or "").split("\n")[0].strip()
        top.append({
            "capa": f"capas/{nome}",
            "link": p["permalink"],
            "data": p["timestamp"][:10],
            "legenda": legenda[:90],
            "views": p["metricas"].get("views", 0),
            "alcance": p["metricas"].get("reach", 0),
            "curtidas": p["metricas"].get("likes", 0),
            "comentarios": p["metricas"].get("comments", 0),
            "compartilhamentos": p["metricas"].get("shares", 0),
            "salvamentos": p["metricas"].get("saved", 0),
        })

    dados = {
        "atualizado_em": agora.astimezone(dt.timezone(dt.timedelta(hours=-3))).strftime("%Y-%m-%d %H:%M"),
        "perfil": {"usuario": conta["username"], "seguidores": conta["followers_count"], "posts": conta["media_count"]},
        "ultimos_30_dias": {
            "alcance": trinta.get("reach", 0),
            "visualizacoes": trinta.get("views", 0),
            "contas_engajadas": trinta.get("accounts_engaged", 0),
            "interacoes": trinta.get("total_interactions", 0),
            "visitas_perfil": trinta.get("profile_views", 0),
            "compartilhamentos": trinta.get("shares", 0),
            "salvamentos": trinta.get("saves", 0),
        },
        "posts_90_dias": {
            "quantidade": len(posts),
            "mediana_views_reels": int(statistics.median(views_reels)) if views_reels else 0,
            "maior_views": max(views_reels) if views_reels else 0,
            "engajamento_medio_pct": round(100 * statistics.mean(interacoes) / seguidores, 2) if interacoes else 0,
        },
        "publico": {
            "genero": demografia("gender"),
            "idade": demografia("age"),
            "paises": demografia("country")[:5],
            "cidades": demografia("city")[:5],
        },
        "melhores_posts": top,
    }
    SAIDA.mkdir(exist_ok=True)
    (SAIDA / "dados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ok: {len(posts)} posts, {conta['followers_count']} seguidores, {len(top)} capas")


if __name__ == "__main__":
    main()
