# Dificuldade e nota

## De onde vêm os dados

Os microdados do Enem (INEP) trazem, em `DADOS/ITENS_PROVA_<ano>.csv`, os parâmetros TRI oficiais de cada item: `NU_PARAM_A` (discriminação), `NU_PARAM_B` (dificuldade) e `NU_PARAM_C` (acerto ao acaso). `tools/microdados.py` acha o caderno azul regular de cada área comparando o gabarito posição a posição com o banco e grava `a`, `b` e `c` nas questões. Item que o INEP abandonou fica sem parâmetro.

```
python3 tools/microdados.py "<pasta DADOS dos microdados>"
```

Os microdados (2 GB ou mais por ano) não entram no repositório. Hoje o banco tem os parâmetros de todos os anos, 2015 a 2025 (1822 de 1850 questões; os `ITENS_PROVA_<ano>.csv` ficam na raiz do projeto, fora do git). Para outro ano, junte os `ITENS_PROVA_<ano>.csv` numa pasta e rode o script nela; só esses arquivos são lidos.

O script casa as questões pela posição relativa dentro da área, porque em 2016 e 2017 o `CO_POSICAO` do INEP não segue a numeração do caderno (em 2016 as áreas estão com posições trocadas; em 2017 cada área começa em 1 e Linguagens vai de 1 a 50, com o espanhol em 6 a 10). O gabarito precisa conferir em 90% das posições, senão a área fica sem parâmetro.

## Nível de dificuldade

Leve < Moderado < Intenso < Radical < Extremo. É o quintil do parâmetro `b` dentro da área, contando todas as questões do banco que têm parâmetro: Leve são os 20% mais fáceis da área, Extremo os 20% mais difíceis. A comparação é dentro da área porque cada área tem escala própria. O selo aparece embaixo do ano; questão sem parâmetro oficial não mostra nível. Rodar o script de novo com mais anos recalcula os quintis.

Questão sem parâmetro (item abandonado pelo INEP; 9 entre 2022 e 2025) recebe o nível pela porcentagem real de acerto dos participantes, contada por `tools/acerto_por_questao.py` e guardada em `tools/acerto/<ano>.json`: vale a mediana do nível das 10 questões da área com parâmetro e acerto mais parecido. Essas questões ficam com `nivel_por: "acerto"`. A porcentagem de acerto e o parâmetro b andam juntos (correlação de −0,66 a −0,87 por área em 2022 a 2025). De 2015 a 2021 só há o `ITENS_PROVA`, sem as respostas dos participantes, então as 11 questões abandonadas desses anos (3 de 2016, 5 de 2019, 3 de 2021) recebem, a pedido do usuário, a média arredondada do nível das outras questões da mesma prova (ano e área), marcadas com `nivel_por: "media"`. Deram Intenso, exceto duas de Linguagens 2016, que deram Radical.

## Nota

**Regra (decisão do usuário, 2026-10-25): toda questão vale o mesmo, de qualquer ano.** A nota é a mediana oficial das notas dos participantes que tiveram o mesmo número de acertos, em `NOTA_ACERTOS` (`js/simulado.js`). Simulado com menos de 45 questões vai à proporção (3 de 5 conta como 27 de 45) e o valor entre dois números de acertos é interpolado.

Como a tabela foi feita: para cada prova de 2022, 2023, 2024 e 2025, contei os acertos de cada participante com nota (respostas `TX_RESPOSTAS_<área>` contra `TX_GABARITO_<área>`; em Linguagens, o gabarito tem 50 posições e uso as 5 da língua escolhida mais as 40 comuns) e tirei a mediana de `NU_NOTA_<área>` em cada número de acertos. Contagem com menos de 30 participantes (só nas pontas) foi trocada por extrapolação linear dos vizinhos. A tabela final é a média dos quatro anos, forçada a crescer com os acertos.

| Acertos de 45 | CN | CH | LC | MT |
|---|---|---|---|---|
| 0 | 338 | 302 | 293 | 338 |
| 15 | 538 | 489 | 476 | 581 |
| 30 | 689 | 624 | 599 | 779 |
| 45 | 887 | 831 | 800 | 976 |

Variação entre os anos com 30 acertos: CN 674 a 709, CH 600 a 642, LC 587 a 613, MT 756 a 827. Dentro de um ano, 80% dos participantes com 30 acertos ficaram a uns 20 a 30 pontos da mediana, porque a TRI oficial pesa quais questões foram acertadas.

Para atualizar com um ano novo, rode `tools/nota_por_acertos.py` nos microdados desse ano e refaça a média.

### Cálculo exato do INEP (referência)

Com os parâmetros de cada questão, a nota oficial se reproduz assim: logística de 3 parâmetros sem o fator 1,7, `P(θ) = c + (1 − c) / (1 + e^(−a(θ − b)))`, EAP com priori normal padrão de θ = −6 a 6 em passos de 0,05, e `nota = k · θ + m` (CN 113,09 e 501,15; CH 112,30 e 501,49; LC 108,08 e 499,98; MT 129,63 e 500,03). Conferido com 600 participantes por área de 2022 (diferença mediana de 0,03 ponto). O app não usa esse cálculo porque ele dá pesos diferentes a cada questão, e o usuário quer que todas valham o mesmo.
