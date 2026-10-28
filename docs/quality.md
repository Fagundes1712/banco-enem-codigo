# Qualidade

## Verificações
| Comando | O que garante | Onde roda |
|---|---|---|
| `npm run check` | Sintaxe de `js/*.js` e `sw.js`, no máximo 350 linhas por arquivo de código, `site/public/` igual à raiz e os contratos de arquitetura abaixo. Sem dependências. | hook, CI |
| `npm run lint` | Biome (lint de JS e CSS, sem formatador para não reescrever o código) e Knip (arquivos, exports e dependências sem uso). | hook, CI |
| `npm test` | Testes unitários das funções puras (`test/unidade.test.cjs`, `node:test`), 148 checks de integração em jsdom com o banco real (`test/dom.test.cjs`) e o hook do Claude. `BANCO=<arquivo>` testa outro banco. | hook, CI |
| `npm run verify` | Os três acima. Antes de cada push (hook) e no job `verify` do CI. | hook, CI |
| `npx commitlint` | Mensagens de commit do PR: frase de 10 a 100 caracteres, sem ponto final, corpo separado por linha em branco (`commitlint.config.cjs`). Sem prefixo de tipo, como já era o padrão. | CI |
| `npm run e2e` | Playwright no Chromium, desktop e celular, contra o site servido por HTTP: simulado do início ao resultado, correções, Suas respostas, confirmação de questões em branco, navegação por conteúdo e lazy loading das figuras, sem erro no console. Gera `coverage/lcov.info`. | CI (job `e2e`) |
| `npm run mutacao` | Stryker muda o código de `js/base.js` e `js/simulado.js` e confere se os testes unitários percebem. Relatório em `reports/mutation/`. Lento. | sob demanda (Actions › Mutação) |
| `npm run pos-deploy` | O site no ar tem a mesma `VERSION` do `sw.js` local e serve `index.html`, `questions.json` e `taxonomy.json`. | deploy |

Primeira vez na máquina: `npm install` e `npx playwright install chromium`.

## Contratos de arquitetura
Checados em `scripts/check.cjs`; quebrar um deles falha o `check`:
- `js/base.js` é o primeiro script; todo arquivo de `js/` é carregado no `index.html` com `defer` e está no `SHELL_ASSETS` do `sw.js`.
- `js/` usa scripts clássicos: sem `import`, `export` ou `require`.
- Só `js/base.js` busca dados (`getJSON`).
- Nenhum dado de questão (`enunciado`, `gabarito`, `alts`) nem JSON embutido em `index.html` ou `js/`.

## Biome
Regras recomendadas, menos as de estilo que contrariam o código atual (concatenação em vez de template, encadeamento com `&&`, vírgula e atribuição em expressão, especificidade de CSS, `!important` do movimento reduzido). Em `js/`, `noUnusedVariables` e `useConst` ficam desligadas porque os arquivos compartilham o escopo global: o que é declarado num arquivo é usado ou reatribuído em outro.

## Cobertura
O job `e2e` envia `coverage/lcov.info` (cobertura V8 de `js/` no Chromium) ao Codecov. Para ativar: entrar em https://codecov.io com a conta do GitHub e ligar o repositório `banco-enem-codigo`; se o Codecov pedir token, salvar como segredo `CODECOV_TOKEN` do repositório. Sem isso o envio falha sem derrubar o CI. Referência medida em 2026-10-28: 67% das linhas e 61% das funções de `js/`.

## Validação manual
Fluxo crítico no navegador: abrir a home, iniciar um simulado aleatório, responder uma alternativa, terminar e ver o resultado. Sem erros no console. O `npm run e2e` cobre esse fluxo; a validação manual continua para mudanças visuais.

## Revisão
- Mudança não trivial: revisão independente focada no risco (comportamento, testes, acessibilidade).
- Segurança: `docs/prompts/security-review.md` (prompt 13 do toolkit). Relatório privado fora do repositório.

## Melhoria do harness (método inspirado no Harness2)
Quando uma instrução falhar de forma repetida: registrar o caso, criar um candidato de correção descartável, comparar com o atual usando `npm run verify` e o fluxo manual, e só então mudar `AGENTS.md`. Sem falha concreta, nada muda. Fonte: toolkit `docs/tools/23-harness2.md` e prompt 15.
