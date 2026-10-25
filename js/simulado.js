"use strict";

/* ============================= Simulado ============================== */

// qs já vem na ordem da prova; `back` é a tela para onde o estudante volta.
function start(qs, back = home, i = 0) {
  T = { qs, ans: {}, i, t0: Date.now(), back, live: true, ctx: { top: S.topico } };
  clearInterval(tick);
  tick = setInterval(() => {
    const e = document.getElementById("tm");
    if (e) e.textContent = fmt(Math.floor((Date.now() - T.t0) / 1000));
  }, 1000);
  test();
}

function test() {
  const q = T.qs[T.i];
  const n = T.qs.length;
  const done = Object.keys(T.ans).length;
  document.documentElement.dataset.area = q.area;

  mount(
    h(
      "div",
      { class: "bar" },
      h(
        "div",
        { class: "bar-row" },
        h("span", null, "Questão " + (T.i + 1) + " de " + n),
        h(
          "span",
          { class: "bar-acts" },
          h(
            "span",
            { class: "timer", id: "tm", role: "timer", "aria-label": "Tempo decorrido" },
            fmt(Math.floor((Date.now() - T.t0) / 1000))
          ),
          h("button", { class: "btn sair", type: "button", onclick: sair }, "Sair")
        )
      ),
      h(
        "div",
        {
          class: "prog",
          role: "progressbar",
          "aria-valuemin": "0",
          "aria-valuemax": String(n),
          "aria-valuenow": String(done),
          "aria-label": "Progresso do simulado",
        },
        h("i", { style: "transform:scaleX(" + done / n + ")" })
      )
    ),
    h(
      "article",
      { class: "sheet" },
      h(
        "div",
        { class: "q-top" },
        h(
          "p",
          { class: "meta" },
          (AREAS[q.area] ? AREAS[q.area][0] : q.area) +
            (q._ok ? " · " + IX.sub[IX.top[q.topico].materia].nome : "") +
            (q.lang ? " · " + (q.lang === "ingles" ? "Inglês" : "Espanhol") : "")
        ),
        h(
          "div",
          { class: "q-tags" },
          h("span", { class: "q-year", "aria-label": "Ano da prova: ENEM " + q.ano }, "ENEM " + q.ano),
          nivel(q)
        )
      ),
      rich(q.enunciado),
      imgs(q),
      h(
        "fieldset",
        { class: "alts" },
        h("legend", { class: "skip" }, "Alternativas"),
        Object.entries(q.alts).map(([l, t]) =>
          h(
            "label",
            { class: "alt" },
            h("input", {
              type: "radio",
              name: "a",
              value: l,
              checked: T.ans[q.id] === l,
              onchange: () => {
                T.ans[q.id] = l;
                paint();
              },
            }),
            h("span", { class: "bub", "aria-hidden": "true" }, l),
            h("span", null, altc(t))
          )
        )
      )
    ),
    h(
      "div",
      { class: "nav" },
      h(
        "button",
        { class: "btn", disabled: T.i === 0, onclick: () => { T.i--; test(); } },
        "Anterior"
      ),
      T.i < n - 1
        ? h("button", { class: "btn primary", onclick: () => { T.i++; test(); } }, "Próxima")
        : h("button", { class: "btn primary", onclick: finish }, "Finalizar simulado")
    ),
    h(
      "div",
      { class: "grid", role: "group", "aria-label": "Ir para a questão" },
      T.qs.map((x, j) =>
        h(
          "button",
          {
            class: "dot" + (T.ans[x.id] ? " on" : ""),
            "aria-current": j === T.i,
            "aria-label":
              "Questão " + (j + 1) + (T.ans[x.id] ? ", respondida" : ", em branco"),
            onclick: () => {
              T.i = j;
              test();
            },
          },
          j + 1
        )
      )
    )
  );
}

function paint() {
  const n = T.qs.length;
  const done = Object.keys(T.ans).length;
  const bar = document.querySelector(".prog");
  if (bar) {
    bar.setAttribute("aria-valuenow", String(done));
    bar.querySelector("i").style.transform = "scaleX(" + done / n + ")";
  }
  const dot = document.querySelectorAll(".dot")[T.i];
  if (dot) dot.classList.add("on");
}

