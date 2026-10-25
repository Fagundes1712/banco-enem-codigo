"""Extrai as questões das provas oficiais do ENEM (PDF do INEP, caderno azul).

Uso:
  python3 tools/extrair.py <pasta-das-provas> <pasta-de-saída>

A pasta das provas segue o padrão enviado pelo usuário:
  <ano>/<ano>-dia-1-prova.pdf, <ano>-dia-1-gabarito.pdf, -dia-2-...

Saída: <saída>/questions.raw.json (questões sem classificação),
<saída>/img/*.jpg e <saída>/extracao.log.json (avisos por questão).

Decisões:
- Leitura em duas colunas com faixas de largura total (figuras e
  enunciados que cruzam a calha central).
- Índices e expoentes viram caracteres Unicode (CO₂, 10⁻³); quando não
  há caractere equivalente, ficam como _(...) e ^(...).
- Fórmulas montadas (frações, radicais) e figuras viram imagem recortada
  do próprio PDF, para não publicar fórmula quebrada.
- 2021: o INEP embutiu parte do texto com glifos sem mapa Unicode; os
  nomes de glifo "gNN" do CFF apontam para a ordem padrão de glifos do
  Arial e são decodificados por ela.
"""
import io
import json
import pathlib
import re
import sys
import unicodedata

import pymupdf
from fontTools.agl import toUnicode
from fontTools.cffLib import CFFFontSet
from fontTools.ttLib.standardGlyphOrder import standardGlyphOrder

