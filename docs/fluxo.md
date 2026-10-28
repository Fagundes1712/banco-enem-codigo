# Fluxo de desenvolvimento

Como toda tarefa de código vira issue, branch, PR, checagem e deploy. Código em https://github.com/Fagundes1712/banco-enem-codigo (público, branch `main`). As regras curtas estão em `AGENTS.md`; aqui ficam os detalhes e a configuração.

## Para cada tarefa
1. Entender o pedido e escrever os critérios de aceite.
2. `gh issue list --search "<termos>" --state all`: reusar a issue se já existir. Criar uma (`gh issue create`) quando a tarefa muda o repositório e merece rastreio. Perguntas, explicações e ajustes de uma linha não ganham issue; mudanças pequenas e relacionadas vão juntas.
3. Branch a partir da `main` atualizada: `git switch main && git pull && git switch -c <tipo>/<assunto>`. Tipos: `feat`, `fix`, `docs`, `chore`, `dados`.
4. Implementar, `npm run mirror` se mudou arquivo do app, subir `VERSION` em `sw.js` se mudou o shell.
5. `npm run verify` até passar. Mudou interface: fluxo no navegador (home, simulado, resultado) sem erro no console.
6. Revisar o diff procurando regressão; mudança não trivial ganha revisão independente.
7. Commits descritivos em pt-BR, um por etapa. `git push -u origin <branch>`.
8. `gh pr create` usando o modelo (`.github/pull_request_template.md`): objetivo, alterações, testes, riscos, pendências. `Closes #N` só se o PR conclui a issue; senão `Ref. #N`.
9. `gh pr checks --watch`: falha real é corrigida na mesma branch; nunca contornar.
10. Merge só com aprovação do usuário. Depois do merge, conferir o deploy (`gh run list --workflow Deploy`) e o site (`npm run pos-deploy`).
11. Atualizar a documentação responsável quando mudar comportamento ou arquitetura.

Pedir intervenção só para: acesso que falta, conflito relevante, decisão de arquitetura, custo, operação destrutiva ou risco alto.

## O que está automatizado
| Peça | Onde | O que faz |
|---|---|---|
| Hook do Claude Code | `.claude/settings.json`, `.claude/hooks/guarda.cjs` | Antes de cada comando Bash/PowerShell: bloqueia commit em `main`/`master`, push para `main`/`master` e push forçado; roda `npm run check` antes de commit e `npm run verify` antes de push. Testado por `test/guarda.test.cjs`. |
| Permissões | `.claude/settings.json` | Libera comandos de rotina (testes, git, issues, PRs); pede confirmação para `gh pr merge` e `gh workflow run`; nega push forçado, `reset --hard` e apagar repositório. |
| CI | `.github/workflows/ci.yml` | `npm ci` + `npm run verify` em todo PR e push na `main`. Check obrigatório: `verify`. |
| Deploy | `.github/workflows/deploy.yml` | Copia `site/public/` para `Fagundes1712/banco-enem-app` (GitHub Pages) e roda `npm run pos-deploy`. |
| Pós-deploy | `scripts/pos-deploy.cjs` | Espera o `sw.js` no ar ter a mesma `VERSION` do local (até 10 min) e confere `index.html`, `questions.json` e `taxonomy.json`. |

## Deploy
- Produção: https://fagundes1712.github.io/banco-enem-app/ (Pages do repositório público `banco-enem-app`, branch `main`, raiz).
- Automático depois do CI verde na `main` só com a variável de repositório `DEPLOY_AUTOMATICO=true`. Sem ela, só manual: Actions › Deploy › Run workflow.
- Acesso: chave de deploy SSH com escrita só no `banco-enem-app`; a privada fica no segredo `DEPLOY_KEY_SITE` do repositório de código. Nada de token pessoal.
- Não há ambiente de preview separado: o PR é validado pelo CI e, se precisar, localmente com `npm start`.

## Recuperação
- Site quebrado depois de um deploy: Actions › Deploy › Run workflow com `ref` = último commit bom da `main` (ou `gh workflow run deploy.yml -f ref=<sha>`). Depois, `git revert` do commit ruim num PR.
- Deploy falhou no meio: o `banco-enem-app` só recebe um commit no fim; rodar de novo é seguro.
- Último recurso, à mão: clonar `banco-enem-app`, `git revert HEAD`, `git push`.

## Requisitos de acesso
- `gh` autenticado como `Fagundes1712` com escopos `repo` e `workflow`.
- Proteção da `main` no `banco-enem-codigo`: PR obrigatório, check `verify` verde e atualizado com a `main`, vale também para o administrador, sem push forçado nem exclusão. Funciona no plano gratuito porque o repositório é público.
- O antigo `Fagundes1712/Banco-Enem` (privado) tem arquivos de outros projetos e não é usado.
