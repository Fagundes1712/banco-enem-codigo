# Arquitetura

App estático, sem framework e sem build. Login e assinatura ficam numa API em Python à parte (`api/`), ainda não publicada.

## Arquivos
| Caminho | Papel |
|---|---|
| `index.html` | Casca da página; carrega os scripts de `js/` em ordem com `defer`. |
| `js/base.js` | Constantes, estado global, helpers de DOM, carga do JSON, histórico e índices. |
| `js/inicio.js` | Tela inicial e tela de matéria. |
| `js/topico.js` | Tela de tópico e filtros. |
| `js/simulado.js` | Simulado, cronômetro e cálculo da nota TRI. |
| `js/respostas.js` | Aba "Suas respostas": guarda cada simulado terminado como bloco (`banco-enem:blocos`, até 100), lista com filtros de área e matéria, ao tocar num bloco oferece visualizar as correções ou refazer as questões (todas ou só as incorretas); refazer atualiza o próprio bloco e recalcula a nota. Também liga a barra lateral. |
| `js/resultado.js` | Resultado, correções, atalhos de teclado, `load()`, registro do service worker e captura de erros (Sentry, desligada sem DSN). |
| `styles.css` | Todo o estilo (tokens em `:root`, tema claro e escuro). |
| `sw.js` | Service worker: cache do shell (`VERSION`) e dos dados. |
| `questions.json`, `taxonomy.json` | Dados. Nunca embutir no HTML ou JS. |
| `img/` | Figuras das questões. |
| `site/public/` | Cópia publicável do app (`npm run mirror`). |
| `tools/` | Extrator em Python das provas do INEP e aplicação da classificação. |
| `test/unidade.test.cjs` | Testes unitários das funções puras (`node:test`). |
| `test/dom.test.cjs` | Testes de comportamento em jsdom. |
| `e2e/` | Testes end-to-end com Playwright e cobertura para o Codecov. |
| `scripts/check.cjs` | Checagem sem dependências, com os contratos de arquitetura. |
| `scripts/pos-deploy.cjs` | Conferência do site publicado. |
| `.github/workflows/` | CI (`verify` e `e2e` em PR), mutação sob demanda e deploy para o `banco-enem-app`. |
| `api/` | API em Python (FastAPI): contas com bcrypt e JWT em cookie, assinatura por Pix na AbacatePay. Testes com `pytest`; detalhes em `api/README.md`. |
| `.claude/` | Configuração do Claude Code: permissões e hook `guarda.cjs` (`docs/fluxo.md`). |

## Decisões
- **Scripts clássicos, não módulos ES:** os arquivos de `js/` compartilham o escopo global (`const`/`let` de topo) e precisam carregar na ordem do `index.html`. O teste lê essa mesma ordem. Motivo: manter o app sem build e funcionando como antes da divisão (2026-10-24).
- **Dados fora do código:** JSON buscado com `fetch`, cacheado pelo service worker.
- **Histórico local:** `localStorage`, sem servidor. `banco-enem:hist` guarda a última resposta de cada questão; `banco-enem:blocos` guarda os simulados terminados.

- **Segredos só na API:** senha, tokens, chaves e preço nunca passam pelo JavaScript do site; o JWT vive em cookie `HttpOnly` (2026-10-28, issue #12).

## Pipeline dos dados
`tools/extrair.py` → `tools/recortar.py` → `tools/aplicar_classificacao.py` (lê `tools/classificacao.json`). Taxonomia gerada por `tools/taxonomia.py`. Parâmetros TRI e nível de dificuldade por `tools/microdados.py` (`docs/dificuldade.md`).
