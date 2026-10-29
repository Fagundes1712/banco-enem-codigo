from test_pagamentos import compra, webhook


def test_baixar_meus_dados(logado, abacate):
    compra(logado)
    r = logado.get("/conta/dados")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    dados = r.json()
    assert dados["conta"]["email"] == "aluno@exemplo.com"
    assert dados["pagamentos"][0]["plano"] == "mensal" and len(dados["sessoes"]) == 1
    assert "senha" not in r.text


def test_excluir_exige_senha(logado):
    assert logado.post("/conta/excluir", json={"senha": "errada-123"}).status_code == 401
    assert logado.get("/me").status_code == 200


def test_excluir_sem_pagamento_apaga_tudo(logado, emails):
    assert logado.post("/conta/excluir", json={"senha": "senha-forte-1"}).status_code == 200
    assert logado.get("/me").status_code == 401
    # O e-mail fica livre para uma conta nova.
    corpo = {"email": "aluno@exemplo.com", "senha": "senha-forte-1", "turnstile": "ok", "aceite_termos": True}
    assert logado.post("/auth/cadastro", json=corpo).status_code == 202 and len(emails) == 2


def test_excluir_com_pagamento_guarda_so_o_registro_fiscal(logado, abacate):
    cid = compra(logado)
    abacate.paga(cid)
    webhook(logado, cid)
    renovacao = logado.cookies.get("renovacao")
    assert logado.post("/conta/excluir", json={"senha": "senha-forte-1"}).status_code == 200
    logado.cookies.set("renovacao", renovacao, path="/auth")
    assert logado.post("/auth/refresh").status_code == 401
    login = {"email": "aluno@exemplo.com", "senha": "senha-forte-1", "turnstile": "ok"}
    assert logado.post("/auth/login", json=login).status_code == 401
