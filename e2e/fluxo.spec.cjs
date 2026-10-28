"use strict";
/* Fluxo crítico no navegador real: início, simulado, resultado, correções,
   Suas respostas e navegação por conteúdo, sem erro no console. Junta a
   cobertura de js/ (V8) em coverage/lcov.info para o Codecov. */
const { test, expect } = require("@playwright/test");
const cobertura = require("./cobertura.cjs")();

let erros;
test.beforeEach(async ({ page }) => {
  erros = [];
  page.on("pageerror", (e) => erros.push(e.message));
  page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
  await page.coverage.startJSCoverage({ resetOnNavigation: false });
  await page.goto("./");
  await expect(page.locator("main .skeleton")).toHaveCount(0); // banco carregado
});

test.afterEach(async ({ page }) => {
  await cobertura.add(await page.coverage.stopJSCoverage());
  expect(erros, "erros no console").toEqual([]);
});

test("simulado aleatório do início ao resultado", async ({ page }) => {
  await page.getByRole("button", { name: "Simulado aleatório" }).click();
  await page.getByRole("group", { name: "Quantidade de questões" }).getByRole("button", { name: "5", exact: true }).click();
  await page.getByRole("button", { name: "Fazer simulado" }).click();

  for (let i = 0; i < 5; i++) {
    await page.locator(".alt").first().click();
    await page.getByRole("button", { name: i < 4 ? "Próxima" : "Finalizar simulado" }).click();
  }
  await expect(page.locator(".res .score")).toHaveText(/^\d{3}$/);
  await page.getByRole("button", { name: "Ver correções" }).click();
  await expect(page.getByRole("button", { name: "Voltar ao resultado" }).first()).toBeVisible();

  // O simulado feito aparece em Suas respostas (localStorage).
  await page.goto("./");
  await page.locator("#nav-resp:visible, .top button:visible").filter({ hasText: "Suas respostas" }).first().click();
  await expect(page.getByRole("list", { name: "Simulados feitos" }).getByRole("button")).toHaveCount(1);
});

test("deixar questão em branco pede confirmação", async ({ page }) => {
  await page.getByRole("button", { name: "Simulado aleatório" }).click();
  await page.getByRole("group", { name: "Quantidade de questões" }).getByRole("button", { name: "5", exact: true }).click();
  await page.getByRole("button", { name: "Fazer simulado" }).click();
  await page.getByRole("group", { name: "Ir para a questão" }).getByRole("button").last().click();
  await page.getByRole("button", { name: "Finalizar simulado" }).click();
  const dialogo = page.getByRole("dialog", { name: "Ainda há questões em branco" });
  await expect(dialogo).toBeVisible();
  await dialogo.getByRole("button", { name: "Continuar prova" }).click();
  await expect(dialogo).toHaveCount(0);
});

test("navegação por conteúdo até a lista de questões do tópico", async ({ page }) => {
  await page.locator(".item.sub").first().click();
  await page.locator(".item.top-item").first().click();
  await expect(page.getByRole("list", { name: "Questões do tópico" }).or(page.locator(".qlist"))).toBeVisible();
  await page.locator(".btn.back").first().click();
  await expect(page.locator(".item.top-item").first()).toBeVisible();
});

test("imagens das questões carregam sob demanda", async ({ page }) => {
  await page.locator(".item.sub").first().click();
  await page.locator(".item.top-item").first().click();
  const semLazy = await page.locator("img.q:not([loading=lazy])").count();
  expect(semLazy).toBe(0);
});
