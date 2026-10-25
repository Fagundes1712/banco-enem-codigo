# Setup do Vibe Coding Toolkit

- Toolkit: `soumatheusgomes/vibe-coding-toolkit`, revisão `790a895` (2026-10-18). Todos os modelos e guias vieram dessa revisão.
- Aplicado em: 2026-10-24, num contêiner temporário na nuvem (Claude Code), sem GitHub conectado e sem acesso ao PC do usuário.
- Para repetir: rode de novo o prompt 12 do toolkit na raiz do projeto. Ele preserva o que já existe; compare com esta página.

## Antes e depois
| | Antes | Depois |
|---|---|---|
| Instruções | Nenhuma (`AGENTS.md`/`CLAUDE.md` ausentes) | `AGENTS.md` curto + `CLAUDE.md` que o importa |
| Documentos | `DESIGN.md`, `docs/TAXONOMIA.md` | + README, PRODUCT, architecture, onboarding, quality, setup |
| Comandos | `node test/dom.test.cjs` | `npm start / test / check / mirror / verify` |
| Código | `app.js` com 987 linhas | `js/` em 5 arquivos, o maior com 236 linhas |
| Testes | 134 passando | 134 passando + checagem ok + fluxo no navegador sem erros |

## Mapa dos documentos do manifesto
| Destino do toolkit | Neste projeto |
|---|---|
| README.md, PRODUCT.md, AGENTS.md, CLAUDE.md | Criados |
| docs/architecture.md, docs/onboarding.md, docs/quality.md, docs/setup.md | Criados |
| docs/design.md | `DESIGN.md` na raiz já é a fonte canônica; não foi duplicado |

## Matriz de cobertura
Estados: **validado** (rodou aqui), **configurado** (escrito, sem execução), **reusado**, **inaplicável**, **bloqueado**.

| Componente | Estado | Motivo / próxima ação |
|---|---|---|
| AGENTS.md, CLAUDE.md, docs | validado | Links e comandos conferidos |
| Superpowers | validado | 2026-10-24, no PC: `superpowers@claude-plugins-official` 7.0.0, escopo usuário, ativado (`claude plugin list`). Carrega depois de reiniciar o Claude Code |
| Ponytail, Caveman | configurado | Viraram acordos de trabalho no AGENTS.md; plugins não instalados aqui |
| RTK | configurado | 2026-10-24, no PC: `winget install rtk-ai.rtk` → `rtk 1.0.1`, `rtk gain` ok. Hook nativo `rtk hook claude` global (`rtk init -g`, rodado pelo usuário; `rtk init --show` ok). Falta ver uma reescrita em `rtk gain --history` numa sessão nova |
| Context7 | validado | 2026-10-24, no PC: `claude mcp add --scope user --transport http context7 https://mcp.context7.com/mcp`, sem chave (modo anônimo). `claude mcp list`: Connected; `resolve-library-id` e `query-docs` responderam (vitest). Chave própria: `npx ctx7 setup --claude` |
| Graphify | inaplicável | 5 arquivos de JS; grafo não ajuda. Reavaliar se passar de ~30 arquivos |
| Vercel skills / find-skills | inaplicável | Sem React/Next; o conjunto web exige esse stack |
| next-dev-loop, bundle optimizer | inaplicável | Não é Next.js |
| supabase-postgres-best-practices | inaplicável | Sem banco de dados |
| gh-fix-ci | inaplicável | Sem CI; GitHub não conectado |
| differential-review / revisão de segurança | configurado | Prompt em `docs/prompts/security-review.md`; skill não instalada, fallback manual |
| shadcn | inaplicável | Sem React; design próprio em `DESIGN.md` |
| Sentry MCP | inaplicável | Sem backend nem conta escolhida |
| Harness2 (método) | configurado | Procedimento em `docs/quality.md`; sem falha concreta, nada foi alterado. CLI oficial não instalada |
| Browser (agent-browser / DevTools MCP) | reusado | Playwright do ambiente validou o fluxo crítico |
| Memória em camadas | reusado | Memória nativa do projeto (índice `MEMORY.md`, um arquivo por assunto), carregada automaticamente pelo Claude. Fatos com data; aposentar quando mudarem |
| Skills de artefato, skill-creator, plugins oficiais, aia-harness | inaplicável | Sem necessidade concreta |
| Hooks do cliente | inaplicável | Nenhum fluxo pede hook; regras proíbem hooks de Git |
| Quality gates ESLint | inaplicável | JS puro sem dependências; substituído por `scripts/check.cjs`. Reavaliar com crescimento |
| Subagentes | política | Só para partes independentes; trabalho deste setup foi sequencial e feito sem delegação |

## Handoff entre sessões
Para trabalho inacabado, crie `docs/handoff.md` com: objetivo, estado verificado, checagens, pendências, bloqueios e próxima ação. Ao retomar, confira arquivos e `git status` antes de confiar nele. Apague quando terminar.

## Pendências
- Resoluções das questões (vazias; não inventar).
- Prova de 2020 (não veio no zip das provas).
- Revisar 37 classificações marcadas.
- RTK: confirmar numa sessão nova que `git status` é reescrito uma vez (`rtk gain --history`).

## Decisões para revisar
- Adotar ESLint: quando `js/` passar de 10 arquivos ou entrar outra pessoa no projeto.
- Graphify: acima de ~30 arquivos de código.
- Módulos ES em vez de scripts clássicos: se for adotada uma etapa de build.
