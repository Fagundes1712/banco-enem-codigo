"use strict";

/* ========================== Suas respostas =========================== */

// Cada simulado terminado vira um bloco guardado neste navegador, com as
// respostas dadas, para reabrir as correções depois.
const RKEY = "banco-enem:blocos";
const RMAX = 100;
let R = readBlocos();

function readBlocos() {
  try {
    const x = JSON.parse(localStorage.getItem(RKEY));
    return Array.isArray(x) ? x : [];
  } catch {
    return [];
  }
}

function guardaBloco() {
  const c = T.ctx || {};
  R.unshift({
    t: Date.now(),
    area: T.qs[0].area,
    top: c.top || null,
    qs: T.qs.map((q) => q.id),
    ans: { ...T.ans },
    nota: T.nota,
    hits: T.hits,
    secs: T.secs,
  });
  R = R.slice(0, RMAX);
  try {
    localStorage.setItem(RKEY, JSON.stringify(R));
  } catch {
    /* armazenamento indisponível: o bloco fica só nesta sessão */
  }
}

// Marca na barra lateral a seção atual.
function nav(k) {
  for (const [id, on] of [["nav-inicio", k === "inicio"], ["nav-resp", k === "resp"]]) {
    const e = document.getElementById(id);
    if (!e) continue;
    if (on) e.setAttribute("aria-current", "page");
    else e.removeAttribute("aria-current");
  }
}

const subDe = (b) => (b.top && IX.top[b.top] ? IX.top[b.top].materia : "");

function respostas() {
  clearInterval(tick);
  if (T) T.live = false;
  nav("resp");
  const f = { area: "", sub: "", sit: "todas", ...S.rf };
  if (f.sub && f.area && (IX.sub[f.sub] || {}).area !== f.area) f.sub = "";
  document.documentElement.dataset.area = f.area || S.area;

  const list = R.filter(
    (b) => (!f.area || b.area === f.area) && (!f.sub || subDe(b) === f.sub)
  );
  const subs = (f.area ? [f.area] : Object.keys(AREAS)).flatMap((a) => subsOf(a));
  // Situação diferente de "Todas" lista as questões respondidas, da mais recente.
  const qs = f.sit === "todas" ? [] : respondidas(f);

  const sel = (key, label, opts) =>
    h(
      "label",
      { class: "f" },
      label,
      h(
        "select",
        {
          "data-rf": key,
          onchange: (e) => keep(() => {
            S.rf = { ...f, [key]: e.target.value };
            respostas();
            document.querySelector('select[data-rf="' + key + '"]')?.focus({ preventScroll: true });
          }),
        },
        opts.map(([v, n]) => h("option", { value: v, selected: f[key] === v }, n))
      )
    );

  mount(
    h("div", { class: "top" }, h("span", { class: "brand" }, "Banco ENEM")),
    h("h1", null, "Suas respostas"),
    h(
      "p",
      { class: "lead" },
      "Cada simulado que você termina vira um bloco. Abra um bloco para rever as correções."
    ),
    h(
      "div",
      { class: "filters" },
      sel("area", "Área do conhecimento", [
        ["", "Todas as áreas"],
        ...Object.entries(AREAS).map(([k, [n]]) => [k, n]),
      ]),
      sel("sub", "Matéria", [["", "Todas as matérias"], ...subs.map((s) => [s.id, s.nome])]),
      sel("sit", "Situação", Object.entries(SIT))
    ),
    f.sit === "todas"
      ? [
          h(
            "p",
            { class: "note", id: "n-blocos", role: "status" },
            R.length
              ? plural(list.length, "bloco", "blocos") + " neste filtro."
              : "Você ainda não terminou nenhum simulado. Os blocos aparecem aqui quando terminar."
          ),
          h("ul", { class: "blocos", "aria-label": "Simulados feitos" }, list.map(bloco)),
        ]
      : [
          h(
            "p",
            { class: "note", id: "n-blocos", role: "status" },
            plural(qs.length, "questão", "questões") + " neste filtro. Toque numa para refazer."
          ),
          h(
            "ol",
            { class: "qlist", "aria-label": "Questões respondidas" },
            qs.map((q, j) => qcard(q, () => start(qs.slice(), respostas, j)))
          ),
        ]
  );
}

// Última resposta de cada questão (histórico), com os filtros de área e matéria.
function respondidas(f) {
  const byId = new Map(Q.map((q) => [q.id, q]));
  return Object.entries(H)
    .filter(([, r]) => (f.sit === "resp" ? true : f.sit === "ok" ? r.ok : !r.ok))
    .sort((a, b) => (b[1].t || 0) - (a[1].t || 0))
    .map(([id]) => byId.get(id))
    .filter(
      (q) =>
        q && (!f.area || q.area === f.area) && (!f.sub || (q._ok && IX.top[q.topico].materia === f.sub))
    );
}

function bloco(b) {
  const t = b.top && IX.top[b.top];
  const mat = t ? IX.sub[t.materia].nome : AREAS[b.area] ? AREAS[b.area][0] : b.area;
  const n = b.qs.length;
  const dt = new Date(b.t);
  return h(
    "li",
    null,
    h(
      "button",
      { class: "bloco", type: "button", "data-area": b.area, onclick: () => abrir(b) },
      h("span", { class: "bloco-nota" }, h("small", null, "nota"), String(b.nota)),
      h(
        "span",
        { class: "bloco-txt" },
        h("span", { class: "bloco-mat" }, mat),
        h(
          "span",
          { class: "bloco-tema" },
          t
            ? plural(n, "questão", "questões") + " de " + t.nome
            : plural(n, "questão aleatória", "questões aleatórias")
        ),
        h(
          "span",
          { class: "bloco-meta" },
          dt.toLocaleDateString("pt-BR") +
            " às " +
            dt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) +
            " · " +
            fmt(b.secs)
        )
      ),
      h("span", { class: "bloco-placar", "aria-label": b.hits + " acertos de " + n }, b.hits + "/" + n)
    )
  );
}

// Reabre o bloco como um simulado encerrado: resultado e correções.
function abrir(b) {
  const byId = new Map(Q.map((q) => [q.id, q]));
  const qs = b.qs.map((id) => byId.get(id)).filter(Boolean);
  if (!qs.length) return;
  T = {
    qs,
    ans: b.ans,
    nota: b.nota,
    hits: b.hits,
    secs: b.secs,
    blank: qs.filter((q) => !b.ans[q.id]).length,
    back: respostas,
    live: false,
  };
  corr();
}

document.getElementById("nav-inicio")?.addEventListener("click", () => Q.length && swap(home));
document.getElementById("nav-resp")?.addEventListener("click", () => Q.length && swap(respostas));
