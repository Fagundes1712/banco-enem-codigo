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

# Cada tópico: (nome, descrição) ou (nome, descrição, [tópicos antigos que
# ele reúne]). A lista de antigos vira `antes` no taxonomy.json, para
# blocos salvos com ids antigos continuarem achando o tópico.
T = {
 "LC": ("Linguagens, Códigos e suas Tecnologias", "Linguagens", [
  ("lp", "Língua Portuguesa", [
   ("Interpretação e Compreensão de Textos", "Leitura global, inferência, tema, tese, intenção do autor, charges, tirinhas e textos multimodais quando o foco é o sentido."),
   ("Gêneros e Tipos Textuais", "Reconhecer gênero, finalidade, suporte, público e tipologia (narrar, descrever, argumentar, expor, injuntivo)."),
   ("Gramática, Sintaxe e Semântica", "Classes de palavras, pontuação, concordância, regência, relações sintáticas, sentido de palavras, polissemia e ambiguidade a serviço do sentido.",
    ["Gramática e Análise Linguística", "Sintaxe e Semântica"]),
   ("Coesão, Coerência e Organização Textual", "Conectivos, retomadas, referenciação, progressão e articulação entre partes do texto."),
   ("Variação Linguística", "Variedades regionais, sociais, históricas e situacionais; norma-padrão, preconceito linguístico e adequação."),
   ("Funções da Linguagem", "Função predominante (referencial, emotiva, conativa, poética, fática, metalinguística) e recursos expressivos."),
  ]),
  ("lit", "Literatura", [
   ("Texto Literário e Gêneros Literários", "Linguagem literária, figuras de linguagem, versificação, lírico, épico/narrativo e dramático, sem depender de uma escola."),
   ("Do Quinhentismo ao Romantismo", "Textos de informação e catequese, Barroco, Arcadismo e Romantismo (indianismo, nacionalismo, ultrarromantismo, condoreirismo).",
    ["Literatura Colonial: Quinhentismo, Barroco e Arcadismo", "Romantismo"]),
   ("Do Realismo ao Pré-Modernismo", "Realismo, Naturalismo, Parnasianismo, Simbolismo e Pré-Modernismo: Machado de Assis, Aluísio Azevedo, Bilac, Cruz e Sousa, Lima Barreto, Euclides da Cunha.",
    ["Realismo, Naturalismo e Parnasianismo", "Simbolismo e Pré-Modernismo"]),
   ("Modernismo", "Semana de 22, gerações de 30 e 45: Oswald, Mário, Drummond, Bandeira, Graciliano, Rachel de Queiroz, Guimarães Rosa, Clarice, Cabral."),
   ("Literatura Contemporânea e Diversidade", "Produção pós-1960 (poesia marginal, concretismo, prosa urbana, autoria periférica) e literaturas africanas de língua portuguesa, afro-brasileira e indígena.",
    ["Literatura Contemporânea", "Literaturas Africanas, Afro-Brasileiras e Indígenas"]),
  ]),
  ("en", "Língua Inglesa", [
   ("Leitura em Inglês", "Compreensão de textos em inglês: ideia principal, informação específica, inferência, vocabulário e expressões em contexto, aspectos culturais e interculturais.",
    ["Compreensão Leitora em Inglês", "Vocabulário e Expressões em Inglês", "Aspectos Culturais e Interculturais em Inglês"]),
  ]),
  ("es", "Língua Espanhola", [
   ("Leitura em Espanhol", "Compreensão de textos em espanhol: ideia principal, informação específica, inferência, vocabulário, falsos cognatos e aspectos culturais do mundo hispânico.",
    ["Compreensão Leitora em Espanhol", "Vocabulário e Expressões em Espanhol", "Aspectos Culturais e Interculturais em Espanhol"]),
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
   ("Jogos, Danças, Ginásticas e Lutas", "Jogos e brincadeiras, dança como prática corporal, ginásticas, exercício físico, lutas e artes marciais.",
    ["Jogos e Brincadeiras", "Danças e Expressões Corporais", "Ginástica e Atividade Física", "Lutas"]),
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
   ("História Geral — Revoluções e Século XIX", "Iluminismo, revoluções burguesas, Revolução Industrial, movimento operário, liberalismo, nacionalismos e imperialismo.",
    ["História Geral — Iluminismo e Revoluções Burguesas", "História Geral — Revolução Industrial", "História Geral — Imperialismo e Século XIX"]),
   ("História Geral — Guerras Mundiais e Entreguerras", "Primeira e Segunda Guerras, Revolução Russa, crise de 1929, nazifascismo, Holocausto."),
   ("História Geral — Guerra Fria e Mundo Atual", "Bipolaridade, descolonização afro-asiática, fim da URSS, pós-Guerra Fria, conflitos atuais e nova ordem mundial.",
    ["História Geral — Guerra Fria e Descolonização", "História Geral — Mundo Contemporâneo"]),
   ("História do Brasil — Colônia", "Povos indígenas no contato, economia açucareira e mineradora, escravidão, revoltas coloniais."),
   ("História do Brasil — Império", "Independência, Primeiro e Segundo Reinados, Regências, abolição, imigração."),
   ("História do Brasil — Primeira República", "Coronelismo, política do café com leite, Canudos, Contestado, Revolta da Vacina, tenentismo."),
   ("História do Brasil — Era Vargas", "Revolução de 1930, Estado Novo, trabalhismo, CLT, propaganda."),
   ("História do Brasil — De 1946 aos Dias Atuais", "Populismo e desenvolvimentismo, golpe de 1964, ditadura militar, redemocratização, Constituição de 1988 e Brasil contemporâneo.",
    ["História do Brasil — República de 1946 a 1964", "História do Brasil — Ditadura Militar", "História do Brasil — Nova República"]),
   ("História da América", "Povos pré-colombianos, colonização espanhola e inglesa, independências, revoluções e ditaduras latino-americanas, EUA no século XX.",
    ["História da América — Povos Pré-Colombianos", "História da América — Colonização", "História da América — Independências", "História da América — Século XX e Contemporânea"]),
  ]),
  ("geo", "Geografia", [
   ("Cartografia", "Escalas, projeções, coordenadas, fusos, leitura de mapas, sensoriamento e geotecnologias."),
   ("Relevo, Solos e Hidrografia", "Estrutura geológica, tectônica, relevo, solos, rochas, processos erosivos, bacias, rios, aquíferos e gestão da água.",
    ["Geografia Física", "Hidrografia"]),
   ("Clima e Biomas", "Elementos e fatores do clima, massas de ar, fenômenos climáticos, aquecimento global, domínios morfoclimáticos e biomas.",
    ["Climatologia", "Biomas"]),
   ("Meio Ambiente e Sustentabilidade", "Problemas ambientais, conferências, desenvolvimento sustentável, impactos de atividades humanas."),
   ("População e Migrações", "Demografia, transição demográfica, indicadores, fluxos migratórios internos e internacionais, refugiados.",
    ["População", "Migrações"]),
   ("Urbanização", "Cidades, metropolização, rede urbana, segregação socioespacial, problemas urbanos."),
   ("Geografia Agrária", "Estrutura fundiária, agronegócio, agricultura familiar, conflitos no campo, revolução verde."),
   ("Indústria, Energia e Transportes", "Industrialização, fatores locacionais, modelos produtivos, fontes e matrizes energéticas, logística e infraestrutura.",
    ["Industrialização", "Energia", "Geografia do Brasil"]),
   ("Globalização", "Redes, fluxos, multinacionais, blocos econômicos, meio técnico-científico-informacional."),
   ("Geopolítica e Regionalização", "Conflitos territoriais, fronteiras, organismos internacionais, ordem mundial e critérios de regionalização.",
    ["Geopolítica", "Regionalização"]),
  ]),
  ("fil", "Filosofia", [
   ("Filosofia Antiga", "Pré-socráticos, sofistas, Sócrates, Platão, Aristóteles e escolas helenísticas."),
   ("Filosofia Medieval", "Patrística, escolástica, relação entre fé e razão (Agostinho, Tomás de Aquino)."),
   ("Filosofia Moderna", "Racionalismo, empirismo, Kant e o pensamento moderno quando o foco é o autor/período."),
   ("Filosofia Contemporânea", "Hegel, Marx, Nietzsche, existencialismo, Escola de Frankfurt, pós-estruturalismo."),
   ("Ética e Moral", "Virtude, dever, utilitarismo, liberdade, bioética e problemas morais."),
   ("Filosofia Política", "Contratualismo, poder, Estado, justiça, democracia, Maquiavel, Hobbes, Locke, Rousseau, Arendt."),
   ("Conhecimento, Ciência e Estética", "Teoria do conhecimento, método científico, ciência e técnica, lógica e argumentação, e a arte como problema filosófico.",
    ["Teoria do Conhecimento", "Filosofia da Ciência e da Técnica", "Lógica e Argumentação", "Estética"]),
  ]),
  ("soc", "Sociologia", [
   ("Teorias Sociológicas Clássicas", "Durkheim, Weber, Marx e conceitos fundantes da Sociologia."),
   ("Cultura", "Cultura, identidade, etnocentrismo, relativismo, diversidade cultural e dimensão cultural da globalização.",
    ["Cultura", "Globalização"]),
   ("Indústria Cultural e Meios de Comunicação", "Cultura de massa, mídia, consumo e sociedade do espetáculo."),
   ("Trabalho", "Divisão do trabalho, fordismo, toyotismo, precarização, uberização."),
   ("Classes Sociais e Desigualdade", "Estratificação, mobilidade, desigualdade social, pobreza, exclusão e políticas de redução.",
    ["Classes Sociais", "Desigualdade"]),
   ("Estado, Poder e Democracia", "Formação e funções do Estado, relações de poder, dominação, regimes políticos, participação e representação.",
    ["Estado", "Poder", "Democracia"]),
   ("Cidadania e Movimentos Sociais", "Direitos civis, políticos e sociais, direitos humanos, movimentos sociais e ações coletivas.",
    ["Cidadania", "Movimentos Sociais"]),
   ("Relações Étnico-Raciais", "Racismo, povos indígenas e quilombolas, ações afirmativas."),
   ("Gênero", "Relações de gênero, feminismos, violência de gênero, diversidade sexual."),
   ("Instituições Sociais e Violência", "Família, religião, escola, socialização, controle social, violência urbana e sistema penal.",
    ["Instituições Sociais", "Violência"]),
  ]),
 ]),
 "CN": ("Ciências da Natureza e suas Tecnologias", "Ciências da Natureza", [
  ("bio", "Biologia", [
   ("Citologia e Bioquímica Celular", "Estrutura celular, membrana, organelas, moléculas da vida, enzimas, mitose e meiose.",
    ["Citologia", "Bioquímica", "Divisão Celular"]),
   ("Metabolismo Energético", "Fotossíntese, respiração celular e fermentação."),
   ("Genética", "Leis de Mendel, heredogramas, grupos sanguíneos, herança ligada ao sexo, código genético, mutações."),
   ("Biotecnologia", "DNA recombinante, transgênicos, clonagem, células-tronco, PCR, vacinas de nova geração."),
   ("Evolução, Origem da Vida e Classificação", "Lamarck, Darwin, teoria sintética, especiação, origem da vida, sistemática e cladogramas.",
    ["Evolução", "Origem da Vida", "Classificação Biológica"]),
   ("Ecologia e Relações Ecológicas", "População, comunidade, ecossistema, cadeias alimentares, relações ecológicas, sucessão e dinâmica de populações.",
    ["Ecologia", "Dinâmica Ecológica"]),
   ("Ciclos Biogeoquímicos", "Ciclos do carbono, nitrogênio, água, fósforo e oxigênio."),
   ("Impactos Ambientais e Conservação", "Poluição, eutrofização, desmatamento, espécies invasoras, unidades de conservação e recuperação ambiental.",
    ["Impactos Ambientais", "Conservação Ambiental"]),
   ("Ecotoxicologia", "Bioacumulação, magnificação trófica, agrotóxicos, metais pesados nos organismos."),
   ("Fisiologia Humana", "Digestão, respiração, circulação, excreção, sistemas nervoso, endócrino e reprodutor, regulação e homeostase.",
    ["Fisiologia Humana", "Homeostase"]),
   ("Embriologia e Histologia", "Fecundação, desenvolvimento embrionário, anexos embrionários e tecidos.",
    ["Embriologia", "Histologia"]),
   ("Imunologia", "Sistema imune, vacinas, soros, alergias, transplantes."),
   ("Microbiologia, Parasitologia e Saúde Pública", "Vírus, bactérias, fungos e protozoários, ciclos de parasitas e vetores, saneamento e prevenção de doenças.",
    ["Microbiologia", "Parasitologia", "Saúde Pública"]),
   ("Botânica", "Grupos vegetais, morfologia e fisiologia das plantas, hormônios vegetais."),
   ("Zoologia", "Grupos animais, características e adaptações."),
  ]),
  ("qui", "Química", [
   ("Matéria e Separação de Misturas", "Estados físicos, propriedades da matéria, densidade, substâncias, misturas e processos de separação.",
    ["Matéria e Propriedades", "Separação de Misturas"]),
   ("Estrutura Atômica e Tabela Periódica", "Modelos atômicos, isótopos, distribuição eletrônica, organização e propriedades periódicas.",
    ["Estrutura Atômica", "Tabela Periódica"]),
   ("Ligações e Interações Intermoleculares", "Ligações químicas, geometria e polaridade molecular, forças intermoleculares, solubilidade e pontos de ebulição.",
    ["Ligações Químicas", "Geometria e Polaridade Molecular", "Interações Intermoleculares"]),
   ("Funções e Reações Inorgânicas", "Ácidos, bases, sais e óxidos, teorias ácido-base, neutralização, tipos de reação e balanceamento.",
    ["Funções Inorgânicas", "Ácidos e Bases", "Reações Químicas"]),
   ("Estequiometria e Gases", "Mol, massa molar, cálculos estequiométricos, rendimento, pureza e leis dos gases.",
    ["Estequiometria", "Gases"]),
   ("Soluções e Propriedades Coligativas", "Concentração, diluição, mistura de soluções, solubilidade, osmose e efeitos coligativos.",
    ["Soluções", "Propriedades Coligativas"]),
   ("Termoquímica e Cinética Química", "Entalpia, lei de Hess, combustíveis, velocidade de reação, catalisadores e energia de ativação.",
    ["Termoquímica", "Cinética Química"]),
   ("Equilíbrio Químico e Iônico", "Constantes de equilíbrio, Le Chatelier, pH, hidrólise, solução-tampão e Kps.",
    ["Equilíbrio Químico", "Equilíbrio Iônico"]),
   ("Eletroquímica", "Pilhas, baterias, eletrólise, corrosão, potenciais de redução."),
   ("Radioatividade", "Emissões, meia-vida, fissão e fusão nuclear, aplicações."),
   ("Química Orgânica e Isomeria", "Cadeias carbônicas, hibridização, funções orgânicas, nomenclatura e isomeria.",
    ["Química Orgânica", "Funções Orgânicas", "Isomeria"]),
   ("Reações Orgânicas, Polímeros e Biomoléculas", "Adição, substituição, oxidação, esterificação, saponificação, polímeros e biomoléculas.",
    ["Reações Orgânicas", "Polímeros", "Biomoléculas"]),
   ("Química Ambiental e Cotidiana", "Poluição química, chuva ácida, tratamento de água e resíduos, processos industriais e química do dia a dia.",
    ["Química Ambiental", "Química Industrial", "Química Cotidiana"]),
  ]),
  ("fis", "Física", [
   ("Cinemática", "MRU, MRUV, queda livre, lançamentos, movimento circular, polias, gráficos de movimento e grandezas.",
    ["Cinemática", "Movimento Circular", "Grandezas e Medidas"]),
   ("Dinâmica, Estática e Gravitação", "Leis de Newton, atrito, equilíbrio, torque, alavancas, leis de Kepler e gravitação.",
    ["Dinâmica", "Forças e Equilíbrio", "Estática", "Gravitação"]),
   ("Energia e Quantidade de Movimento", "Trabalho, potência mecânica, rendimento, conservação da energia, impulso e colisões.",
    ["Trabalho e Energia", "Quantidade de Movimento"]),
   ("Hidrostática", "Pressão, densidade, Stevin, Pascal, empuxo (Arquimedes)."),
   ("Termologia e Calorimetria", "Temperatura, escalas, dilatação, calor sensível e latente, trocas de calor e mudanças de fase.",
    ["Termologia", "Calorimetria"]),
   ("Termodinâmica e Transmissão de Calor", "Leis da termodinâmica, máquinas térmicas, condução, convecção, irradiação e isolamento.",
    ["Termodinâmica", "Transmissão de Calor"]),
   ("Ondas e Fenômenos Ondulatórios", "Elementos da onda, espectro eletromagnético, reflexão, refração, difração, interferência, ressonância e Doppler.",
    ["Ondulatória", "Fenômenos Ondulatórios"]),
   ("Acústica", "Som, altura, intensidade, timbre, tubos e cordas sonoras."),
   ("Óptica e Física Moderna", "Espelhos, lentes, visão, instrumentos ópticos, efeito fotoelétrico, relatividade e física nuclear.",
    ["Óptica", "Física Moderna"]),
   ("Eletrostática e Eletrodinâmica", "Carga, campo, corrente, Lei de Ohm, potência elétrica e consumo de energia em aparelhos.",
    ["Eletrostática", "Eletrodinâmica"]),
   ("Circuitos Elétricos", "Associação de resistores (série e paralelo), geradores, receptores, medidores, análise de circuitos."),
   ("Eletromagnetismo e Geração de Energia", "Ímãs, campo e força magnética, indução, transformadores, motores, usinas e transmissão de energia.",
    ["Magnetismo", "Eletromagnetismo", "Tecnologia e Energia"]),
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
   ("Estatística", "Média, moda, mediana, desvio, leitura e interpretação de gráficos e tabelas.",
    ["Estatística", "Matemática Aplicada"]),
   ("Probabilidade", "Probabilidade simples, condicional e de eventos independentes."),
   ("Grandezas e Medidas", "Unidades de medida, conversões, escalas, regra de três e grandezas proporcionais."),
  ]),
 ]),
}

out = {"versao": 2, "niveis": ["area", "materia", "topico"], "areas": []}
for aid, (nome, curto, subs) in T.items():
    a = {"id": aid, "nome": nome, "curto": curto, "subjects": []}
    for sid, snome, tops in subs:
        s = {"id": aid + "." + sid, "nome": snome, "topics": []}
        for tnome, desc, *antes in tops:
            t = {"id": s["id"] + "." + slug(tnome), "nome": tnome, "desc": desc}
            velhos = [s["id"] + "." + slug(x) for x in (antes[0] if antes else [])]
            if [v for v in velhos if v != t["id"]]:
                t["antes"] = velhos
            s["topics"].append(t)
        a["subjects"].append(s)
    out["areas"].append(a)

ids = [t["id"] for a in out["areas"] for s in a["subjects"] for t in s["topics"]]
assert len(ids) == len(set(ids)), "ids de tópico repetidos"

root = pathlib.Path(__file__).resolve().parent.parent
(root / "taxonomy.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
for a in out["areas"]:
    print(a["id"], sum(len(s["topics"]) for s in a["subjects"]), "tópicos em", len(a["subjects"]), "matérias")
print("total", len(ids))
