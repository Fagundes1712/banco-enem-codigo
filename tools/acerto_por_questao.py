"""Porcentagem real de acerto de cada questão do banco, pelos microdados.

Uso: python3 tools/acerto_por_questao.py <ITENS_PROVA_<ano>.csv> <MICRODADOS_ENEM_<ano>.csv ou RESULTADOS_<ano>.csv> <saida.json>

Para cada área acha o caderno azul regular (gabarito igual ao do banco),
conta, entre os participantes desse caderno com nota, quantos marcaram o
gabarito em cada posição e grava {id da questão: % de acerto}. Serve para
dar nível de dificuldade a questões sem parâmetro TRI oficial
(tools/microdados.py, docs/dificuldade.md).
"""
import csv
import json
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent.parent
qs = json.loads((root / "questions.json").read_text(encoding="utf-8"))
itens = list(csv.DictReader(open(sys.argv[1], encoding="latin-1"), delimiter=";"))
ano = int(pathlib.Path(sys.argv[1]).stem[-4:])
LANG = {"ingles": "0", "espanhol": "1"}

# Ordem das posições na string de respostas de cada caderno (e língua, em LC).
ordem, alvo = {}, {}
for area in ("CN", "CH", "LC", "MT"):
    banco = {(q["numero"], LANG.get(q.get("lang"), "")): q for q in qs if q["ano"] == ano and q["area"] == area}
    melhor, pontos = None, -1
    for cp in {r["CO_PROVA"] for r in itens if r["SG_AREA"] == area}:
        rs = [r for r in itens if r["CO_PROVA"] == cp]
        p = sum(1 for r in rs if (int(r["CO_POSICAO"]), r["TP_LINGUA"].strip() if area == "LC" else "") in banco
                and banco[(int(r["CO_POSICAO"]), r["TP_LINGUA"].strip() if area == "LC" else "")]["gab"] == r["TX_GABARITO"])
        if p > pontos:
            melhor, pontos = cp, p
    if pontos < 0.9 * len(banco):
        print(f"{ano} {area}: caderno não confere", file=sys.stderr)
        continue
    rs = sorted((r for r in itens if r["CO_PROVA"] == melhor), key=lambda r: int(r["CO_POSICAO"]))
    for lang in (("0", "1") if area == "LC" else ("",)):
        lista = [r for r in rs if r["TP_LINGUA"].strip() in ("", lang)]
        ordem[(melhor, lang)] = [banco.get((int(r["CO_POSICAO"]), r["TP_LINGUA"].strip())) for r in lista]
    alvo[area] = melhor

cont = {k: [0] * len(v) for k, v in ordem.items()}
total = {k: 0 for k in ordem}
rd = csv.reader(open(sys.argv[2], encoding="latin-1"), delimiter=";")
h = next(rd)
ix = {k: i for i, k in enumerate(h)}
for row in rd:
    for area, cp in alvo.items():
        if row[ix["CO_PROVA_" + area]] != cp or not row[ix["NU_NOTA_" + area]]:
            continue
        lang = row[ix["TP_LINGUA"]] if area == "LC" else ""
        k = (cp, lang)
        if k not in ordem:
            continue
        resp = row[ix["TX_RESPOSTAS_" + area]]
        total[k] += 1
        for i, q in enumerate(ordem[k]):
            if q and i < len(resp) and resp[i] == q["gab"]:
                cont[k][i] += 1

out = {}
for k, v in ordem.items():
    for i, q in enumerate(v):
        if q and total[k]:
            out[q["id"]] = round(100 * cont[k][i] / total[k], 1)
pathlib.Path(sys.argv[3]).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print(f"{ano}: {len(out)} questões, participantes por caderno {total}")
