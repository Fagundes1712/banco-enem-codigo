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
        h("i", { style: "--v:" + done / n })
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
                guardaAndamento();
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
  guardaAndamento();
}

function paint() {
  const n = T.qs.length;
  const done = Object.keys(T.ans).length;
  const bar = document.querySelector(".prog");
  if (bar) {
    bar.setAttribute("aria-valuenow", String(done));
    bar.querySelector("i").style.setProperty("--v", done / n);
  }
  const dot = document.querySelectorAll(".dot")[T.i];
  if (dot) dot.classList.add("on");
}

/* ================================ Nota =============================== */

// Nota oficial mediana por número de acertos (0 a 45) em cada área, média
// das provas de 2022 a 2025, contada com todos os participantes dos
// microdados do INEP. Toda questão vale o mesmo, de qualquer ano (escolha do
// usuário). Simulado menor que 45 é levado à proporção: 3 de 5 conta como
// 27 de 45. Ver docs/dificuldade.md.
const NOTA_ACERTOS = {
  CN: [338,  341,  349,  364,  371,  381,  392,  405,  418,  433,  449,  467,  485,  503,  521,  538,  553,  567,  580,  592,  602,  612,  622,  631,  640,  648,  657,  665,  673,  681,  689,  698,  706,  714,  723,  732,  742,  752,  762,  773,  786,  803,  820,  841,  864,  887],
  CH: [302,  306,  314,  323,  335,  346,  357,  370,  384,  399,  415,  430,  446,  461,  475,  489,  501,  513,  524,  534,  543,  552,  560,  569,  577,  584,  592,  600,  608,  616,  624,  632,  640,  649,  658,  668,  678,  689,  701,  714,  728,  744,  764,  784,  809,  831],
  LC: [293,  298,  305,  316,  326,  338,  351,  365,  380,  395,  411,  425,  440,  453,  465,  476,  487,  497,  506,  515,  523,  531,  539,  547,  554,  562,  569,  577,  584,  591,  599,  607,  615,  623,  632,  641,  651,  661,  672,  684,  697,  712,  728,  746,  772,  800],
  MT: [338,  340,  347,  355,  364,  375,  387,  400,  415,  433,  454,  477,  503,  530,  557,  581,  602,  621,  638,  653,  667,  680,  692,  704,  715,  726,  737,  747,  758,  768,  779,  789,  799,  810,  822,  833,  845,  858,  871,  886,  900,  917,  932,  949,  963,  976],
};

function nota(items) {
  const t = NOTA_ACERTOS[items[0][0].area];
  const x = (45 * items.filter(([, ok]) => ok).length) / items.length;
  const i = Math.min(44, Math.floor(x));
  return Math.round(t[i] + (t[i + 1] - t[i]) * (x - i));
}

function confirmDialog(msg, txt = {}) {
  return new Promise((resolve) => {
    const done = (v) => {
      document.removeEventListener("keydown", onKey, true);
      dlg.close();
      // Espera a animação de saída (styles.css, .modal) antes de tirar do DOM.
      setTimeout(() => dlg.remove(), 200);
      resolve(v);
    };
    // Esc fecha sem escolher nenhum dos dois botões: resolve null.
    const onKey = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        done(null);
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
      done(null);
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
    largaAndamento();
    clearInterval(tick);
    T.live = false;
    T.back();
  });
}

// Estatística de uso do painel: só duas somas, sem dizer quais questões nem as respostas. Falha não atrapalha o resultado.
function avisaUso() {
  const questoes = T.qs.length - T.blank;
  if (API && questoes) api("/uso", { questoes, minutos: Math.round(T.secs / 60) }).catch(() => {});
}

function closeExam() {
  largaAndamento();
  clearInterval(tick);
  T.live = false;
  // Guarda a última tentativa de cada questão respondida (em branco não conta).
  for (const q of T.qs)
    if (T.ans[q.id]) H[canon(q)] = { r: T.ans[q.id], ok: T.ans[q.id] === q.gab, t: Date.now() };
  saveHist();
  T.secs = Math.floor((Date.now() - T.t0) / 1000);
  T.hits = T.qs.filter((q) => T.ans[q.id] === q.gab).length;
  T.blank = T.qs.length - Object.keys(T.ans).length;
  T.nota = nota(T.qs.map((q) => [q, T.ans[q.id] === q.gab]));
  guardaBloco();
  avisaUso();
  result();
}


/* ======================== Bloco em andamento ======================== */

// O bloco aberto fica guardado neste navegador a cada resposta e troca de
// questão. Se o site fechar, ao voltar o estudante escolhe se continua.
// Terminar ou sair do simulado apaga o registro.
const AKEY = "banco-enem:andamento";

function guardaAndamento() {
  if (!T || !T.live) return;
  const c = T.ctx || {};
  try {
    localStorage.setItem(
      AKEY,
      JSON.stringify({
        qs: T.qs.map((q) => q.id),
        ans: T.ans,
        i: T.i,
        ms: (T.pausa || Date.now()) - T.t0,
        volta: T.back === home ? "home" : T.back === respostas ? "resp" : "top",
        top: c.top || null,
        bloco: c.bloco ? c.bloco.t : null,
      })
    );
  } catch {
    /* armazenamento indisponível: o bloco só vale nesta sessão */
  }
}

function largaAndamento() {
  try {
    localStorage.removeItem(AKEY);
  } catch {
    /* nada guardado */
  }
}

// Fora da tela o relógio para; ao voltar, o tempo parado não conta.
document.addEventListener("visibilitychange", () => {
  if (!T || !T.live) return;
  if (document.hidden) {
    T.pausa = Date.now();
    guardaAndamento();
  } else if (T.pausa) {
    T.t0 += Date.now() - T.pausa;
    T.pausa = null;
  }
});

// Chamado no boot, com o banco carregado.
function retomar() {
  let a = null;
  try {
    a = JSON.parse(localStorage.getItem(AKEY));
  } catch {
    /* registro ilegível: segue sem ele */
  }
  if (!a || !Array.isArray(a.qs)) return;
  const por = new Map(Q.map((q) => [q.id, q]));
  const qs = a.qs.map((id) => por.get(id)).filter(Boolean);
  if (!qs.length) return largaAndamento();
  confirmDialog("Suas respostas e o tempo do bloco ficaram guardados.", {
    title: "Você saiu antes de terminar as questões",
    ok: "Voltar de onde parei",
    cancel: "Abandonar bloco",
  }).then((sim) => {
    if (sim === null) return; // Esc: o bloco segue guardado para a próxima vez
    if (!sim) return largaAndamento();
    const back = a.volta === "resp" ? respostas : a.volta === "top" && IX.top[a.top] ? () => topico(a.top) : home;
    start(qs, back, Math.min(Math.max(0, a.i | 0), qs.length - 1));
    for (const q of qs) if (a.ans && a.ans[q.id]) T.ans[q.id] = a.ans[q.id];
    T.t0 = Date.now() - (Number(a.ms) || 0);
    T.ctx = { top: a.top, bloco: R.find((b) => b.t === a.bloco) };
    test();
  });
}
