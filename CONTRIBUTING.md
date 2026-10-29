# Como contribuir

1. Leia `AGENTS.md` (regras do projeto) e `docs/fluxo.md` (issue, branch, PR, CI e deploy).
2. Abra ou reuse uma issue pelos modelos de bug ou melhoria.
3. Crie uma branch `<tipo>/<assunto>` a partir da `main` (`feat`, `fix`, `docs`, `chore`, `dados`).
4. Mudou arquivo do app? Rode `npm run mirror` e suba `VERSION` em `sw.js` se for o shell.
5. `npm run verify` precisa passar. Mudou a interface: confira home, simulado e resultado no navegador.
6. Abra o PR pelo modelo. O merge exige o check `verify` verde e aprovação do responsável.

Tudo em pt-BR. Não invente dados de questões: gabaritos, classificações e resoluções vêm das provas oficiais ou ficam vazios. Segurança: `SECURITY.md`.
