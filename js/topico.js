"use strict";

/* ========================= Grande tópico ============================ */

function topico(id) {
  clearInterval(tick);
  if (T) T.live = false;
  const t = IX.top[id];
  const s = IX.sub[t.materia];
  if (S.topico !== id) S.f = {};
  S = { ...S, materia: s.id, topico: id };
  document.documentElement.dataset.area = t.area;
  nav("inicio");

  const all = inTop(id);
  const anul = Q.filter((q) => q._ok && q.topico === id && q.anulada).length;
  const f = { ano: "", n: 5, ...S.f };
  const list = all.filter((q) => !f.ano || String(q.ano) === f.ano);
  // Quantidade na escala 5, 10, 25, 45, só até o que o filtro tem.
  const qtds = QTDS.filter((n) => n <= list.length);
  const qn = qtds.includes(f.n) ? f.n : qtds[qtds.length - 1];

  const nOk = all.filter((q) => sit(q) === "ok").length;
  const nBad = all.filter((q) => sit(q) === "bad").length;
  const nResp = nOk + nBad;

  const anos = {};
  for (const q of all) anos[q.ano] = (anos[q.ano] || 0) + 1;
  const anosK = Object.keys(anos).sort();
  const max = Math.max(1, ...Object.values(anos));

  const sel = (key, label, opts) =>
    h(
      "label",
      { class: "f" },
      label,
      h(
        "select",
        {
          "data-f": key,
          onchange: (e) => keep(() => {
            S.f = { ...f, [key]: e.target.value };
            topico(id);
            document.querySelector('select[data-f="' + key + '"]')?.focus({ preventScroll: true });
          }),
        },
        opts.map(([v, n]) => h("option", { value: v, selected: f[key] === v }, n))
      )
    );

  mount(
    h(
      "div",
      { class: "top" },
      s.topics.length > 1 ? back(s.nome, () => materia(s.id)) : back(AREAS[t.area][0], home)
    ),
    h("p", { class: "eyebrow" }, AREAS[t.area][0] + " · " + s.nome),
    h("h1", null, t.nome),
    h("p", { class: "lead" }, t.desc),
    h(
      "div",
      { class: "stats" },
      h("div", null, h("b", { id: "n-uni" }, String(all.length)), h("span", null, "questões únicas")),
      h("div", null, h("b", null, String(nResp)), h("span", null, "respondidas")),
      h("div", travada({ class: "nota-stat" }), h("b", null, valorNota(notaDe(all))), h("span", null, "nota")),
      h("div", null, h("b", null, String(all.length - nResp)), h("span", null, "não respondidas")),
      h("div", null, h("b", null, String(nOk)), h("span", null, "acertadas")),
      h("div", null, h("b", null, String(nBad)), h("span", null, "erradas"))
    ),
    all.length
      ? h(
          "div",
          { class: "learn" },
          h(
            "div",
            {
              class: "prog",
              role: "progressbar",
              "aria-valuemin": "0",
              "aria-valuemax": String(all.length),
              "aria-valuenow": String(nOk),
              "aria-label": "Progresso de aprendizagem: questões acertadas",
            },
            h("i", { style: "--v:" + nOk / all.length })
          ),
          h(
            "p",
            { class: "note" },
            "Progresso: " + nOk + " de " + all.length + " acertadas" +
              (nResp ? " · aproveitamento de " + Math.round((100 * nOk) / nResp) + "% nas respondidas" : "") +
              "."
          )
        )
      : null,
    anul
      ? h("p", { class: "note" }, plural(anul, "questão anulada fica", "questões anuladas ficam") + " fora dos simulados.")
      : null,
    anosK.length
      ? h(
          "section",
          { class: "dist", "aria-labelledby": "dl" },
          h("h3", { id: "dl" }, "Distribuição por ano"),
          h(
            "ul",
            { class: "rows" },
            anosK.map((a) =>
              h(
                "li",
                { class: "row" },
                h("span", null, "ENEM " + a),
                h("span", { class: "row-bar", "aria-hidden": "true" }, h("i", { style: "--v:" + anos[a] / max })),
                h("b", null, String(anos[a]))
              )
            )
          )
        )
      : null,
    all.length
      ? h(
          "div",
          { class: "filters" },
          sel("ano", "Ano", [["", "Todos os anos"], ...anosK.map((a) => [a, "ENEM " + a])])
        )
      : null,
    h(
      "p",
      { class: "note", id: "n-fil", role: "status" },
      all.length
        ? plural(list.length, "questão", "questões") + " neste filtro."
        : "Ainda não há questões classificadas neste tópico."
    ),
    qtds.length
      ? h(
          "div",
          { class: "qtd" },
          h("div", { id: "ql" }, "Quantidade de questões"),
          h(
            "div",
            { class: "chips", role: "group", "aria-labelledby": "ql" },
            qtds.map((n) =>
              h(
                "button",
                {
                  class: "chip",
                  type: "button",
                  "aria-pressed": n === qn,
                  onclick: () => keep(() => {
                    S.f = { ...f, n };
                    topico(id);
                  }),
                },
                n
              )
            )
          ),
          h(
            "button",
            {
              class: "btn primary",
              onclick: () => start(shuffle(list.slice()).slice(0, qn), () => topico(id)),
            },
            "Fazer " + qn + " questões"
          ),
          h("p", { class: "note" }, "Ou escolha uma questão da lista para começar por ela.")
        )
      : list.length
        ? h("p", { class: "note" }, "Escolha uma questão da lista para começar.")
        : null,
    h(
      "ol",
      { class: "qlist", "aria-label": "Questões do tópico" },
      list.map((q, j) => qcard(q, () => start(list.slice(), () => topico(id), j)))
    )
  );
}

// Cartão de questão das listas (tópico e Suas respostas).
function qcard(q, onclick) {
  const st = sit(q);
  return h(
    "li",
    null,
    h(
      "button",
      { class: "qcard", type: "button", onclick },
      h(
        "span",
        { class: "qcard-head" },
        h(
          "span",
          { class: "meta" },
          "ENEM " + q.ano +
            (q.numero ? " · Questão " + q.numero : "") +
            (q.lang ? " · " + (q.lang === "ingles" ? "Inglês" : "Espanhol") : "")
        ),
        nivel(q),
        h(
          "span",
          { class: "tag " + (st === "ok" ? "ok" : st === "bad" ? "bad" : "nil") },
          st === "ok" ? "Acertou" : st === "bad" ? "Errou" : "Não respondida"
        )
      ),
      h("span", { class: "qcard-text" }, snippet(q.enunciado))
    )
  );
}

function snippet(t) {
  const x = String(t || "").replace(/!\[[^\]]*\]\([^)]+\)/g, "[figura]").replace(/\s+/g, " ").trim();
  return x.length > 180 ? x.slice(0, 177).trimEnd() + "…" : x;
}

