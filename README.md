# Banco ENEM

Simulados com as questões oficiais do ENEM (INEP, 2015–2025, sem 2020), separadas por área, matéria e tópico, com gabarito, correção questão a questão e nota estimada por TRI. Funciona offline depois da primeira visita.

## Rodar

```bash
npm start          # python3 -m http.server 8765
# abra http://localhost:8765
```

Precisa ser servido por HTTP; abrir o `index.html` direto não carrega as questões.

## Verificar

```bash
npm install        # só jsdom, para os testes
npm run verify     # checagem + 148 testes
```

Mais em [docs/onboarding.md](docs/onboarding.md). Regras para agentes e pessoas em [AGENTS.md](AGENTS.md).
