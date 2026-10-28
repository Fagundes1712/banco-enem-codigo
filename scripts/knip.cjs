"use strict";
/* Knip: arquivos, exports e dependências sem uso. */
const { execSync } = require("node:child_process");

// O parser do Knip reserva memória demais no Windows; o modo comum dá o mesmo resultado.
try {
  execSync("knip", { stdio: "inherit", env: { ...process.env, KNIP_DISABLE_RAW_TRANSFER: "1" } });
} catch {
  process.exit(1);
}
