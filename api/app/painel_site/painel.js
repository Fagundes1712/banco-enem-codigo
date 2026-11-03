"use strict";
/* Página do painel: só desenha os totais que a API devolve. Sem editar, apagar ou exportar. */
const $ = (id) => document.getElementById(id);
const TAXA_PIX_CENTAVOS = 80;

const el = (tag, classe, texto) => {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
};
const inteiro = (n) => Number(n).toLocaleString("pt-BR");
const reais = (c) => (c / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const data = (d) => new Date(`${d}T00:00:00`).toLocaleDateString("pt-BR");

function grafico(titulo, linhas, valor, formato = inteiro) {
  const caixa = el("section");
  caixa.append(el("h2", "", titulo));
  if (!linhas.length) caixa.append(el("p", "vazio", "Nada ainda."));
  const maior = Math.max(1, ...linhas.map(valor));
  for (const l of linhas) {
    const linha = el("div", "linha");
    const trilho = el("div", "trilho");
    const barra = el("div", "barra");
    barra.style.width = `${(valor(l) / maior) * 100}%`;
    trilho.append(barra);
    linha.append(el("span", "", data(l.inicio)), trilho, el("span", "valor", formato(valor(l))));
    caixa.append(linha);
  }
  return caixa;
}

function resumo(itens) {
  const caixa = el("div", "resumo");
  for (const [rotulo, valor] of itens) {
    const item = el("div", "", rotulo);
    item.prepend(el("strong", "", valor));
    caixa.append(item);
  }
  return caixa;
}

function desenha(t) {
  const ativos = t.assinantes.reduce((s, a) => s + a.ativos, 0);
  const naoRenovaram = t.assinantes.reduce((s, a) => s + a.nao_renovaram, 0);
  const porPlano = t.assinantes.map((a) => [`Ativos no ${a.plano}`, inteiro(a.ativos)]);
  const { contas, assinantes } = t.conversao;
  const taxa = contas ? `${((assinantes / contas) * 100).toFixed(1).replace(".", ",")}%` : "—";
  const liquido = (f) => f.centavos - f.pagamentos * TAXA_PIX_CENTAVOS;
  const doPlano = (plano) => t.uso.filter((u) => u.plano === plano);
  $("graficos").replaceChildren(
    resumo([["Assinantes ativos", inteiro(ativos)], ...porPlano, ["Não renovaram", inteiro(naoRenovaram)], ["Conversão", taxa]]),
    grafico("Contas confirmadas", t.contas, (c) => c.total),
    grafico("Faturamento, menos a taxa do Pix", t.faturamento, liquido, reais),
    grafico("Questões, grátis", doPlano("gratis"), (u) => u.questoes),
    grafico("Questões, Pro", doPlano("pro"), (u) => u.questoes),
    grafico("Minutos, grátis", doPlano("gratis"), (u) => u.minutos),
    grafico("Minutos, Pro", doPlano("pro"), (u) => u.minutos)
  );
}

function carrega() {
  return fetch(`/painel/totais?periodo=${$("periodo").value}`).then((r) => {
    $("entrada").hidden = r.ok;
    $("dados").hidden = !r.ok;
    if (r.ok) return r.json().then(desenha);
  });
}

$("entrada").addEventListener("submit", (e) => {
  e.preventDefault();
  fetch("/painel/entrar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ codigo: $("codigo").value }),
  }).then((r) => {
    $("codigo").value = "";
    if (r.ok) return carrega();
    $("erro").textContent = r.status === 429 ? "Muitas tentativas. Espere 15 minutos." : "Código incorreto.";
  });
});
$("periodo").addEventListener("change", carrega);
carrega();