/* ============================== Nota TRI ============================= */

// Mesmo cálculo do INEP, conferido com as notas reais dos microdados de
// 2022 (diferença mediana de 0,03 ponto): EAP com priori normal padrão,
// logística de 3 parâmetros sem o fator 1,7, e escala própria de cada área
// (nota = k · θ + m). Questão sem parâmetro oficial usa a mediana dos itens
// da área em 2022. Ver docs/dificuldade.md.
const ESCALA = { CN: [113.09, 501.15], CH: [112.3, 501.49], LC: [108.08, 499.98], MT: [129.63, 500.03] };
const PADRAO = {
  CN: { a: 2.005, b: 1.465, c: 0.161 },
  CH: { a: 2.073, b: 0.9, c: 0.16 },
  LC: { a: 2.002, b: 0.669, c: 0.134 },
  MT: { a: 1.907, b: 2.333, c: 0.162 },
};

function tri(items) {
  const area = items[0][0].area;
  let num = 0;
  let den = 0;
  for (let i = -120; i <= 120; i++) {
    const t = i / 20;
    let L = Math.exp((-t * t) / 2);
    for (const [q, ok] of items) {
      const d = q.b == null ? PADRAO[q.area] : q;
      const p = d.c + (1 - d.c) / (1 + Math.exp(-d.a * (t - d.b)));
      L *= ok ? p : 1 - p;
    }
    num += t * L;
    den += L;
  }
  const [k, m] = ESCALA[area];
  return Math.round(k * (num / den) + m);
}

function confirmDialog(msg, txt = {}) {
  return new Promise((resolve) => {
    const done = (v) => {
      document.removeEventListener("keydown", onKey, true);
      dlg.close();
      dlg.remove();
      resolve(v);
    };
    const onKey = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        done(false);
      }
    };
    const cancel = h("button", { class: "btn", onclick: () => done(false) }, txt.cancel || "Continuar prova");
    const ok = h(
      "button",
      { class: "btn primary", onclick: () => done(true) },
      txt.ok || "Finalizar mesmo assim"
    );
    const dlg = h(
      "dialog",
      { class: "modal", "aria-labelledby": "md-title" },
      h("h2", { id: "md-title" }, txt.title || "Ainda há questões em branco"),
      h("p", { class: "note" }, msg),
      h("div", { class: "modal-actions" }, cancel, ok)
    );
    dlg.addEventListener("cancel", (e) => {
      e.preventDefault();
      done(false);
    });
    document.body.append(dlg);
    document.addEventListener("keydown", onKey, true);
    dlg.showModal();
    ok.focus();
  });
}

function finish() {
  const blank = T.qs.length - Object.keys(T.ans).length;
  if (!blank) return closeExam();
  confirmDialog(
    blank === 1
      ? "1 questão sem resposta. Em branco conta como erro na nota."
      : blank + " questões sem resposta. Em branco conta como erro na nota."
  ).then((yes) => {
    if (yes) closeExam();
  });
}

// Sai sem corrigir nem salvar: volta para onde o simulado começou.
function sair() {
  confirmDialog("As respostas desta tentativa não serão salvas.", {
    title: "Sair do simulado?",
    ok: "Sair",
  }).then((yes) => {
    if (!yes || !T.live) return;
    clearInterval(tick);
    T.live = false;
    T.back();
  });
}

function closeExam() {
  clearInterval(tick);
  T.live = false;
  // Guarda a última tentativa de cada questão respondida (em branco não conta).
  for (const q of T.qs)
    if (T.ans[q.id]) H[canon(q)] = { r: T.ans[q.id], ok: T.ans[q.id] === q.gab, t: Date.now() };
  saveHist();
  T.secs = Math.floor((Date.now() - T.t0) / 1000);
  T.hits = T.qs.filter((q) => T.ans[q.id] === q.gab).length;
  T.blank = T.qs.length - Object.keys(T.ans).length;
  T.nota = tri(T.qs.map((q) => [q, T.ans[q.id] === q.gab]));
  guardaBloco();
  result();
}

