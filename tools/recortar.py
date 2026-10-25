"""Recorta como imagem as questões que o extrator não conseguiu ler por inteiro.

Uso: python3 tools/recortar.py <pasta das provas> <pasta de saída do extrair.py>

Lê <saída>/questions.raw.json e <saída>/extracao.log.json. Para cada questão
com aviso grave (alternativa faltando ou vazia, enunciado vazio, caractere não
reconhecido), troca o texto pela imagem fiel da prova, recortada do cabeçalho
"QUESTÃO N" até o cabeçalho da questão seguinte, coluna por coluna. As
alternativas ficam como letras, com o texto lido na imagem. A questão recebe
`recorte: true` para ir à revisão.
"""
import json
import pathlib
import re
import sys

import pymupdf

ZOOM = 1.6
HEAD = re.compile(r"^\s*QUEST[ÃA]O\s+(\d{1,3})\s*$", re.I)
GRAVE = re.compile(r"alternativas encontradas|alternativa vazia|enunciado vazio|não reconhecidos")


def heads(doc):
    out = []
    for pno in range(doc.page_count):
        page = doc[pno]
        mid = page.rect.width / 2
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                t = "".join(s["text"] for s in l["spans"])
                m = HEAD.match(t)
                if m:
                    r = pymupdf.Rect(l["bbox"])
                    out.append((pno, 0 if r.x0 < mid - 8 else 1, r.y0, int(m.group(1))))
    return sorted(out)


SECAO = re.compile(r"E SUAS TECNOLOGIAS|Quest[õo]es de \d+ a \d+|^\s*\d{1,3}\s*$|AZUL|enem\s*20\d\d|^ENEM", re.I)


def conteudo(page, y0, y1, c):
    """União do que está impresso na coluna c entre y0 e y1 (o que nasce na
    coluna e transborda para a outra entra junto), sem rodapé nem cabeçalho."""
    W, H = page.rect.width, page.rect.height
    mid = W / 2
    na_coluna = lambda r: (r.x0 < mid - 8) if c == 0 else (r.x0 >= mid - 8)
    rs = []
    for b in page.get_text("dict")["blocks"]:
        r = pymupdf.Rect(b["bbox"])
        if r.y1 <= y0 or r.y0 >= y1 or r.y1 > H - 28 or not na_coluna(r):
            continue
        if b["type"] == 0:
            t = " ".join(s["text"] for l in b["lines"] for s in l["spans"]).strip()
            if not t or SECAO.search(t):
                continue
        rs.append(r)
    for d in page.get_drawings():
        r = pymupdf.Rect(d["rect"])
        if r.y1 <= y0 or r.y0 >= y1 or r.y1 > H - 40 or not na_coluna(r) or r.width > W * 0.9:
            continue
        if r.height < 3 and r.width > 60:
            continue  # fios decorativos de seção e de cabeçalho
        rs.append(r)
    # Cabeçalho da página (logotipo, código de barras) e faixa lateral ficam fora.
    rs = [r for r in rs if r.y1 > 75 and not (r.width < 40 and (r.x0 < 30 or r.x1 > W - 30))]
    if not rs:
        return None
    u = rs[0]
    for r in rs[1:]:
        u |= r
    u = (u + (-3, -3, 3, 3)) & pymupdf.Rect(0, y0, W, y1)
    if c == 0 and u.x1 > mid + 5 and any(h[0] == page.number and h[1] == 1 and u.y0 < h[2] < u.y1 for h in HS):
        u.x1 = mid - 2  # outra questão na coluna direita: não invade
    txt = page.get_text("text", clip=u).strip()
    if len(txt) < 12 and u.height < 60:
        return None
    return u


HS = []


def cortes(doc, hs, k):
    HS[:] = hs
    p, c, y, _ = hs[k]
    y -= 1
    fim = hs[k + 1] if k + 1 < len(hs) else (p, 1, doc[p].rect.height - 30, 0)
    segs = []
    while (p, c) <= fim[:2]:
        page = doc[p]
        H = page.rect.height
        y1 = fim[2] - 2 if (p, c) == fim[:2] else H - 28
        u = conteudo(page, y, y1, c)
        if u and u.height > 12 and not re.search(r"PROPOSTA DE REDA", page.get_text("text", clip=u)):
            segs.append((p, u))
        largo = c == 0 and u is not None and u.x1 > page.rect.width / 2 + 20
        p, c = (p, 1) if c == 0 else (p + 1, 0)
        y = u.y1 if largo else 40  # recorte em largura total já cobriu a coluna direita
        if p >= doc.page_count:
            break
    return segs


