# Primeiros passos

1. Tenha Node.js 18+ e Python 3.
2. `npm install` (instala só o jsdom para os testes).
3. `npm start` e abra http://localhost:8765.
4. Antes de cada commit: `npm run mirror` e `npm run verify`.
5. Leia `AGENTS.md` (regras) e `PRODUCT.md` (escopo).

Para recarregar sem o cache antigo do service worker: Ctrl+Shift+R, ou suba `VERSION` em `sw.js`.

Para regenerar o banco a partir das provas: veja o cabeçalho de `tools/extrair.py`. Ele precisa das provas do INEP em PDF e de PyMuPDF.
