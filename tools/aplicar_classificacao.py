"""Aplica tools/classificacao.json ao banco e valida a integridade.

Uso: python3 tools/aplicar_classificacao.py <questions.json de entrada> <saída>

classificacao.json: { "<id>": {"t": "<id do tópico>", "tags": [...], "rev": "motivo"} }
Cada questão recebe `materia` e `topico` derivados do tópico, `tags` quando
houver e `revisao` quando o caso foi marcado como ambíguo. Questão sem
classificação fica sem `topico` (aparece só no simulado aleatório).
"""
import json
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent.parent
tax = json.loads((root / "taxonomy.json").read_text(encoding="utf-8"))
TOP = {}
for a in tax["areas"]:
    for s in a["subjects"]:
        for t in s["topics"]:
            TOP[t["id"]] = (a["id"], s["id"])

cls = json.loads((root / "tools" / "classificacao.json").read_text(encoding="utf-8"))
qs = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
erros, sem = [], []
for q in qs:
    for k in ("materia", "topico", "tags", "revisao"):
        q.pop(k, None)
    c = cls.get(q["id"])
    if not c:
        sem.append(q["id"])
        continue
    t = c["t"]
    if t not in TOP:
        erros.append(f"{q['id']}: tópico inexistente {t}")
        continue
    area, mat = TOP[t]
    if area != q["area"]:
        erros.append(f"{q['id']}: tópico {t} é de outra área ({area})")
        continue
    q["materia"], q["topico"] = mat, t
    tags = [x for x in c.get("tags", []) if x != t]
    bad = [x for x in tags if x not in TOP]
    if bad:
        erros.append(f"{q['id']}: tags inexistentes {bad}")
    if tags:
        q["tags"] = tags
    if c.get("rev"):
        q["revisao"] = c["rev"]

if erros:
    print("\n".join(erros), file=sys.stderr)
    sys.exit(1)
pathlib.Path(sys.argv[2]).write_text(json.dumps(qs, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"{len(qs)} questões; {len(qs) - len(sem)} classificadas; {len(sem)} sem classificação;",
      sum(1 for q in qs if q.get("revisao")), "para revisão")
