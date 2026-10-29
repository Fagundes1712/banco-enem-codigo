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
  if (c.bloco) return refazBloco(c.bloco);
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
  salvaBlocos();
}

function salvaBlocos() {
  try {
    localStorage.setItem(RKEY, JSON.stringify(R));
  } catch {
    /* armazenamento indisponível: o bloco fica só nesta sessão */
  }
}

// Refazer atualiza o próprio bloco: as respostas novas substituem as antigas
// e a nota é recalculada com o bloco inteiro. O resultado mostra o bloco todo.
function refazBloco(b) {
  for (const q of T.qs) {
    if (T.ans[q.id]) b.ans[q.id] = T.ans[q.id];
    else delete b.ans[q.id];
  }
  const qs = qsDe(b);
  const certo = (q) => b.ans[q.id] === q.gab;
  b.t = Date.now();
  b.secs = T.secs;
  b.hits = qs.filter(certo).length;
  b.nota = nota(qs.map((q) => [q, certo(q)]));
  R = [b, ...R.filter((x) => x !== b)];
  salvaBlocos();
  Object.assign(T, {
    qs,
    ans: b.ans,
    nota: b.nota,
    hits: b.hits,
    blank: qs.filter((q) => !b.ans[q.id]).length,
  });
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

const qsDe = (b) => {
  const byId = new Map(Q.map((q) => [q.id, q]));
  return b.qs.map((id) => byId.get(id)).filter(Boolean);
};

// Tocar no bloco pergunta se é para rever as correções ou refazer questões.
function abrir(b) {
  const qs = qsDe(b);
  if (!qs.length) return;
  const erradas = qs.filter((q) => b.ans[q.id] !== q.gab);
  escolha("O que fazer com este bloco?", [
    ["ver", "Visualizar respostas"],
    ["refazer", "Refazer questões"],
  ]).then((k) => {
    if (k === "ver") ver(b, qs);
    else if (k === "refazer")
      escolha("Quais questões responder de novo?", [
        ["todas", "Responder todas"],
        ["erradas", "Responder apenas as incorretas", !erradas.length],
      ]).then((r) => {
        if (!r) return;
        start(r === "todas" ? qs : erradas, respostas);
        T.ctx = { top: b.top, bloco: b };
      });
  });
}

// Reabre o bloco como um simulado encerrado: resultado e correções.
function ver(b, qs) {
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

// Quadro de opções empilhadas. Resolve com a chave
// escolhida, ou null ao fechar. Opção com terceiro item verdadeiro fica desligada.
function escolha(titulo, opts) {
  return new Promise((resolve) => {
    const done = (v) => {
      dlg.close();
      dlg.remove();
      resolve(v);
    };
    const dlg = h(
      "dialog",
      { class: "modal escolha", "aria-labelledby": "md-title" },
      h("h2", { id: "md-title" }, titulo),
      h(
        "div",
        { class: "escolhas" },
        opts.map(([k, txt, off]) =>
          h("button", { class: "btn", type: "button", disabled: !!off, onclick: () => done(k) }, txt)
        )
      ),
      h("button", { class: "btn fechar", type: "button", onclick: () => done(null) }, "Cancelar")
    );
    dlg.addEventListener("cancel", (e) => {
      e.preventDefault();
      done(null);
    });
    // Toque fora do quadro (no fundo escurecido) fecha.
    dlg.addEventListener("click", (e) => e.target === dlg && done(null));
    document.body.append(dlg);
    dlg.showModal();
    dlg.querySelector(".escolhas .btn:not(:disabled)").focus();
  });
}

document.getElementById("nav-inicio")?.addEventListener("click", () => Q.length && swap(home));
document.getElementById("nav-resp")?.addEventListener("click", () => Q.length && swap(respostas));
