# Dificuldade e nota

## De onde vêm os dados

Os microdados do Enem (INEP) trazem, em `DADOS/ITENS_PROVA_<ano>.csv`, os parâmetros TRI oficiais de cada item: `NU_PARAM_A` (discriminação), `NU_PARAM_B` (dificuldade) e `NU_PARAM_C` (acerto ao acaso). `tools/microdados.py` acha o caderno azul regular de cada área comparando o gabarito posição a posição com o banco e grava `a`, `b` e `c` nas questões. Item que o INEP abandonou fica sem parâmetro.

```
python3 tools/microdados.py "<pasta DADOS dos microdados>"
```

Os microdados (cerca de 2 GB por ano) não entram no repositório. Hoje o banco tem os parâmetros de 2022 (178 questões). Para os outros anos basta rodar o script na pasta DADOS de cada ano; só o `ITENS_PROVA_<ano>.csv` é lido.

## Nível de dificuldade

Leve < Moderado < Intenso < Radical < Extremo. É o quintil do parâmetro `b` dentro da área, contando todas as questões do banco que têm parâmetro: Leve são os 20% mais fáceis da área, Extremo os 20% mais difíceis. A comparação é dentro da área porque cada área tem escala própria. O selo aparece embaixo do ano; questão sem parâmetro oficial não mostra nível. Rodar o script de novo com mais anos recalcula os quintis.

## Nota

`tri()` em `js/simulado.js` reproduz o cálculo do INEP:

- logística de 3 parâmetros sem o fator 1,7: `P(θ) = c + (1 − c) / (1 + e^(−a(θ − b)))`;
- EAP com priori normal padrão, θ de −6 a 6 em passos de 0,05;
- escala de cada área: `nota = k · θ + m`.

| Área | k | m |
|---|---|---|
| CN | 113,09 | 501,15 |
| CH | 112,30 | 501,49 |
| LC | 108,08 | 499,98 |
| MT | 129,63 | 500,03 |

As constantes e a ausência do 1,7 foram ajustadas com 600 participantes reais de cada área do Enem 2022 (respostas e nota oficial do arquivo `MICRODADOS_ENEM_2022.csv`): diferença mediana de 0,03 ponto e máxima de 0,17 ponto. Com o fator 1,7 a diferença mediana passava de 4 pontos. Com os parâmetros de cada questão, a fórmula reproduziu dois participantes reais (CN 425,1 e MT 843,8).

**Mesma régua para todos os anos (decisão do usuário, 2026-10-25):** toda questão, de qualquer ano e mesmo as que têm parâmetro oficial, entra na nota com a mediana dos itens da área na prova mais recente com microdados (hoje 2022: CN a 2,005, b 1,465, c 0,161; CH 2,073, 0,900, 0,160; LC 2,002, 0,669, 0,134; MT 1,907, 2,333, 0,162). Assim um acerto de 2015 vale o mesmo que um de 2025, e a nota depende só de quantas questões o estudante acertou em cada área, na régua da prova recente. Os parâmetros por questão continuam no banco e definem só o nível de dificuldade. Quando chegarem microdados mais novos, atualize `PADRAO` em `js/simulado.js` com as medianas da prova mais recente.

Pontos de referência (45 questões): 0, 15, 30 e 45 acertos dão CN 381, 563, 684, 858; CH 346, 513, 622, 801; LC 329, 498, 595, 773; MT 417, 639, 819, 1009.

Com poucas questões a nota fica perto de 500: o EAP puxa para a média quando há pouca informação, como faria o INEP com uma prova curta.
