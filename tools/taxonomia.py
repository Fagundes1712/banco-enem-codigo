"""Fonte da taxonomia de 3 níveis (área → matéria → grande tópico).

Gera taxonomy.json. Edite aqui, rode `python3 tools/taxonomia.py` e
espelhe o resultado em site/public/. A descrição de cada tópico diz o
que entra nele; os exemplos servem só para orientar a classificação e
NUNCA viram um quarto nível.
"""
import json, re, unicodedata, pathlib

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

T = {
 "LC": ("Linguagens, Códigos e suas Tecnologias", "Linguagens", [
  ("lp", "Língua Portuguesa", [
   ("Interpretação e Compreensão de Textos", "Leitura global, inferência, tema, tese, intenção do autor, charges, tirinhas e textos multimodais quando o foco é o sentido."),
   ("Gêneros e Tipos Textuais", "Reconhecer gênero, finalidade, suporte, público e tipologia (narrar, descrever, argumentar, expor, injuntivo)."),
   ("Gramática e Análise Linguística", "Classes de palavras, morfologia, pontuação, concordância, regência, crase e ortografia usadas a serviço do sentido."),
   ("Coesão, Coerência e Organização Textual", "Conectivos, retomadas, referenciação, progressão e articulação entre partes do texto."),
   ("Sintaxe e Semântica", "Relações sintáticas, sentido de palavras e expressões, polissemia, ambiguidade, sinonímia e efeitos de sentido."),
   ("Variação Linguística", "Variedades regionais, sociais, históricas e situacionais; norma-padrão, preconceito linguístico e adequação."),
   ("Funções da Linguagem", "Função predominante (referencial, emotiva, conativa, poética, fática, metalinguística) e recursos expressivos."),
  ]),
  ("lit", "Literatura", [
   ("Texto Literário e Gêneros Literários", "Linguagem literária, figuras de linguagem, versificação, lírico, épico/narrativo e dramático, sem depender de uma escola."),
   ("Literatura Colonial: Quinhentismo, Barroco e Arcadismo", "Textos de informação e catequese, Barroco (Gregório de Matos, Vieira) e Arcadismo."),
   ("Romantismo", "Poesia e prosa românticas, indianismo, nacionalismo, ultrarromantismo, condoreirismo."),
   ("Realismo, Naturalismo e Parnasianismo", "Machado de Assis, Aluísio Azevedo, Raul Pompeia, Olavo Bilac e afins."),
   ("Simbolismo e Pré-Modernismo", "Cruz e Sousa, Alphonsus de Guimaraens, Euclides da Cunha, Lima Barreto, Monteiro Lobato, Augusto dos Anjos."),
   ("Modernismo", "Semana de 22, gerações de 30 e 45: Oswald, Mário, Drummond, Bandeira, Graciliano, Rachel de Queiroz, Guimarães Rosa, Clarice, Cabral."),
   ("Literatura Contemporânea", "Produção pós-1960: poesia marginal, concretismo, prosa urbana, autoria periférica e contemporânea."),
   ("Literaturas Africanas, Afro-Brasileiras e Indígenas", "Autores africanos de língua portuguesa, literatura afro-brasileira e indígena."),
  ]),
  ("en", "Língua Inglesa", [
   ("Compreensão Leitora em Inglês", "Ideia principal, informação específica, inferência e finalidade de textos em inglês."),
   ("Vocabulário e Expressões em Inglês", "Sentido de palavras, expressões idiomáticas, trocadilhos e recursos linguísticos em contexto."),
   ("Aspectos Culturais e Interculturais em Inglês", "Cultura, identidade e diversidade em países de língua inglesa e relações interculturais."),
  ]),
  ("es", "Língua Espanhola", [
   ("Compreensão Leitora em Espanhol", "Ideia principal, informação específica, inferência e finalidade de textos em espanhol."),
   ("Vocabulário e Expressões em Espanhol", "Sentido de palavras, expressões, falsos cognatos e recursos linguísticos em contexto."),
   ("Aspectos Culturais e Interculturais em Espanhol", "Cultura, identidade e diversidade no mundo hispânico e relações interculturais."),
  ]),
  ("art", "Artes", [
   ("Artes Visuais", "Pintura, escultura, fotografia, gravura, arquitetura e design; leitura de obras e movimentos artísticos."),
   ("Música", "Gêneros, movimentos e funções sociais da música; leitura de letras como manifestação musical."),
   ("Teatro e Dança", "Artes cênicas: teatro, dança, circo e performance como linguagem artística."),
   ("Arte Contemporânea", "Instalação, intervenção urbana, arte conceitual, grafite e arte digital."),
   ("Patrimônio e Cultura Popular", "Manifestações populares, artesanato, festas e patrimônio material e imaterial."),
  ]),
  ("ef", "Educação Física", [
   ("Esporte", "Esporte de rendimento e de lazer, regras, mídia esportiva e inclusão."),
   ("Jogos e Brincadeiras", "Jogos populares, tradicionais e cooperativos."),
   ("Danças e Expressões Corporais", "Dança como prática corporal e cultura do movimento."),
   ("Ginástica e Atividade Física", "Ginásticas, exercício físico e condicionamento."),
   ("Lutas", "Lutas e artes marciais como prática corporal."),
   ("Corpo, Saúde e Estética", "Padrões de beleza, saúde, qualidade de vida e imagem corporal."),
  ]),
  ("tic", "Tecnologias da Informação e Comunicação", [
   ("Linguagem Digital e Hipertexto", "Hipertexto, multimodalidade, memes, emojis e gêneros digitais."),
   ("Redes Sociais e Comunicação em Rede", "Interação em redes, algoritmos, exposição e comunicação mediada."),
   ("Mídia, Informação e Desinformação", "Jornalismo, publicidade em meios digitais, fake news e checagem."),
   ("Ética, Cidadania e Inclusão Digital", "Privacidade, direitos digitais, acesso e exclusão digital."),
  ]),
 ]),
 "CH": ("Ciências Humanas e suas Tecnologias", "Humanas", [
  ("his", "História", [
   ("História Geral — Antiguidade", "Primeiras civilizações, Grécia e Roma antigas."),
   ("História Geral — Idade Média", "Feudalismo, Igreja medieval, Império Bizantino, mundo islâmico, cruzadas, crise do século XIV."),
   ("História Geral — Idade Moderna", "Renascimento, Reformas religiosas, Absolutismo, Mercantilismo e Expansão Marítima."),
   ("História Geral — Iluminismo e Revoluções Burguesas", "Iluminismo, Revoluções Inglesas, Independência dos EUA, Revolução Francesa e Era Napoleônica."),
   ("História Geral — Revolução Industrial", "Revoluções industriais, movimento operário, socialismos e mundo do trabalho no século XIX."),
   ("História Geral — Imperialismo e Século XIX", "Liberalismo, nacionalismos, unificações, neocolonialismo na África e na Ásia."),
   ("História Geral — Guerras Mundiais e Entreguerras", "Primeira e Segunda Guerras, Revolução Russa, crise de 1929, nazifascismo, Holocausto."),
   ("História Geral — Guerra Fria e Descolonização", "Bipolaridade, corrida armamentista, descolonização afro-asiática, fim da URSS."),
   ("História Geral — Mundo Contemporâneo", "Pós-Guerra Fria, conflitos atuais, terrorismo, nova ordem mundial."),
   ("História do Brasil — Colônia", "Povos indígenas no contato, economia açucareira e mineradora, escravidão, revoltas coloniais."),
   ("História do Brasil — Império", "Independência, Primeiro e Segundo Reinados, Regências, abolição, imigração."),
   ("História do Brasil — Primeira República", "Coronelismo, política do café com leite, Canudos, Contestado, Revolta da Vacina, tenentismo."),
   ("História do Brasil — Era Vargas", "Revolução de 1930, Estado Novo, trabalhismo, CLT, propaganda."),
   ("História do Brasil — República de 1946 a 1964", "Populismo, desenvolvimentismo, JK, crise de 1964."),
   ("História do Brasil — Ditadura Militar", "Golpe de 1964, AIs, censura, repressão, resistência, milagre econômico, abertura."),
   ("História do Brasil — Nova República", "Redemocratização, Constituição de 1988, Brasil contemporâneo."),
   ("História da América — Povos Pré-Colombianos", "Maias, astecas, incas e outros povos originários."),
   ("História da América — Colonização", "Colonização espanhola e inglesa, sistemas de trabalho e resistência indígena."),
   ("História da América — Independências", "Independências da América espanhola e do Haiti; caudilhismo."),
   ("História da América — Século XX e Contemporânea", "Revoluções Mexicana e Cubana, ditaduras latino-americanas, populismos, EUA no século XX."),
  ]),
  ("geo", "Geografia", [
   ("Cartografia", "Escalas, projeções, coordenadas, fusos, leitura de mapas, sensoriamento e geotecnologias."),
   ("Geografia Física", "Estrutura geológica, tectônica, relevo, solos, rochas e processos erosivos."),
   ("Climatologia", "Elementos e fatores do clima, massas de ar, fenômenos climáticos, aquecimento global."),
   ("Hidrografia", "Bacias, rios, aquíferos, uso e gestão da água."),
   ("Biomas", "Domínios morfoclimáticos e biomas do Brasil e do mundo, vegetação."),
   ("Meio Ambiente e Sustentabilidade", "Problemas ambientais, conferências, desenvolvimento sustentável, impactos de atividades humanas."),
   ("População", "Demografia, transição demográfica, pirâmides, IDH e indicadores."),
   ("Migrações", "Fluxos migratórios internos e internacionais, refugiados, xenofobia."),
   ("Urbanização", "Cidades, metropolização, rede urbana, segregação socioespacial, problemas urbanos."),
   ("Geografia Agrária", "Estrutura fundiária, agronegócio, agricultura familiar, conflitos no campo, revolução verde."),
   ("Industrialização", "Fases da industrialização, fatores locacionais, desconcentração industrial, modelos produtivos."),
   ("Energia", "Fontes e matrizes energéticas, impactos e geopolítica da energia."),
   ("Globalização", "Redes, fluxos, multinacionais, blocos econômicos, meio técnico-científico-informacional."),
   ("Geopolítica", "Conflitos territoriais, fronteiras, organismos internacionais, ordem mundial."),
   ("Regionalização", "Critérios de regionalização do Brasil e do mundo; regiões geoeconômicas."),
   ("Geografia do Brasil", "Formação territorial e questões brasileiras que não cabem nos tópicos temáticos."),
  ]),
  ("fil", "Filosofia", [
   ("Filosofia Antiga", "Pré-socráticos, sofistas, Sócrates, Platão, Aristóteles e escolas helenísticas."),
   ("Filosofia Medieval", "Patrística, escolástica, relação entre fé e razão (Agostinho, Tomás de Aquino)."),
   ("Filosofia Moderna", "Racionalismo, empirismo, Kant e o pensamento moderno quando o foco é o autor/período."),
   ("Filosofia Contemporânea", "Hegel, Marx, Nietzsche, existencialismo, Escola de Frankfurt, pós-estruturalismo."),
   ("Ética e Moral", "Virtude, dever, utilitarismo, liberdade, bioética e problemas morais."),
   ("Filosofia Política", "Contratualismo, poder, Estado, justiça, democracia, Maquiavel, Hobbes, Locke, Rousseau, Arendt."),
   ("Teoria do Conhecimento", "Epistemologia: verdade, ceticismo, razão, experiência, método."),
   ("Filosofia da Ciência e da Técnica", "Método científico, ciência e tecnologia, crítica à razão instrumental."),
   ("Lógica e Argumentação", "Argumentos, falácias, silogismo, retórica."),
   ("Estética", "Belo, arte e gosto como problema filosófico."),
  ]),
  ("soc", "Sociologia", [
   ("Teorias Sociológicas Clássicas", "Durkheim, Weber, Marx e conceitos fundantes da Sociologia."),
   ("Cultura", "Cultura, identidade, etnocentrismo, relativismo e diversidade cultural."),
   ("Indústria Cultural e Meios de Comunicação", "Cultura de massa, mídia, consumo e sociedade do espetáculo."),
   ("Trabalho", "Divisão do trabalho, fordismo, toyotismo, precarização, uberização."),
   ("Classes Sociais", "Estratificação, mobilidade e estrutura de classes."),
   ("Desigualdade", "Desigualdade social, pobreza, exclusão e políticas de redução."),
   ("Estado", "Formação e funções do Estado, burocracia, políticas públicas."),
   ("Poder", "Relações de poder, dominação, legitimidade, controle social."),
   ("Democracia", "Regimes políticos, participação, representação, eleições."),
   ("Cidadania", "Direitos civis, políticos e sociais; direitos humanos; Constituição."),
   ("Movimentos Sociais", "Movimentos sociais urbanos e rurais, ações coletivas e reivindicações."),
   ("Relações Étnico-Raciais", "Racismo, povos indígenas e quilombolas, ações afirmativas."),
   ("Gênero", "Relações de gênero, feminismos, violência de gênero, diversidade sexual."),
   ("Globalização", "Dimensão social e cultural da globalização."),
   ("Instituições Sociais", "Família, religião, escola, socialização e controle social."),
   ("Violência", "Violência urbana, segurança pública e sistema penal."),
  ]),
 ]),
 "CN": ("Ciências da Natureza e suas Tecnologias", "Ciências da Natureza", [
  ("bio", "Biologia", [
   ("Citologia", "Estrutura celular, membrana, organelas, transporte celular."),
   ("Bioquímica", "Água, sais, carboidratos, lipídios, proteínas, enzimas, vitaminas, ácidos nucleicos."),
   ("Metabolismo Energético", "Fotossíntese, respiração celular e fermentação."),
   ("Divisão Celular", "Mitose, meiose e ciclo celular; câncer como falha do ciclo."),
   ("Genética", "Leis de Mendel, heredogramas, grupos sanguíneos, herança ligada ao sexo, código genético, mutações."),
   ("Biotecnologia", "DNA recombinante, transgênicos, clonagem, células-tronco, PCR, vacinas de nova geração."),
   ("Evolução", "Lamarck, Darwin, teoria sintética, especiação, seleção natural, resistência."),
   ("Ecologia", "Conceitos de população, comunidade, ecossistema, cadeias e teias alimentares, nicho, habitat."),
   ("Dinâmica Ecológica", "Relações ecológicas, sucessão ecológica, dinâmica de populações."),
   ("Ciclos Biogeoquímicos", "Ciclos do carbono, nitrogênio, água, fósforo e oxigênio."),
   ("Impactos Ambientais", "Poluição, eutrofização, desmatamento, efeito estufa, espécies invasoras."),
   ("Conservação Ambiental", "Unidades de conservação, biodiversidade, manejo e recuperação ambiental."),
   ("Fisiologia Humana", "Digestão, respiração, circulação, excreção, sistemas nervoso, endócrino e reprodutor."),
   ("Homeostase", "Regulação de temperatura, glicemia, equilíbrio hídrico e hormonal."),
   ("Imunologia", "Sistema imune, vacinas, soros, alergias, transplantes."),
   ("Saúde Pública", "Saneamento, epidemiologia, prevenção de doenças, políticas de saúde."),
   ("Microbiologia", "Vírus, bactérias, fungos e protozoários como organismos; antibióticos."),
   ("Parasitologia", "Doenças parasitárias, ciclos de vida de parasitas e vetores."),
   ("Botânica", "Grupos vegetais, morfologia e fisiologia das plantas, hormônios vegetais."),
   ("Zoologia", "Grupos animais, características e adaptações."),
   ("Embriologia", "Fecundação, desenvolvimento embrionário, anexos embrionários."),
   ("Histologia", "Tecidos animais e vegetais."),
   ("Classificação Biológica", "Sistemática, taxonomia, cladogramas, reinos e domínios."),
   ("Origem da Vida", "Abiogênese, biogênese, hipóteses sobre a origem da vida."),
   ("Ecotoxicologia", "Bioacumulação, magnificação trófica, agrotóxicos, metais pesados nos organismos."),
  ]),
  ("qui", "Química", [
   ("Matéria e Propriedades", "Estados físicos, propriedades da matéria, densidade, substâncias e misturas."),
   ("Separação de Misturas", "Filtração, destilação, decantação, cromatografia e outros processos."),
   ("Estrutura Atômica", "Modelos atômicos, partículas, isótopos, distribuição eletrônica."),
   ("Tabela Periódica", "Organização e propriedades periódicas."),
   ("Ligações Químicas", "Ligações iônica, covalente e metálica."),
   ("Geometria e Polaridade Molecular", "Geometria molecular, polaridade de ligações e moléculas."),
   ("Interações Intermoleculares", "Forças intermoleculares, solubilidade e pontos de ebulição."),
   ("Funções Inorgânicas", "Ácidos, bases, sais e óxidos: nomenclatura e propriedades."),
   ("Reações Químicas", "Tipos de reação, balanceamento, oxirredução fora de pilhas."),
   ("Estequiometria", "Mol, massa molar, cálculos estequiométricos, rendimento, pureza."),
   ("Gases", "Leis dos gases, equação de Clapeyron, misturas gasosas."),
   ("Soluções", "Concentração, diluição, mistura de soluções, solubilidade."),
   ("Propriedades Coligativas", "Tonoscopia, ebulioscopia, crioscopia, osmose."),
   ("Termoquímica", "Entalpia, lei de Hess, calor de reação, combustíveis."),
   ("Cinética Química", "Velocidade de reação, fatores, catalisadores, energia de ativação."),
   ("Equilíbrio Químico", "Constantes de equilíbrio, deslocamento (Le Chatelier)."),
   ("Equilíbrio Iônico", "pH, pOH, hidrólise salina, solução-tampão, Kps."),
   ("Ácidos e Bases", "Teorias ácido-base (Arrhenius, Brønsted-Lowry, Lewis), força e neutralização."),
   ("Eletroquímica", "Pilhas, baterias, eletrólise, corrosão, potenciais de redução."),
   ("Radioatividade", "Emissões, meia-vida, fissão e fusão nuclear, aplicações."),
   ("Química Orgânica", "Cadeias carbônicas, hibridização, propriedades gerais dos compostos orgânicos."),
   ("Funções Orgânicas", "Identificação e nomenclatura de funções orgânicas."),
   ("Isomeria", "Isomeria plana e espacial."),
   ("Reações Orgânicas", "Adição, substituição, eliminação, oxidação, esterificação, saponificação."),
   ("Polímeros", "Polímeros de adição e condensação, plásticos, borrachas."),
   ("Biomoléculas", "Carboidratos, lipídios, proteínas e ácidos nucleicos sob o olhar químico."),
   ("Química Ambiental", "Poluição química, chuva ácida, tratamento de água e resíduos."),
   ("Química Industrial", "Processos industriais, siderurgia, obtenção de substâncias em escala."),
   ("Química Cotidiana", "Química de alimentos, cosméticos, limpeza e medicamentos sem foco em outro tópico."),
  ]),
  ("fis", "Física", [
   ("Grandezas e Medidas", "Unidades, notação científica, ordem de grandeza, análise dimensional."),
   ("Cinemática", "MRU, MRUV, queda livre, lançamentos, gráficos de movimento."),
   ("Movimento Circular", "Velocidade angular, período, frequência, transmissão por polias e engrenagens."),
   ("Dinâmica", "Leis de Newton, atrito, força resultante, plano inclinado."),
   ("Forças e Equilíbrio", "Equilíbrio de ponto material, forças em sistemas, tração e normal."),
   ("Gravitação", "Leis de Kepler, gravitação universal, satélites."),
   ("Estática", "Equilíbrio de corpo extenso, torque, alavancas, centro de massa."),
   ("Trabalho e Energia", "Trabalho, potência mecânica, rendimento, energias cinética e potencial, conservação."),
   ("Quantidade de Movimento", "Impulso, momento linear, colisões."),
   ("Hidrostática", "Pressão, densidade, Stevin, Pascal, empuxo (Arquimedes)."),
   ("Termologia", "Temperatura, escalas termométricas, dilatação térmica."),
   ("Calorimetria", "Calor sensível e latente, trocas de calor, mudanças de fase."),
   ("Termodinâmica", "Leis da termodinâmica, máquinas térmicas, ciclos, rendimento."),
   ("Transmissão de Calor", "Condução, convecção, irradiação, isolamento térmico."),
   ("Ondulatória", "Elementos de uma onda, equação fundamental, espectro eletromagnético."),
   ("Fenômenos Ondulatórios", "Reflexão, refração, difração, interferência, ressonância, polarização, efeito Doppler."),
   ("Acústica", "Som, altura, intensidade, timbre, tubos e cordas sonoras."),
   ("Óptica", "Óptica geométrica, espelhos, lentes, visão e instrumentos ópticos."),
   ("Eletrostática", "Carga elétrica, eletrização, campo e potencial elétrico."),
   ("Eletrodinâmica", "Corrente, Lei de Ohm, potência elétrica e consumo de energia em aparelhos."),
   ("Circuitos Elétricos", "Associação de resistores (série e paralelo), geradores, receptores, medidores, análise de circuitos."),
   ("Magnetismo", "Ímãs, campo magnético, força magnética."),
   ("Eletromagnetismo", "Indução eletromagnética, transformadores, motores e geradores."),
   ("Física Moderna", "Efeito fotoelétrico, relatividade, física quântica e nuclear."),
   ("Tecnologia e Energia", "Geração e transmissão de energia elétrica, usinas, eficiência energética."),
  ]),
 ]),
 "MT": ("Matemática e suas Tecnologias", "Matemática", [
  ("mat", "Matemática e suas Tecnologias", [
   ("Aritmética e Conjuntos Numéricos", "Operações, frações, MMC/MDC, divisibilidade, potências, razões e proporções simples, conjuntos."),
   ("Porcentagem e Matemática Financeira", "Porcentagem, acréscimos e descontos, juros simples e compostos."),
   ("Álgebra e Equações", "Expressões, equações, inequações e sistemas."),
   ("Funções", "Funções afim, quadrática, exponencial, logarítmica; leitura de gráficos de funções."),
   ("Sequências e Matemática Discreta", "PA, PG, padrões, lógica e contagem simples."),
   ("Análise Combinatória", "Princípio multiplicativo, arranjos, permutações e combinações."),
   ("Geometria Plana", "Áreas, perímetros, ângulos, semelhança, Teorema de Pitágoras, polígonos, círculo."),
   ("Geometria Espacial", "Volumes, áreas de sólidos, planificações, vistas e projeções."),
   ("Geometria Analítica", "Plano cartesiano, distância, retas, circunferência."),
   ("Trigonometria", "Razões trigonométricas, ciclo trigonométrico, funções trigonométricas."),
   ("Estatística", "Média, moda, mediana, desvio, leitura e interpretação de gráficos e tabelas."),
   ("Probabilidade", "Probabilidade simples, condicional e de eventos independentes."),
   ("Grandezas e Medidas", "Unidades de medida, conversões, escalas, regra de três e grandezas proporcionais."),
   ("Matemática Aplicada", "Problemas de contexto que combinam vários tópicos sem predomínio claro; use com parcimônia."),
  ]),
 ]),
}

out = {"versao": 1, "niveis": ["area", "materia", "topico"], "areas": []}
for aid, (nome, curto, subs) in T.items():
    a = {"id": aid, "nome": nome, "curto": curto, "subjects": []}
    for sid, snome, tops in subs:
        s = {"id": aid + "." + sid, "nome": snome, "topics": []}
        for tnome, desc in tops:
            s["topics"].append({"id": s["id"] + "." + slug(tnome), "nome": tnome, "desc": desc})
        a["subjects"].append(s)
    out["areas"].append(a)

ids = [t["id"] for a in out["areas"] for s in a["subjects"] for t in s["topics"]]
assert len(ids) == len(set(ids)), "ids de tópico repetidos"

root = pathlib.Path(__file__).resolve().parent.parent
(root / "taxonomy.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
for a in out["areas"]:
    print(a["id"], sum(len(s["topics"]) for s in a["subjects"]), "tópicos em", len(a["subjects"]), "matérias")
print("total", len(ids))
