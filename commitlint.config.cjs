"use strict";
// Padrão do projeto: frase descritiva em pt-BR, sem prefixo de tipo obrigatório.
module.exports = {
  rules: {
    "header-min-length": [2, "always", 10],
    "header-max-length": [2, "always", 100],
    "header-full-stop": [2, "never", "."],
    "body-leading-blank": [2, "always"],
    "footer-leading-blank": [1, "always"],
  },
};