ZOOM = 1.6
SUP = str.maketrans("0123456789+-−=()niax", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁼⁽⁾ⁿⁱᵃˣ")
SUB = str.maketrans("0123456789+-−=()aeoxnmt", "₀₁₂₃₄₅₆₇₈₉₊₋₋₌₍₎ₐₑₒₓₙₘₜ")
SUP_OK = set("0123456789+-−=()niax ")
SUB_OK = set("0123456789+-−=()aeoxnmt ")
HEAD = re.compile(r"^\s*QUEST[ÃA]O\s+(\d{1,3})\s*$", re.I)
LANG = re.compile(r"Quest[õo]es\s+de\s+0?1\s+a\s+0?5.*\((?:op[çc][ãa]o\s+)?(ingl[êe]s|espanhol)\)", re.I)
MATHFONT = re.compile(r"Symbol|Math|MTExtra|Euclid|Cambria", re.I)


# ----------------------------------------------------------------- 2021

# Na fonte de 2021 a ordem de glifos do Arial difere da ordem padrão do Mac
# em alguns pontos. Correções conferidas no contexto (ex.: "pro›table" →
# "profitable", "re fiexão" → "reflexão", aspas de abertura e fechamento).
FIX2021 = {
    "guilsinglright": "fi", "fi": "fl", "oe": "–", "endash": "—",
    "emdash": "“", "quotedblleft": "”", "quoteleft": "’", "Igrave": "Ó",
    "partialdiff": "·", "Thorn": "−", "onehalf": "φ", "egrave": "°",
    "Icircumflex": "³", "ordmasculine": "²",
}

def glyph_maps(doc):
    """Por xref de fonte CFF, gid → caractere para glifos nomeados gNN."""
    maps = {}
    for page in doc:
        for xref, ext, *_ in page.get_fonts(full=True):
            if xref in maps or ext != "cff":
                continue
            maps[xref] = {}
            try:
                buf = doc.extract_font(xref)[3]
                cs = CFFFontSet()
                cs.decompile(io.BytesIO(buf), None)
                names = cs[cs.fontNames[0]].charset
            except Exception:
                continue
            for gid, n in enumerate(names):
                m = re.fullmatch(r"g(\d+)", n)
                if m and int(m.group(1)) < len(standardGlyphOrder):
                    name = standardGlyphOrder[int(m.group(1))]
                    u = FIX2021.get(name) or toUnicode(name)
                    if u:
                        maps[xref][gid] = u
    return maps


def decode_2021(page, maps):
    """Mapa origem→char usando gid quando o glifo é gNN."""
    fix = {}
    xrefs = {}
    for f in page.get_fonts(full=True):
        xrefs.setdefault(f[3].split("+")[-1], []).append(f[0])
    for sp in page.get_texttrace():
        base = (sp["font"] or "").split("+")[-1]
        for x in xrefs.get(base, []):
            m = maps.get(x)
            if not m:
                continue
            for c in sp["chars"]:
                u = m.get(c[1])
                if u is not None:
                    fix[(round(c[2][0], 1), round(c[2][1], 1))] = u
    return fix


# ------------------------------------------------------------ linhas

def line_text(line, fix):
    """Texto da linha com índices e expoentes convertidos."""
    spans = [s for s in line["spans"] if "".join(c["c"] for c in s["chars"]).strip() or s["chars"]]
    if not spans:
        return "", []
    sizes = {}
    for s in spans:
        n = len("".join(c["c"] for c in s["chars"]).strip())
        sizes[round(s["size"], 1)] = sizes.get(round(s["size"], 1), 0) + n
    main = max(sizes, key=sizes.get)
    base = [s["origin"][1] for s in spans if abs(s["size"] - main) < 0.3]
    base = sorted(base)[len(base) // 2] if base else spans[0]["origin"][1]
    out = []
    fonts = []
    for s in spans:
        t = "".join(fix.get((round(c["origin"][0], 1), round(c["origin"][1], 1)), c["c"]) for c in s["chars"])
        fonts.append(s["font"])
        small = s["size"] < main * 0.85
        dy = s["origin"][1] - base
        if small and t.strip() and dy < -1:
            t = t.strip()
            t = t.translate(SUP) if set(t) <= SUP_OK else "^(" + t + ")"
        elif small and t.strip() and dy > 1:
            t = t.strip()
            t = t.translate(SUB) if set(t) <= SUB_OK else "_(" + t + ")"
        out.append(t)
    return "".join(out), fonts


def norm(t):
    t = unicodedata.normalize("NFC", t.replace("\t", " ").replace("\u00ad", ""))
    t = t.replace("\uf0b7", "•").replace("\x1f", "").replace("\x07", "")
    t = re.sub(r"ﬁ ?(?=[a-zà-ú])", "fi", t).replace("ﬁ", "fi")
    t = re.sub(r"ﬂ ?(?=[a-zà-ú])", "fl", t).replace("ﬂ", "fl")
    t = re.sub(r"[\u2000-\u200a\u202f]", " ", t)
    return re.sub(r"[ \u00a0]+", " ", t)


# ----------------------------------------------------------- figuras

def boxes(page, top, bottom, heads=()):
    """Agrupa desenhos vetoriais e imagens em retângulos de figura."""
    W = page.rect.width
    rs = []
    for d in page.get_drawings():
        r = pymupdf.Rect(d["rect"])
        if r.width < 1 or r.height < 1:
            # linhas retas têm retângulo degenerado (vazio para o PyMuPDF)
            r = pymupdf.Rect(r.x0 - 0.6, r.y0 - 0.6, r.x1 + 0.6, r.y1 + 0.6)
            d = dict(d, rect=r)
        if r.y1 < top or r.y0 > bottom or r.x0 < 8 or r.y0 < 8 or r.x1 > W - 8:
            continue
        if r.height <= 8 and r.width > 0.6 * W:
            continue  # régua de seção
        if r.width <= 4 and r.height > 0.3 * page.rect.height:
            continue  # divisória de colunas
        if any(h.y0 - 6 <= r.y0 <= h.y1 and r.height <= 20 and r.x0 >= h.x1 - 8 for h in heads):
            continue  # faixa decorativa na linha do cabeçalho "QUESTÃO"
        if 2.5 < r.height <= 12 and r.width >= 60 and d.get("fill") and not d.get("color"):
            continue  # faixa decorativa ao lado do cabeçalho da questão
        if r.width > 0.6 * W and r.height > 0.6 * page.rect.height:
            continue
        rs.append([pymupdf.Rect(r), len(d["items"]), "v", d])
    for b in page.get_text("dict")["blocks"]:
        if b["type"] == 1:
            r = pymupdf.Rect(b["bbox"])
            if any(h.y0 - 6 <= r.y0 <= h.y1 and r.height <= 20 and r.x0 >= h.x1 - 8 for h in heads):
                continue  # faixa decorativa na linha do cabeçalho
            if r.width >= 12 and r.height >= 12 and r.y0 < bottom and r.y1 > top:
                rs.append([r, 50, "i", None])
    groups = []
    for r, n, k, d in rs:
        groups.append({"r": pymupdf.Rect(r), "n": n, "img": k == "i", "thin": [d] if k == "v" else []})
    merged = True
    while merged:
        merged = False
        out = []
        for g in groups:
            for o in out:
                tol = 0 if (g["img"] and not g["thin"]) or (o["img"] and not o["thin"]) else (4 if g["r"].height < 3 or g["r"].width < 3 or o["r"].height < 3 or o["r"].width < 3 else 2)
                if (g["r"].x0 <= o["r"].x1 + tol and o["r"].x0 <= g["r"].x1 + tol and
                        g["r"].y0 <= o["r"].y1 + tol and o["r"].y0 <= g["r"].y1 + tol):
                    o["r"] |= g["r"]
                    o["n"] += g["n"]
                    o["img"] = o["img"] or g["img"]
                    o["thin"] += g["thin"]
                    merged = True
                    break
            else:
                out.append(g)
        groups = out
    return groups


def prose(t):
    """Linha de texto corrido (não fórmula)."""
    return len(re.findall(r"[A-Za-zÀ-ú]{3,}", t)) >= 4


def is_thin(d):
    r = d["rect"]
    return r.height <= 2.2 and r.width >= 4


# -------------------------------------------------------------- página

def page_elems(doc, pno, maps, out_img, area_of_page):
    page = doc[pno]
    W, H = page.rect.width, page.rect.height
    mid = W / 2
    fix = decode_2021(page, maps) if maps else {}
    top, bottom = 60, H - 44
    lines = []
    rotated = []
    for b in page.get_text("rawdict")["blocks"]:
        if b["type"]:
            continue
        for l in b["lines"]:
            if l["dir"][0] < 0.9:
                rr = pymupdf.Rect(l["bbox"])
                if top < rr.y0 and rr.y1 < bottom and rr.height < 200:
                    rotated.append(rr)  # rótulo de eixo girado: entra na figura vizinha
                continue
            t, fonts = line_text(l, fix)
            t = norm(t)
            r = pymupdf.Rect(l["bbox"])
            if not t.strip() or r.y1 < top or r.y0 > bottom:
                continue
            size = max(s["size"] for s in l["spans"])
            if size < 3 or any("C39" in f for f in fonts):
                continue
            if re.search(r"Caderno \d+\s*[-–•]\s*AZUL|CADERNO \d+ • AZUL|^\s*\d{1,2}\s*$", t) and r.y0 > H - 70:
                continue  # rodapé
            if re.fullmatch(r"(\d{1,3}\s*ENEM\s*)+|(ENEM\s*20\d\d\s*)+|M?(20\d\dENEM)+.*", t.strip()):
                continue
            lines.append({"r": r, "t": t, "fonts": fonts, "size": size,
                          "bold": all("Bold" in f or "Black" in f for f in fonts if f),
                          "f0": fonts[0] if fonts else ""})
    # Funde linhas na mesma altura e adjacentes (spans quebrados pelo PDF).
    lines.sort(key=lambda x: (round(x["r"].y0), x["r"].x0))
    merged = []
    for l in lines:
        p = merged[-1] if merged else None
        if (p and abs(p["r"].y0 - l["r"].y0) < 2.5 and 0 <= l["r"].x0 - p["r"].x1 < 12
                and not ((p["r"].x1 <= mid + 3) ^ (l["r"].x1 <= mid + 3) and l["r"].x0 > mid - 3)):
            sep = "" if p["t"].endswith(" ") or l["t"].startswith(" ") or l["r"].x0 - p["r"].x1 < 1.2 else " "
            p["t"] += sep + l["t"]
            p["r"] |= l["r"]
            p["fonts"] += l["fonts"]
            p["bold"] = p["bold"] and l["bold"]
        else:
            merged.append(l)
    lines = merged
    # Linhas duplicadas (2022+ repete a letra da alternativa sozinha).
    seen = []
    dedup = []
    for l in lines:
        if re.fullmatch(r"[A-E]\s*", l["t"]) and any(
                o is not l and abs(o["r"].y0 - l["r"].y0) < 4 and abs(o["r"].x0 - l["r"].x0) < 2 and o["t"].strip().startswith(l["t"].strip()) and len(o["t"].strip()) > 1
                for o in lines):
            continue
        dedup.append(l)
    lines = dedup

    figs = []
    mathy = area_of_page in ("CN", "MT")
    # Linha com caractere sem mapa Unicode (símbolos da fonte embaralhada)
    # vira imagem recortada: melhor que publicar um símbolo trocado.
    for l in lines:
        odd = re.search(r"[\x00-\x08\x0b-\x1f\ue000-\uf8ff\ufffd]", l["t"])
        if odd or (maps and any("Symbol" in (f or "") for f in l["fonts"])):
            figs.append({"r": pymupdf.Rect(l["r"]), "kind": "math"})
    for g in boxes(page, top, bottom, [l["r"] for l in lines if HEAD.match(l["t"])]):
        r = g["r"]
        inside = [l for l in lines if r.contains(l["r"]) or (pymupdf.Rect(l["r"]) & r).get_area() > 0.6 * l["r"].get_area()]
        body = [l for l in inside if l["size"] >= 8.5]
        chars = sum(len(l["t"]) for l in body)
        only_thin = (g["thin"] and all(is_thin(d) for d in g["thin"]) and not g["img"]
                     and r.height <= 3 and r.width < 160)
        if only_thin:
            if mathy:
                # traço de fração/radical: vira faixa de fórmula
                near = [l for l in lines if l["r"].y0 - 14 <= r.y1 and l["r"].y1 + 14 >= r.y0
                        and l["r"].x0 <= r.x1 and l["r"].x1 >= r.x0 and l["r"].height < 20]
                above = [l for l in near if l["r"].y1 <= r.y0 + 3]
                below = [l for l in near if l["r"].y0 >= r.y1 - 3]
                if above and below:
                    figs.append({"r": r, "kind": "math"})
            continue
        if r.width < 14 or r.height < 10:
            continue
        frame = (not g["img"] and g["n"] <= 4 and len(body) >= 3 and chars > 120)
        if frame:
            continue  # moldura de texto: o texto fica como texto
        if not g["img"] and g["n"] <= 2 and not inside and (r.width < 25 or r.height < 25):
            continue
        figs.append({"r": r, "kind": "fig"})
    # Faixas de fórmula: une o traço com as linhas da mesma coluna que ele toca.
    side = lambda rr: "F" if rr.x0 < mid - 20 and rr.x1 > mid + 20 else ("L" if (rr.x0 + rr.x1) / 2 < mid else "R")
    for f in figs:
        if f["kind"] != "math":
            continue
        r = pymupdf.Rect(f["r"])
        c = side(r)
        for _ in range(2):
            for l in lines:
                if (l["r"].y0 <= r.y1 + 2 and l["r"].y1 >= r.y0 - 2 and l["r"].x0 <= r.x1 + 30
                        and l["r"].x1 >= r.x0 - 30 and l["r"].height < 20 and side(l["r"]) == c
                        and not HEAD.match(l["t"]) and not prose(l["t"])):
                    r |= l["r"]
        # completa a linha da fórmula (ex.: seta e produtos de uma equação)
        for l in lines:
            ov = min(l["r"].y1, r.y1) - max(l["r"].y0, r.y0)
            near = l["r"].x0 - r.x1 < 60 and r.x0 - l["r"].x1 < 60
            if (ov > 0.5 * l["r"].height and near and not HEAD.match(l["t"]) and not prose(l["t"])
                    and (c == "F" or side(l["r"]) in (c, "F"))):
                r |= l["r"]
        f["r"] = r
    side_of = lambda rr: "F" if rr.x0 < mid - 20 and rr.x1 > mid + 20 else ("R" if rr.x0 >= mid - 8 or (rr.x0 + rr.x1) / 2 >= mid else "L")
    # Rótulos de figura (eixos, legendas curtas) entram na figura mais próxima.
    def dist(r, l):
        dx = max(r.x0 - l.x1, l.x0 - r.x1, 0)
        dy = max(r.y0 - l.y1, l.y0 - r.y1, 0)
        return max(dx, dy * 1.25)
    for _ in range(3):
        grow = False
        for l in lines:
            t = l["t"].strip()
            if HEAD.match(t) or "Bundesbahn" in l["f0"] or len(t) > 30:
                continue
            if re.match(r"(Dispon|Acesso|Fonte)", t):
                continue
            fs = [f for f in figs if f["kind"] == "fig"]
            if not fs or any(f["r"].contains(l["r"]) for f in fs):
                continue
            best = min(fs, key=lambda f: dist(f["r"], l["r"]))
            sb, sl = side_of(best["r"]), side_of(l["r"])
            if sb != "F" and sl != sb:
                continue  # rótulo não atravessa a calha entre colunas
            inside_x = l["r"].x0 >= best["r"].x0 - 6 and l["r"].x1 <= best["r"].x1 + 6
            numeric = re.fullmatch(r"[\d\s.,%−+\-–()R$]+", t) is not None and len(t) <= 14
            label = l["size"] < 9.3 or len(t) <= 4 or numeric or (inside_x and not re.search(r"[.:?;]$", t))
            if label and dist(best["r"], l["r"]) <= 10:
                best["r"] |= l["r"]
                grow = True
        if not grow:
            break
    for rr in rotated:
        fs = [f for f in figs if f["kind"] == "fig"]
        if fs:
            best = min(fs, key=lambda f: dist(f["r"], rr))
            if dist(best["r"], rr) <= 12:
                best["r"] |= rr
    # Zonas com linhas lado a lado na mesma coluna (tabelas, índices
    # empilhados, rótulos) viram imagem: o texto linear sairia embaralhado.
    side = lambda rr: "F" if rr.x0 < mid - 20 and rr.x1 > mid + 20 else ("L" if (rr.x0 + rr.x1) / 2 < mid else "R")
    letter = lambda l: "Bundesbahn" in l["f0"] and re.match(r"^[A-E](\s|$)", l["t"].strip())
    figr = [f["r"] + (-2, -2, 2, 2) for f in figs if f["kind"] == "fig"]
    cand = [l for l in lines if not HEAD.match(l["t"]) and not letter(l) and not LANG.search(l["t"])
            and not any((pymupdf.Rect(l["r"]) & fr).get_area() > 0.3 * max(l["r"].get_area(), 1) for fr in figr)]
    zone = set()
    for i, a in enumerate(cand):
        for b in cand[i + 1:]:
            if side(a["r"]) != side(b["r"]):
                ym0, ym1 = min(a["r"].y0, b["r"].y0) - 30, max(a["r"].y1, b["r"].y1) + 30
                if not any(side(f["r"]) == "F" and f["r"].y1 > ym0 and f["r"].y0 < ym1 for f in cand):
                    continue
            ov = min(a["r"].y1, b["r"].y1) - max(a["r"].y0, b["r"].y0)
            hmin = min(a["r"].height, b["r"].height)
            disjoint = a["r"].x1 + 3 < b["r"].x0 or b["r"].x1 + 3 < a["r"].x0
            if ov > 0.4 * hmin and (disjoint or (mathy and abs(a["r"].y0 - b["r"].y0) > 1.5)):
                zone.add(id(a))
                zone.add(id(b))
    zr = []
    for l in cand:
        if id(l) in zone:
            for z in zr:
                if (z.y0 - 4 <= l["r"].y1 and l["r"].y0 <= z.y1 + 4 and z.x0 - 40 <= l["r"].x1 and l["r"].x0 <= z.x1 + 40
                        and ("F" in (side(z), side(l["r"])) or side(z) == side(l["r"]))):
                    z |= l["r"]
                    break
            else:
                zr.append(pymupdf.Rect(l["r"]))
    grp = [g["r"] for g in boxes(page, top, bottom, [l["r"] for l in lines if HEAD.match(l["t"])])]
    changed = True
    rounds = 0
    while changed and rounds < 8:
        changed = False
        rounds += 1
        for z in zr:
            for g in grp:
                if (z + (-4, -4, 4, 4)).intersects(g) and not z.contains(g) and g.width < W * 0.95 and not g.is_empty:
                    z |= g
                    changed = True
        out = []
        for z in zr:
            for o in out:
                if (o + (-2, -6, 2, 6)).intersects(z) and ("F" in (side(o), side(z)) or side(o) == side(z)):
                    o |= z
                    changed = True
                    break
            else:
                out.append(pymupdf.Rect(z))
        zr = out
    for z in zr:
        figs.append({"r": z, "kind": "math" if mathy else "fig"})
    # Linhas com fontes de símbolo matemático em CN/MT também viram faixa.
    if mathy:
        for l in lines:
            if any(MATHFONT.search(f or "") for f in l["fonts"]) and not re.match(r"^[A-E]\s", l["t"]):
                txt = l["t"]
                if re.search(r"[√∑∫∞≅≈≠≤≥∆Δ]|^\s*[^\w\s]{1,3}\s*$", txt):
                    figs.append({"r": pymupdf.Rect(l["r"]), "kind": "math"})
    # Faixa de fórmula ocupa a linha inteira (seta e produtos de uma equação).
    gr_all = [g["r"] for g in boxes(page, top, bottom, [l["r"] for l in lines if HEAD.match(l["t"])])]
    for f in figs:
        if f["kind"] != "math":
            continue
        r = f["r"]
        for _ in range(3):
            for x in [l["r"] for l in lines if not HEAD.match(l["t"]) and not prose(l["t"])
                      and not ("Bundesbahn" in l["f0"] and re.match(r"^[A-E](\s|$)", l["t"].strip()))] + gr_all:
                ov = min(x.y1, r.y1) - max(x.y0, r.y0)
                if ov > 0.5 * min(x.height, r.height) and x.x0 - r.x1 < 60 and r.x0 - x.x1 < 60 and x.height < 3 * max(r.height, 12):
                    u = r | x
                    if side(u) == "F" and side(r) != "F" and not any(
                            side(l["r"]) == "F" and l["r"].y1 > u.y0 - 30 and l["r"].y0 < u.y1 + 30 for l in lines):
                        continue  # não atravessa a calha numa página em duas colunas
                    r |= x
        f["r"] = r
    # Uma figura/faixa não pode engolir várias alternativas: corta entre as letras.
    letters, seen_l = [], set()
    for l in lines:
        if "Bundesbahn" in l["f0"] and re.match(r"^[A-E](\s|$)", l["t"].strip()):
            k = (l["t"].strip()[0], round(l["r"].y0 / 4), round(l["r"].x0 / 4))
            if k not in seen_l:
                seen_l.add(k)
                letters.append(l)
    split = []
    for f in figs:
        r = f["r"]
        fs = side(r)
        ls = sorted([l for l in letters if (fs == "F" or side(l["r"]) == fs) and r.y0 - 2 <= (l["r"].y0 + l["r"].y1) / 2 <= r.y1 + 2
                     and l["r"].x0 <= r.x0 + 20 and r.x0 - l["r"].x1 < 90], key=lambda l: l["r"].y0)
        uniq_l = {}
        for l in ls:
            uniq_l.setdefault(l["t"].strip()[0], l)
        ls = sorted(uniq_l.values(), key=lambda l: l["r"].y0)
        if len(ls) < 2:
            split.append(f)
            continue
        mid_y = lambda l: (l["r"].y0 + l["r"].y1) / 2
        gap = min(mid_y(ls[i + 1]) - mid_y(ls[i]) for i in range(len(ls) - 1))
        cuts = [r.y0] + [(mid_y(ls[i]) + mid_y(ls[i + 1])) / 2 for i in range(len(ls) - 1)] + [r.y1]
        # parte acima da primeira alternativa (texto do enunciado) fica separada
        first_top = mid_y(ls[0]) - gap / 2
        pieces = []
        if first_top - r.y0 > 8:
            pieces.append(("stem", pymupdf.Rect(r.x0, r.y0, r.x1, first_top)))
            cuts[0] = first_top
        for i in range(len(cuts) - 1):
            pieces.append((ls[i]["t"].strip()[0], pymupdf.Rect(max(r.x0, ls[i]["r"].x1 + 1), cuts[i], r.x1, cuts[i + 1])))
        for k, p in pieces:
            if p.height > 4:
                split.append({"r": p, "kind": f["kind"], "nomerge": k})
    figs = split
    # Une figuras sobrepostas.
    figs.sort(key=lambda f: (f["r"].y0, f["r"].x0))
    fm = []
    for f in figs:
        for o in fm:
            if (f.get("nomerge") == o.get("nomerge") and (f["r"] & o["r"]).get_area() > 4
                    and {side(f["r"]), side(o["r"])} != {"L", "R"}):
                o["r"] |= f["r"]
                o["kind"] = "fig" if "fig" in (o["kind"], f["kind"]) else "math"
                break
        else:
            fm.append(f)
    figs = fm
    # Linhas cobertas por figura saem do texto (aparecem na imagem).
    # Exceção: cabeçalho de questão e letras de alternativa.
    keep = []
    for l in lines:
        covered = None
        for f in figs:
            inter = (pymupdf.Rect(l["r"]) & f["r"]).get_area()
            if inter > 0.5 * max(l["r"].get_area(), 1):
                covered = f
        if covered and not HEAD.match(l["t"]) and not (re.match(r"^[A-E](\s|$)", l["t"].strip()) and "Bundesbahn" in l["f0"]):
            continue
        if covered and re.match(r"^[A-E](\s|$)", l["t"].strip()) and "Bundesbahn" in l["f0"]:
            # letra de alternativa sobre a figura: recorta a figura à direita da letra
            if covered["r"].x0 < l["r"].x1 and l["r"].x0 - covered["r"].x0 < 15:
                covered["r"].x0 = l["r"].x1 + 1
            l = dict(l, t=l["t"].strip()[0])
        keep.append(l)
    lines = keep

    elems = []
    for l in lines:
        r = l["r"]
        col = "F" if r.x0 < mid - 20 and r.x1 > mid + 20 else ("R" if r.x0 >= mid - 8 or (r.x0 + r.x1) / 2 >= mid else "L")
        elems.append({"k": "t", "r": r, "col": col, **l})
    for f in figs:
        r = f["r"]
        col = "F" if r.x0 < mid - 15 and r.x1 > mid + 15 else ("L" if (r.x0 + r.x1) / 2 < mid else "R")
        elems.append({"k": f["kind"], "r": r, "col": col, "page": pno})
    # Letras de alternativa ao lado de figura: associa pela altura.
    for e in elems:
        if e["k"] == "t" and re.fullmatch(r"[A-E]", e["t"].strip()):
            for f in elems:
                if f["k"] in ("fig", "math") and f["r"].y0 - 4 <= (e["r"].y0 + e["r"].y1) / 2 <= f["r"].y1 + 4 and 0 <= f["r"].x0 - e["r"].x0 <= 90:
                    f["alt_of"] = e["t"].strip()
                    f["sort_y"] = e["r"].y0 + 0.1
    # Margem esquerda de cada coluna (para reconhecer recuo de parágrafo).
    cl = {}
    for e in elems:
        if e["k"] == "t" and len(e["t"]) > 25:
            cl[e["col"]] = min(cl.get(e["col"], 1e9), e["r"].x0)
    for e in elems:
        e["cl"] = cl.get(e["col"], e["r"].x0)
    order = reading_order(elems, mid)
    return order


def reading_order(elems, mid):
    key_y = lambda e: e.get("sort_y", e["r"].y0)
    full = sorted([e for e in elems if e["col"] == "F"], key=key_y)
    rest = [e for e in elems if e["col"] != "F"]
    out = []
    prev = -1e9
    cuts = full + [None]
    for f in cuts:
        lim = key_y(f) if f else 1e9
        band = [e for e in rest if prev <= key_y(e) < lim]
        out += sorted([e for e in band if e["col"] == "L"], key=key_y)
        out += sorted([e for e in band if e["col"] == "R"], key=key_y)
        if f:
            out.append(f)
            prev = key_y(f)
    return out


# ------------------------------------------------------------ gabarito

def gabarito(path):
    toks = []
    for p in pymupdf.open(path):
        toks += [t.strip() for t in p.get_text().split("\n") if t.strip()]
    g = {}
    i = 0
    while i < len(toks):
        if re.fullmatch(r"\d{1,3}", toks[i]):
            n = int(toks[i])
            ans = []
            j = i + 1
            while j < len(toks) and (re.fullmatch(r"[A-E]", toks[j]) or re.match(r"anula", toks[j], re.I)):
                ans.append("X" if re.match(r"anula", toks[j], re.I) else toks[j])
                j += 1
            if ans and 1 <= n <= 180 and n not in g:
                g[n] = ans
            i = j if ans else i + 1
        else:
            i += 1
    return g


# ------------------------------------------------------------- provas

def areas(ano, dia):
    if ano <= 2016:
        return ("CH", "CN") if dia == 1 else ("LC", "MT")
    return ("LC", "CH") if dia == 1 else ("CN", "MT")


def area_of(ano, num):
    if ano <= 2016:
        return "CH" if num <= 45 else "CN" if num <= 90 else "LC" if num <= 135 else "MT"
    return "LC" if num <= 45 else "CH" if num <= 90 else "CN" if num <= 135 else "MT"


def lang_range(ano):
    return range(91, 96) if ano <= 2016 else range(1, 6)


SECTION = re.compile(r"^\s*(Quest[õo]es de \d+ a \d+|(LINGUAGENS, C[ÓO]DIGOS|CI[ÊE]NCIAS HUMANAS|CI[ÊE]NCIAS DA NATUREZA|MATEM[ÁA]TICA)( E SUAS)?\s*(TECNOLOGIAS)?\s*$|TECNOLOGIAS\s*$)", re.I)
STOP = re.compile(r"PROPOSTA DE REDA|INSTRU[ÇC][ÕO]ES PARA A REDA|^\s*RASCUNHO\s*$|TEXTO DEFINITIVO|FOLHA DE RASCUNHO", re.I)


def extract(src, outdir):
    src = pathlib.Path(src)
    outdir = pathlib.Path(outdir)
    (outdir / "img").mkdir(parents=True, exist_ok=True)
    allq, log = [], []
    for ydir in sorted(p for p in src.iterdir() if p.is_dir() and p.name.isdigit()):
        ano = int(ydir.name)
        for dia in (1, 2):
            prova = ydir / f"{ano}-dia-{dia}-prova.pdf"
            gab = ydir / f"{ano}-dia-{dia}-gabarito.pdf"
            if not prova.exists():
                continue
            G = gabarito(gab) if gab.exists() else {}
            doc = pymupdf.open(prova)
            maps = glyph_maps(doc) if ano == 2021 else {}
            stream = []
            for pno in range(doc.page_count):
                ptxt = doc[pno].get_text()
                if re.search(r"PROPOSTA DE REDA[ÇC][ÃA]O", ptxt) and not re.search(r"QUEST[ÃA]O\s+\d", ptxt, re.I):
                    stream.append({"k": "stop"})
                    continue
                a_guess = None
                nums = [int(n) for n in re.findall(r"(?i)quest[ãa]o\s+(\d{1,3})\b", ptxt)]
                if nums:
                    a_guess = area_of(ano, nums[0])
                for e in page_elems(doc, pno, maps, outdir / "img", a_guess):
                    e["page"] = pno
                    stream.append(e)
                stream.append({"k": "pagebreak"})
            qs = split(stream, ano)
            carry = []
            for num, lang, items in qs:
                items, carry = carry + items, []
                q, warn = build(doc, ano, dia, num, lang, items, G, outdir, carry)
                if q:
                    allq.append(q)
                if warn:
                    log.append({"id": q["id"] if q else f"{ano}-{num}", "avisos": warn})
            print(prova.name, len(qs), "questões", file=sys.stderr)
    return allq, log


JUNK = re.compile(r"Transcreva a sua Reda|\(adaptad[oa]\)\.?\s*$|^Dispon[íi]vel em|Acesso em|^\s*\d{1,4}\s*$|E SUAS TECNOLOGIAS|^\s*\*\w+\*\s*$")


def split(stream, ano):
    qs = []
    cur = None
    lang = None
    lr = lang_range(ano)
    seen_lang = {}
    for e in stream:
        if e["k"] == "stop":
            cur = None
            continue
        if e["k"] == "pagebreak":
            if cur is not None:
                cur[2].append(e)
            continue
        if e["k"] == "t":
            m = LANG.search(e["t"])
            if m:
                lang = "ingles" if m.group(1).lower().startswith("ingl") else "espanhol"
                continue
            h = HEAD.match(e["t"])
            if h:
                n = int(h.group(1))
                l = None
                if n in lr:
                    # Sem cabeçalho de idioma: o primeiro bloco é inglês.
                    if lang is None:
                        l = "espanhol" if seen_lang.get(n) else "ingles"
                    else:
                        l = lang
                    seen_lang[n] = True
                cur = [n, l, []]
                qs.append(cur)
                continue
            if SECTION.search(e["t"]) and e["bold"]:
                continue
            if STOP.search(e["t"]) or (e["size"] >= 12.5 and e["bold"] and re.search(r"TECNOLOGIAS|REDA", e["t"])):
                cur = None
                continue
        if cur is not None:
            cur[2].append(e)
    return qs


def build(doc, ano, dia, num, lang, items, G, outdir, carry):
    warn = []
    area = area_of(ano, num)
    qid = f"{ano}-{area}-{num:02d}" + ({"ingles": "-en", "espanhol": "-es"}.get(lang, ""))
    # Separa enunciado e alternativas.
    parts = {"stem": []}
    curk = "stem"
    expect = "A"
    for e in items:
        if e["k"] == "t":
            t = e["t"].strip()
            m = re.match(r"^([A-E])(?:\s+|$)(.*)$", t)
            is_alt = m and m.group(1) == expect and "Bundesbahn" in e["f0"]
            if is_alt:
                curk = expect
                parts[curk] = []
                expect = chr(ord(expect) + 1) if expect != "E" else "-"
                if m.group(2).strip():
                    parts[curk].append(dict(e, t=m.group(2)))
                continue
        if e.get("alt_of") and e["alt_of"] in parts and e["alt_of"] == curk:
            parts[curk].append(e)
            continue
        parts[curk].append(e)
    alts_found = [k for k in "ABCDE" if k in parts]
    if alts_found != list("ABCDE"):
        warn.append("alternativas encontradas: " + "".join(alts_found))
    # Sobra depois da E: corta em salto grande ou troca de coluna.
    if "E" in parts:
        e_items = parts["E"]
        keepE, extra = [], []
        last = None
        for e in e_items:
            if e["k"] == "pagebreak":
                if keepE:
                    extra.append(e)
                continue
            if last is not None and (extra or e.get("page") != last.get("page") or e["col"] != last["col"] or e["r"].y0 - last["r"].y1 > 22):
                extra.append(e)
                continue
            keepE.append(e)
            last = e
        sobra = [x for x in extra if x["k"] == "t" and x["t"].strip() and not JUNK.search(x["t"])]
        lastt = next((x["t"].strip() for x in reversed(keepE) if x["k"] == "t"), "")
        if sobra and lastt and not re.search(r"[.!?)]$", lastt) and re.match(r"[a-zà-ú]", sobra[0]["t"].strip()):
            # A alternativa E continua na outra coluna ou página.
            keepE += sobra[:1]
            sobra = sobra[1:]
        parts["E"] = keepE
        if sobra:
            # Texto-base da questão seguinte, impresso antes do cabeçalho dela.
            i0 = next(i for i, x in enumerate(extra) if x is sobra[0])
            carry.extend(x for x in extra[i0:] if x["k"] != "t" or not JUNK.search(x["t"]))
    n_img = [0]

    def render(e):
        n_img[0] += 1
        name = f"{qid}-{n_img[0]}.jpg"
        r = pymupdf.Rect(e["r"]) + (-3, -3, 3, 3)
        pix = doc[e["page"]].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), clip=r)
        pix.save(str(outdir / "img" / name), jpg_quality=78)
        return "img/" + name

    def text_of(items, alt=False):
        out = []
        last = None
        for e in items:
            if e["k"] == "pagebreak":
                continue
            if e["k"] in ("fig", "math"):
                out.append(("img", render(e)))
                last = None
                continue
            t = e["t"].rstrip()
            if last is None:
                out.append(("t", t.strip()))
            else:
                gap = e["r"].y0 - last["r"].y1
                ind = lambda x: x["r"].x0 - x.get("cl", x["r"].x0)
                indent = ind(e) > 8 and ind(last) <= 3
                bullet = re.match(r"^\s*[•▪●■◦–-]\s", t) is not None
                small = e["size"] < 8.6
                src_line = (small and not (last["size"] < 8.6)) or (not small and last["size"] < 8.6)
                para = (not alt) and (gap > 6 or indent or src_line or e.get("page") != last.get("page") and False)
                short = last["r"].x1 < col_right(last) - 35
                if para:
                    out.append(("t", "\n\n" + t.strip()))
                elif (short or bullet) and not alt:
                    out.append(("t", "\n" + t.strip()))
                else:
                    prev = out[-1][1] if out and out[-1][0] == "t" else ""
                    joiner = "" if prev.endswith("-") and not prev.endswith(" -") else " "
                    tt = t.strip()
                    if joiner == "" and tt.startswith("-"):
                        tt = tt[1:]  # hífen repetido na quebra de linha
                    out.append(("t", joiner + tt))
            last = e
        return out

    def col_right(e):
        W = doc[e.get("page", 0)].rect.width
        return W / 2 - 3 if e["col"] == "L" else W - 30

    stem = text_of(parts["stem"])
    enun = ""
    for k, v in stem:
        enun += v if k == "t" else "\n\n![Figura da questão](" + v + ")\n\n"
    enun = re.sub(r"\n{3,}", "\n\n", enun).strip()
    alts = {}
    for k in "ABCDE":
        if k not in parts:
            continue
        seg = text_of(parts[k], alt=True)
        txt = "".join(v for kk, v in seg if kk == "t").strip()
        ims = [v for kk, v in seg if kk == "img"]
        if ims and not txt and len(ims) == 1:
            alts[k] = "img:" + ims[0]
        elif ims:
            alts[k] = re.sub(r"[ \t]+", " ", "".join(
                v if kk == "t" else " ![Figura da alternativa](" + v + ") " for kk, v in seg)).strip()
        else:
            alts[k] = re.sub(r"\s+", " ", txt)
    # Ligadura fi/fl seguida de espaço espúrio ("verifi cam", "fi cha").
    lig = lambda t: re.sub(r"f([il]) (?=[a-zà-úñ])(?!de\b)", r"f\1", t)
    enun = lig(enun)
    alts = {k: lig(v) for k, v in alts.items()}
    g = G.get(num)
    gab = None
    anulada = False
    if not g:
        warn.append("sem gabarito")
    else:
        if len(g) == 2 and lang:
            g = [g[0] if lang == "ingles" else g[1]]
        gab = g[0]
        if gab == "X":
            anulada, gab = True, None
    if not enun:
        warn.append("enunciado vazio")
    odd = re.findall(r"[\x00-\x08\x0b-\x1f\ue000-\uf8ff\ufffd]", enun + "".join(alts.values()))
    if odd:
        warn.append("caracteres não reconhecidos no texto: " + " ".join(sorted(set(repr(c) for c in odd))))
    if any(not v for v in alts.values()):
        warn.append("alternativa vazia")
    q = {
        "id": qid, "ano": ano, "area": area, "lang": lang, "enunciado": enun,
        "imagens": [], "alts": alts, "gab": gab, "resolucao": None,
        "aplicacao": "regular", "caderno": "Azul", "dia": dia, "numero": num,
        "fonte": f"INEP — ENEM {ano}, {dia}º dia, caderno azul (prova e gabarito oficiais)",
    }
    if anulada:
        q["anulada"] = True
    return q, warn


if __name__ == "__main__":
    qs, log = extract(sys.argv[1], sys.argv[2])
    out = pathlib.Path(sys.argv[2])
    (out / "questions.raw.json").write_text(json.dumps(qs, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "extracao.log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(qs), "questões;", len(log), "com avisos", file=sys.stderr)
