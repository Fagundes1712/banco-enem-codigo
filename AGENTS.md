# Banco ENEM

Simulados do ENEM com as provas oficiais do INEP (2015–2025, sem 2020). App estático em HTML, CSS e JavaScript puro, sem framework e sem build. Escopo em `PRODUCT.md`.

## Comandos

- Instalar dependência de teste: `npm install` (só jsdom)
- Rodar local: `npm start` e abrir http://localhost:8765 (precisa de HTTP; `file://` não carrega o JSON)
- Testes: `npm test` (jsdom com o banco real + hook do Claude)
- Checagem: `npm run check` (sintaxe, limite de 350 linhas, espelho em `site/public/`)
- Tudo: `npm run verify`
- Espelhar: `npm run mirror`
- Lint, tipos e build: não existem; o projeto é JS puro sem etapa de build.

## Regras do projeto

- Tudo em pt-BR: interface, documentação e commits.
- Visual segue `DESIGN.md` (Caderno de prova, cor por área). Animação só com `transform` e `opacity`, curvas `--ease-out`/`--ease-in-out`, toque com `scale(0.97)`.
- Mudou algo do shell (HTML, CSS, `js/`, `sw.js`, ícone, manifest)? Suba `VERSION` em `sw.js`.
- Depois de mudar arquivos do app, rode `npm run mirror`; `npm run check` acusa espelho desatualizado.
- Nunca embutir JSON em HTML ou JS; os dados ficam em `questions.json` e `taxonomy.json`.
- Não inventar dados: resoluções, gabaritos e classificações vêm das provas oficiais ou ficam vazios.
- A taxonomia tem exatamente 3 níveis (`docs/TAXONOMIA.md`).
- Um commit por etapa.
- Novo recurso externo (script, fonte, serviço) precisa entrar na CSP do `index.html` e do `_headers` e ser avaliado em `docs/privacidade.md`. Estilo dinâmico só por CSSOM (`h()` com `style`), nunca atributo `style` no HTML.

## Fluxo de toda tarefa de código

Pedido de mudança no repositório já autoriza o fluxo inteiro abaixo, sem pedir licença a cada passo. Detalhes, comandos e recuperação em `docs/fluxo.md`.

1. Critérios de aceite primeiro.
2. Procurar issue existente (`gh issue list --search`); criar só se a tarefa muda o repositório e merece rastreio. Perguntas e ajustes mínimos não ganham issue; mudanças pequenas relacionadas vão juntas.
3. Branch `<tipo>/<assunto>` a partir da `main` atualizada. Nunca commitar na `main`.
4. Implementar preservando a arquitetura; `npm run verify` até passar; revisar o diff atrás de regressão.
5. Commits descritivos, `git push -u origin <branch>`, PR pelo modelo (objetivo, alterações, testes, riscos, pendências). `Closes #N` só se concluir a issue; senão `Ref. #N`.
6. Acompanhar `gh pr checks` e corrigir falhas reais; nunca contornar check ou proteção.
7. Merge e deploy de produção só com aprovação do usuário. Depois do merge, conferir o deploy (`npm run pos-deploy`).
8. Atualizar a documentação quando mudar comportamento ou arquitetura.

Parar e perguntar só para: acesso que falta, conflito relevante, decisão de arquitetura, custo, operação destrutiva ou risco alto. Nunca expor segredos.

## Acordos de trabalho

- Leia as instruções e o código relevante antes de editar. Separe fato observado, suposição e decisão.
- Defina critério de aceite e comando de verificação antes de implementar. Correção de bug pede reprodução e teste de regressão quando viável.
- Faça a menor mudança completa (estilo Ponytail). Reuse padrões existentes; não crie abstração nem dependência sem necessidade.
- Conversa curta e clara na língua do usuário (estilo Caveman); código, docs e commits em texto normal.
- Atualize o documento responsável junto com a mudança. Trabalho de várias sessões usa `docs/handoff.md` (modelo em `docs/setup.md`).
- Bloqueio parcial só para o que depende dele; continue o resto autorizado.
- Mudança não trivial ganha revisão independente; segurança usa `docs/prompts/security-review.md`.

## Mapa

| Assunto | Fonte |
|---|---|
| Produto e escopo | `PRODUCT.md` |
| Estrutura e decisões | `docs/architecture.md` |
| Interface | `DESIGN.md` |
| Taxonomia | `docs/TAXONOMIA.md` |
| Dificuldade e nota | `docs/dificuldade.md` |
| Primeiros passos | `docs/onboarding.md` |
| Verificações | `docs/quality.md` |
| Ferramentas e setup do toolkit | `docs/setup.md` |
| Fluxo, CI, deploy e recuperação | `docs/fluxo.md` |
| Segurança, CSP e segredos | `docs/security.md` |
| Ambientes, backup, monitoramento e incidentes | `docs/operacao.md` |
| Privacidade e LGPD | `docs/privacidade.md` |
| O que se aplica de um SaaS e o estado de cada item | `docs/producao.md` |
