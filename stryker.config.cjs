"use strict";
// Teste de mutação sob demanda (npm run mutacao): muda o código das funções
// puras e confere se os testes unitários percebem. Lento; não roda no CI de PR.
module.exports = {
  mutate: ["js/base.js", "js/simulado.js"],
  testRunner: "command",
  commandRunner: { command: "node --test test/unidade.test.cjs" },
  coverageAnalysis: "off",
  reporters: ["clear-text", "html", "progress"],
  thresholds: { high: 80, low: 60, break: null },
  tempDirName: ".stryker-tmp",
};
