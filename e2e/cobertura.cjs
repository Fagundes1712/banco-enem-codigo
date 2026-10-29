"use strict";
// Cobertura V8 do Chromium para lcov (Codecov). Os testes juntam no cache;
// o globalTeardown gera coverage/lcov.info uma vez só.
const { CoverageReport } = require("monocart-coverage-reports");

const opcoes = {
  name: "Banco ENEM e2e",
  outputDir: "coverage",
  reports: ["lcovonly", "console-summary"],
  entryFilter: (e) => /\/js\/[^/]+\.js$/.test(e.url),
  sourcePath: (p) => p.replace(/^.*?\/js\//, "js/"),
};

module.exports = () => new CoverageReport(opcoes);