def palavras(t):
    return re.findall(r"[a-zà-ú]{4,}", re.sub(r"!\[.*?\]\(.*?\)", "", t).lower())


def confere(q, impresso):
    """O texto extraído bate com o impresso? Aceita texto-base impresso antes
    do cabeçalho (todas as palavras da prova extraídas e alternativas limpas)."""
    imp = set(palavras(impresso))
    if not imp:
        return False
    frac = lambda ws, ref: sum(w in ref for w in ws) / len(ws) if ws else 1
    ext = palavras(q["enunciado"] + " " + " ".join(q["alts"].values()))
    alts = palavras(" ".join(q["alts"].values()))
    if ext and frac(ext, imp) >= 0.75:
        return True
    return frac(list(imp), set(ext)) >= 0.9 and frac(alts, imp) >= 0.9


def main(src, outdir):
    src, outdir = pathlib.Path(src), pathlib.Path(outdir)
    qs = json.loads((outdir / "questions.raw.json").read_text(encoding="utf-8"))
    log = json.loads((outdir / "extracao.log.json").read_text(encoding="utf-8"))
    alvo = {x["id"] for x in log if any(GRAVE.search(a) for a in x["avisos"])}
    for q in qs:
        n = sorted(len(v) for v in q["alts"].values())
        if len(n) == 5 and n[-1] > 200 and n[-1] > 4 * max(n[1], 20):
            alvo.add(q["id"])  # alternativa engoliu o texto da questão seguinte
    docs, feitos, divergentes = {}, [], []
    for q in qs:
        if q.get("lang"):
            continue
        key = (q["ano"], q["dia"])
        if key not in docs:
            doc = pymupdf.open(src / str(q["ano"]) / f"{q['ano']}-dia-{q['dia']}-prova.pdf")
            docs[key] = (doc, heads(doc))
        doc, hs = docs[key]
        ks = [i for i, h in enumerate(hs) if h[3] == q["numero"]]
        if not ks:
            continue
        if q["id"] not in alvo:
            # Confere o texto extraído com o texto impresso entre os cabeçalhos
            # (em 2021 a camada de texto do PDF é cifrada e não serve de régua).
            texto = lambda k: " ".join(doc[p].get_text("text", clip=r) for p, r in cortes(doc, hs, k))
            if q["ano"] == 2021 or confere(q, texto(ks[0])):
                continue
            imp = palavras(texto(ks[0]))
            ext = set(palavras(q["enunciado"] + " " + " ".join(q["alts"].values())))
            lista = palavras(q["enunciado"] + " " + " ".join(q["alts"].values()))
            achadas = sum(w in set(imp) for w in lista) / max(len(lista), 1)
            if imp and (sum(w in ext for w in imp) / len(imp) >= 0.9 or achadas >= 0.6):
                # O recorte é que ficou curto ou pegou figura vizinha: a maior
                # parte do texto extraído está impressa sob este número.
                continue
            divergentes.append(q["id"])
        for f in (outdir / "img").glob(q["id"] + "-*.jpg"):
            f.unlink()
        ims = []
        for n, (p, r) in enumerate(cortes(doc, hs, ks[0]), 1):
            name = f"{q['id']}-p{n}.jpg"
            doc[p].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), clip=r).save(str(outdir / "img" / name), jpg_quality=80)
            ims.append(f"![Questão {q['numero']} da prova, parte {n}](img/{name})")
        q["enunciado"] = "Questão reproduzida como imagem da prova oficial.\n\n" + "\n\n".join(ims)
        q["alts"] = {k: f"Alternativa {k} (ver imagem)" for k in "ABCDE"}
        q["recorte"] = True
        feitos.append(q["id"])
    (outdir / "questions.raw.json").write_text(json.dumps(qs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(feitos), "questões recortadas como imagem:", " ".join(feitos), file=sys.stderr)
    print("texto diferente do impresso:", " ".join(divergentes), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
