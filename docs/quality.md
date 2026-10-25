# Qualidade

## Verificações
| Comando | O que garante |
|---|---|
| `npm run check` | Sintaxe de `js/*.js` e `sw.js` (`node --check`), no máximo 350 linhas por arquivo de código, `site/public/` igual à raiz. Sem dependências. |
| `npm test` | 148 checks em jsdom: navegação, simulado, Suas respostas, TRI, correção, acessibilidade básica, service worker e integridade do banco real. `BANCO=<arquivo>` testa outro banco (125 checks com fixture). |
| `npm run verify` | Os dois acima. |

Não há lint, verificação de tipos nem build: o projeto é JS puro. ESLint não foi adotado porque exigiria dependências e configuração sem ganho medido; reavaliar se o código crescer.

## Validação manual
Fluxo crítico no navegador: abrir a home, iniciar um simulado aleatório, responder uma alternativa, terminar e ver o resultado. Sem erros no console.

## Revisão
- Mudança não trivial: revisão independente focada no risco (comportamento, testes, acessibilidade).
- Segurança: `docs/prompts/security-review.md` (prompt 13 do toolkit). Relatório privado fora do repositório.

## Melhoria do harness (método inspirado no Harness2)
Quando uma instrução falhar de forma repetida: registrar o caso, criar um candidato de correção descartável, comparar com o atual usando `npm run verify` e o fluxo manual, e só então mudar `AGENTS.md`. Sem falha concreta, nada muda. Fonte: toolkit `docs/tools/23-harness2.md` e prompt 15.
