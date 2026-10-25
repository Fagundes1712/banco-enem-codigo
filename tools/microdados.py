"""Grava os parâmetros TRI oficiais e o nível de dificuldade em questions.json.

Uso: python3 tools/microdados.py <pasta com ITENS_PROVA_<ano>.csv>

Os arquivos vêm da pasta DADOS dos microdados do Enem (INEP). Para cada ano
e área, o script acha o caderno azul da aplicação regular comparando o
gabarito oficial posição a posição com o banco, e copia NU_PARAM_A, _B e _C
de cada item para `a`, `b` e `c`. Item sem parâmetro (anulado ou
abandonado pelo INEP) fica sem nada. Nada é estimado aqui: o nível de
dificuldade é o quintil do parâmetro b oficial dentro da área, contando
todas as questões do banco que têm parâmetro (1 = 20% mais fáceis da área,
5 = 20% mais difíceis). Ver docs/dificuldade.md.

Questão sem parâmetro (item abandonado pelo INEP) recebe o nível pela
porcentagem real de acerto (tools/acerto/<ano>.json, gerado por
tools/acerto_por_questao.py): a mediana do nível das 10 questões da área
com parâmetro e acerto mais parecido. Ela fica marcada com nivel_por = "acerto".
"""
import csv
import json
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parent.parent

def ler(arq):
    raw = arq.read_bytes()
    for enc in ("utf-8-sig", "latin-1"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    sep = ";" if txt.count(";") > txt.count(",") else ","
    return list(csv.DictReader(txt.splitlines(), delimiter=sep))


def num(x):
    try:
        return float(str(x).replace(",", "."))
    except ValueError:
        return None


qs = json.loads((root / "questions.json").read_text(encoding="utf-8"))
for q in qs:
    q.pop("nivel", None)
    q.pop("nivel_por", None)
banco = {}
for q in qs:
    banco.setdefault((q["ano"], q["area"]), []).append(q)

pasta = pathlib.Path(sys.argv[1])
gravados, sem = 0, []
for arq in sorted(pasta.glob("*.csv")):
    m = re.search(r"ITENS_PROVA_(\d{4})", arq.name, re.I)
    if not m:
        continue
    ano = int(m.group(1))
    provas = {}
    for r in ler(arq):
        provas.setdefault(r["CO_PROVA"], []).append(r)
    for area in ("CN", "CH", "LC", "MT"):
        alvo = banco.get((ano, area), [])
        if not alvo:
            continue
        # Posição relativa: em 2016 e 2017 o CO_POSICAO não segue a numeração do caderno.
        base = min(q["numero"] for q in alvo)
        chave = lambda q: (q["numero"] - base, {"ingles": "0", "espanhol": "1"}.get(q.get("lang"), ""))
        gab = {chave(q): q["gab"] for q in alvo}

        def itens(rs):
            out, ini = {}, min(int(r["CO_POSICAO"]) for r in rs)
            for r in rs:
                lang = r.get("TP_LINGUA", "").strip() if area == "LC" else ""
                if lang not in ("0", "1"):
                    lang = ""
                p = int(r["CO_POSICAO"]) - ini
                # 2017: Linguagens numerada de 1 a 50, com o espanhol em 6 a 10.
                if len(rs) == 50 and max(int(x["CO_POSICAO"]) for x in rs) - ini == 49 and lang != "0":
                    p -= 5
                out[(p, lang)] = r
            return out

        melhor, pontos = None, -1
        for cod, rs in provas.items():
            if rs[0]["SG_AREA"] != area or "AZUL" not in rs[0].get("TX_COR", "").upper():
                continue
            it = itens(rs)
            p = sum(1 for k, g in gab.items() if k in it and it[k]["TX_GABARITO"].strip() == g)
            if p > pontos:
                melhor, pontos = it, p
        if not melhor or pontos < 0.9 * len(gab):
            sem.append(f"{ano} {area}: caderno azul não confere ({pontos}/{len(gab)})")
            continue
        for q in alvo:
            for k in ("a", "b", "c"):
                q.pop(k, None)
            r = melhor.get(chave(q))
            a, b, c = (num(r[k]) for k in ("NU_PARAM_A", "NU_PARAM_B", "NU_PARAM_C")) if r else (None,) * 3
            if None in (a, b, c):
                continue
            q["a"], q["b"], q["c"] = round(a, 5), round(b, 5), round(c, 5)
            gravados += 1

# Nível: quintil de b na área, com as questões de todos os anos que têm parâmetro.
for area in ("CN", "CH", "LC", "MT"):
    com = sorted((q for q in qs if q["area"] == area and "b" in q), key=lambda q: q["b"])
    for i, q in enumerate(com):
        q["nivel"] = 1 + (5 * i) // len(com)

# Sem parâmetro: nível pelos vizinhos de mesma porcentagem de acerto.
acerto = {}
for arq in (root / "tools" / "acerto").glob("*.json"):
    acerto.update(json.loads(arq.read_text(encoding="utf-8")))
for q in qs:
    if "nivel" in q or q.get("anulada") or q["id"] not in acerto:
        continue
    viz = sorted(
        (x for x in qs if x["area"] == q["area"] and "b" in x and x["id"] in acerto),
        key=lambda x: abs(acerto[x["id"]] - acerto[q["id"]]),
    )[:10]
    if viz:
        q["nivel"] = sorted(x["nivel"] for x in viz)[len(viz) // 2]
        q["nivel_por"] = "acerto"

if sem:
    print("\n".join(sem), file=sys.stderr)
(root / "questions.json").write_bytes(
    json.dumps(qs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
)
print(f"{gravados} de {len(qs)} questões com parâmetros oficiais")
