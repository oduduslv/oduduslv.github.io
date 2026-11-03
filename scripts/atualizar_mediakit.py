"""Busca os números do @oduduslv na API do Instagram e grava o media kit.

Gera `mediakit/dados.json`, as capas das postagens recentes em `mediakit/capas/`
e mantém `mediakit/stories.json`, o histórico dos stories (a API só mostra os
números de um story enquanto ele está no ar, então cada execução guarda o que vê).

Roda a cada 6 horas pelo GitHub Actions (com IG_ACCESS_TOKEN e IG_USER_ID nos secrets)
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
HISTORICO_STORIES = SAIDA / "stories.json"
VERSAO = "v23.0"
RECENTES = 10
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
    """Lista de {chave, valor, pct}; com quebra "age,gender" a chave vira "idade|genero"."""
    dados = api(f"{USER}/insights", metric="follower_demographics", period="lifetime",
                metric_type="total_value", breakdown=quebra, timeframe="last_30_days")
    linhas = []
    for m in dados.get("data", []):
        for b in m.get("total_value", {}).get("breakdowns", []):
            for r in b.get("results", []):
                linhas.append({"chave": "|".join(r["dimension_values"]), "valor": r["value"]})
    soma = sum(l["valor"] for l in linhas) or 1
    for l in linhas:
        l["pct"] = round(100 * l["valor"] / soma, 1)
    return sorted(linhas, key=lambda l: -l["valor"])


def idade_por_genero() -> dict[str, list[dict]]:
    por = {}
    for l in demografia("age,gender"):
        idade, genero = l["chave"].split("|")
        por.setdefault(genero, []).append({"chave": idade, "valor": l["valor"]})
    for genero, itens in por.items():
        soma = sum(i["valor"] for i in itens) or 1
        for i in itens:
            i["pct"] = round(100 * i["valor"] / soma, 1)
        itens.sort(key=lambda i: i["chave"])
    return por


def metricas_post(media: dict) -> dict:
    conjunto = "reach,views,likes,comments,shares,saved,total_interactions"
    if media.get("media_product_type") == "REELS":
        conjunto += ",ig_reels_avg_watch_time,ig_reels_video_view_total_time"
    try:
        dados = api(f"{media['id']}/insights", metric=conjunto)
    except RuntimeError:
        dados = api(f"{media['id']}/insights", metric="reach,likes,comments,shares,saved,total_interactions")
    return {m["name"]: (m.get("values") or [{}])[0].get("value", 0) for m in dados.get("data", [])}


def baixar(url: str, destino: pathlib.Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as r:
        destino.write_bytes(r.read())


def media(valores: list[float]) -> float:
    return statistics.mean(valores) if valores else 0


def atualizar_stories(agora: dt.datetime) -> dict:
    historico = json.loads(HISTORICO_STORIES.read_text(encoding="utf-8")) if HISTORICO_STORIES.exists() else {}
    for s in api(f"{USER}/stories", fields="id,timestamp").get("data", []):
        try:
            m = {x["name"]: (x.get("values") or [{}])[0].get("value", 0)
                 for x in api(f"{s['id']}/insights", metric="reach,views").get("data", [])}
        except RuntimeError:
            continue
        antigo = historico.get(s["id"], {})
        historico[s["id"]] = {
            "data": s["timestamp"][:10],
            "views": max(m.get("views", 0), antigo.get("views", 0)),
            "alcance": max(m.get("reach", 0), antigo.get("alcance", 0)),
        }
    corte = (agora - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    historico = {k: v for k, v in historico.items() if v["data"] >= corte}
    HISTORICO_STORIES.write_text(json.dumps(historico, indent=1), encoding="utf-8")
    views = [v["views"] for v in historico.values()]
    return {
        "quantidade": len(views),
        "media_views": int(media(views)),
        "media_alcance": int(media([v["alcance"] for v in historico.values()])),
        "desde": min((v["data"] for v in historico.values()), default=None),
    }


def main() -> None:
    agora = dt.datetime.now(dt.timezone.utc)
    ate = int(agora.timestamp())
    desde = int((agora - dt.timedelta(days=30)).timestamp())

    conta = api(USER, fields="username,followers_count,media_count")
    trinta = total("reach,views,accounts_engaged,total_interactions,likes,comments,shares,saves,"
                   "profile_views,website_clicks", desde, ate)

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
            m["quando"] = quando
            m["metricas"] = metricas_post(m)
            posts.append(m)
        prox = None if fim or "next" not in pagina.get("paging", {}) else f"{USER}/media"
        params["after"] = pagina.get("paging", {}).get("cursors", {}).get("after")

    # Médias com os posts dos últimos 30 dias; se não houver, usa os 90 dias
    corte30 = agora - dt.timedelta(days=30)
    base = [p for p in posts if p["quando"] >= corte30] or posts
    reels = [p for p in base if p.get("media_product_type") == "REELS"]
    seguidores = conta["followers_count"] or 1
    interacoes = [p["metricas"].get("total_interactions", 0) for p in base]

    CAPAS.mkdir(parents=True, exist_ok=True)
    for velho in CAPAS.glob("*.jpg"):
        velho.unlink()
    recentes = []
    for i, p in enumerate(posts[:RECENTES], 1):
        url = p.get("thumbnail_url") or p.get("media_url")
        nome = f"{i}.jpg"
        if url:
            baixar(url, CAPAS / nome)
        recentes.append({
            "capa": f"capas/{nome}",
            "link": p["permalink"],
            "data": p["timestamp"][:10],
            "legenda": (p.get("caption") or "").split("\n")[0].strip()[:90],
            "views": p["metricas"].get("views") or p["metricas"].get("reach", 0),
            "curtidas": p["metricas"].get("likes", 0),
            "comentarios": p["metricas"].get("comments", 0),
        })

    dados = {
        "atualizado_em": agora.astimezone(dt.timezone(dt.timedelta(hours=-3))).strftime("%Y-%m-%d %H:%M"),
        "perfil": {"usuario": conta["username"], "seguidores": conta["followers_count"], "posts": conta["media_count"]},
        "resumo": {
            "seguidores": conta["followers_count"],
            "engajamento_pct": round(100 * media(interacoes) / seguidores, 2),
            "alcance": trinta.get("reach", 0),
            "contas_engajadas": trinta.get("accounts_engaged", 0),
            "cliques_link": trinta.get("website_clicks", 0),
            "salvamentos": trinta.get("saves", 0),
            "publicacoes": conta["media_count"],
            "visualizacoes": trinta.get("views", 0),
            "interacoes": trinta.get("total_interactions", 0),
            "visitas_perfil": trinta.get("profile_views", 0),
            "media_curtidas": int(media([p["metricas"].get("likes", 0) for p in base])),
            "media_comentarios": int(media([p["metricas"].get("comments", 0) for p in base])),
            "posts_na_base": len(base),
        },
        "reels": {
            "quantidade": len(reels),
            "media_views": int(media([p["metricas"].get("views", 0) for p in reels])),
            "tempo_medio_s": round(media([p["metricas"].get("ig_reels_avg_watch_time", 0) for p in reels]) / 1000, 1),
            "tempo_total_h": round(sum(p["metricas"].get("ig_reels_video_view_total_time", 0) for p in reels) / 3.6e6),
        },
        "stories": atualizar_stories(agora),
        "publico": {
            "genero": demografia("gender"),
            "idade": sorted(demografia("age"), key=lambda l: l["chave"]),
            "idade_por_genero": idade_por_genero(),
            "paises": demografia("country")[:6],
            "cidades": demografia("city")[:6],
        },
        "recentes": recentes,
    }
    SAIDA.mkdir(exist_ok=True)
    (SAIDA / "dados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ok: {len(posts)} posts, {conta['followers_count']} seguidores, "
          f"{len(recentes)} capas, {dados['stories']['quantidade']} stories no histórico")


if __name__ == "__main__":
    main()
