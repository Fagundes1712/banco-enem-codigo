"""Nota oficial mediana por número de acertos numa prova do Enem.

Uso: python3 tools/nota_por_acertos.py <MICRODADOS_ENEM_<ano>.csv ou RESULTADOS_<ano>.csv> <saida.json>

Gera, para cada área, [acertos, participantes, mediana, p10, p90] de 0 a 45.
A tabela NOTA_ACERTOS de js/simulado.js é a média dessas medianas entre os
anos (docs/dificuldade.md).
"""
import csv, json, sys
f = open(sys.argv[1], encoding="latin-1")
rd = csv.reader(f, delimiter=";")
h = next(rd); ix = {k: i for i, k in enumerate(h)}
notas = {a: [[] for _ in range(46)] for a in ("CN", "CH", "LC", "MT")}
for row in rd:
    for a in notas:
        n = row[ix["NU_NOTA_" + a]]
        if not n or float(n) <= 0:
            continue
        r, g = row[ix["TX_RESPOSTAS_" + a]], row[ix["TX_GABARITO_" + a]]
        if a == "LC" and len(g) == 50:
            # Gabarito: 5 de inglês, 5 de espanhol e as 40 comuns; resposta tem 45.
            g = (g[:5] if row[ix["TP_LINGUA"]] == "0" else g[5:10]) + g[10:]
        k = sum(1 for x, y in zip(r, g) if x == y and x not in ".*")
        if k <= 45:
            notas[a][k].append(float(n))
out = {}
for a, l in notas.items():
    t = []
    for k, v in enumerate(l):
        v.sort()
        t.append([k, len(v), round(v[len(v) // 2], 1) if v else None, round(v[len(v) // 10], 1) if v else None, round(v[(9 * len(v)) // 10], 1) if v else None])
    out[a] = t
json.dump(out, open(sys.argv[2], "w"))
for a, t in out.items():
    print(a, " ".join(f"{k}:{m}" for k, n, m, lo, hi in t if k % 5 == 0))
