---
name: Banco ENEM
description: Sistema "Caderno de prova". Chão de papel quente, cartões brancos com filete e sombra leve, uma cor por área do conhecimento, títulos e enunciado em serifa (Source Serif 4), interface em Inter, alternativas como bolhas de cartão-resposta.
colors:
  # Claro
  bg: "#f4f1ea"      # papel
  card: "#fffdf9"    # cartões
  sunk: "#ebe6da"    # trilhos, blocos de estatística
  ink: "#1d1b16"
  ink-2: "#5d584e"
  ink-3: "#8a8478"
  line: "#e2dccf"
  line-2: "#d3cbbb"
  ok: "#16834f"
  bad: "#c4362b"
  # Acento por área (claro / escuro)
  CN: "#13795b / #3fcf95"
  MT: "#2852c8 / #7aa0ff"
  CH: "#b4531a / #f5934f"
  LC: "#f2bf1d / #ffd23f (texto #8a6500 no claro, tinta escura sobre o amarelo)"
  # Escuro
  bg-dark: "#12110e"
  card-dark: "#1c1a16"
  ink-dark: "#f2eee5"

typography:
  serif: '"Source Serif 4", Georgia, serif — h1, h2, enunciado, nota'
  sans: '"Inter", -apple-system, "Segoe UI", Roboto, sans-serif — interface'
  mono: 'ui-monospace, Menlo, Consolas — cronômetro'
  h1: "clamp(36px, 5.2vw, 56px) / 1.05 / 600 / -0.02em, serifa"
  h2: "clamp(26px, 3vw, 32px) / 1.15 / 600, serifa"
  enunciado: "19px / 1.6 serifa (17px no celular)"

radius:
  sm: "10px"
  md: "16px"
  lg: "22px"
  pill: "999px"
---

# Design: Caderno de prova

`styles.css` é a fonte da verdade; este arquivo descreve o sistema. Se divergirem, vale o CSS e este arquivo é corrigido. O sistema anterior (Apple HIG, um azul só) foi aposentado em v10; cópia em `backup/antes-redesign-2026-10-24/`.

## 1. Ideia

Ferramenta de estudo usada no celular, muitas vezes à noite. A tela lembra a prova impressa: papel, texto serifado, bolhas de cartão-resposta. A cor diz em que área o estudante está.

1. **Conteúdo primeiro.** O enunciado é o maior texto da tela, numa "folha" (`.sheet`).
2. **Uma cor por área.** `--acc` vem de `data-area` em `<html>` (posto por `home`, `materia`, `topico` e `test`) e nas abas. Ela marca ação principal, seleção, foco e progresso. Fora isso, só tinta neutra e os estados ok/erro.
3. **Claro e escuro juntos** por `prefers-color-scheme`.

## 2. Cores

Só existem os tokens de `:root`, o bloco escuro e as regras `[data-area]`. Nunca escrever hex cru num componente. `--acc-soft` e `--acc-line` derivam de `--acc` por `color-mix` e são redeclarados em `[data-area]`, senão as abas herdariam a cor da página. Texto na cor da área usa `--acc-ink` (igual a `--acc`, exceto o amarelo de Linguagens no claro, que escurece para `#8a6500`); sobre o amarelo cheio, `--on-acc` é tinta escura.

- Tags e alternativas corrigidas usam fundo tingido (`--ok-bg`, `--bad-bg`) com texto na cor cheia; a cor nunca é o único sinal ("Acertou", "Errou", "Em branco", "gabarito", "sua resposta").
- Sem gradientes decorativos. Os únicos gradientes são o anel da nota (`conic-gradient`) e o selo do logo.

## 3. Tipografia

- Serifa (Source Serif 4, Google Fonts) em h1, h2, enunciado, nomes das áreas, trechos das questões e nota.
- Inter em toda a interface (botões, rótulos, metadados). Peso máximo 700, só em rótulos curtos e números.
- Números (nota, tempo, contagens) com `tabular-nums`.

## 4. Forma e espaço

- Cartões: `--card`, filete `1px var(--line)`, raio 22px, `--shadow`. Painel da área ganha faixa superior de 5px na cor da área.
- Itens de matéria e tópico: cartão com borda esquerda de 4px na cor da área e seta "›".
- Escala de espaço 8/16/24/32/48/80.

## 5. Componentes

- **Áreas**: as quatro abas (`role="tablist"`) são cartões com sigla (`data-sigla`) e contagem (`data-n`) via pseudo-elementos, para não mudar o `textContent`. A selecionada continua branca, com contorno na cor da área e a sigla cheia nessa cor.
- **Modos**: trilho afundado com a opção ativa em cartão branco.
- **Botões**: pílula. `.primary` cheio na cor da área; `.btn` contornado; `.back` como link.
- **Barra do simulado**: fixa, translúcida, cronômetro em pílula, progresso de 4px de ponta a ponta.
- **Alternativas**: linha com borda de 1,5px e bolha com a letra; marcada fica com borda e fundo da área e bolha cheia.
- **Mapa de questões**: quadrados de 40px num trilho; respondida tingida, atual cheia.
- **Resultado**: cartão central com anel (`.ring`, `--p` = acertos/total) e a nota em serifa; estatísticas em blocos afundados.
- **Diálogo**: `<dialog>` nativo em cartão, ações lado a lado. Nunca `confirm()` ou `alert()`.

## 6. Movimento

- Animação só com `transform` e `opacity`, curvas `--ease-out` / `--ease-in-out`. Mudança de cor é instantânea.
- Toque com `scale(0.97)`; cartões sobem 2px no hover de mouse.
- `prefers-reduced-motion` remove deslocamentos e deixa só fade.

## 7. Acessibilidade

- Foco: `outline: 2px solid var(--acc)`, offset 2px. Nunca `outline: none` fora do `#app`.
- Todo controle é `<button>`, `<a>`, `<input>` ou `<select>` real. Alvos de pelo menos 44px.
- Troca de tela move o foco para `#app`.

## 8. Ícone e PWA

- `icon.svg` mantém o selo azul com o "E"; o logo na tela é desenhado em CSS na cor da área.
- `manifest.json` e `theme-color`: `#f4f1ea` no claro, `#12110e` no escuro.
