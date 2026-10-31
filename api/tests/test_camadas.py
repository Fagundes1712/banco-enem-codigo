import logging

from conftest import link


def test_cabecalhos_de_seguranca_em_toda_resposta(cliente):
    for r in (cliente.get("/saude"), cliente.post("/auth/logout", headers={"Origin": "https://outro.site"})):
        assert r.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
        assert r.headers["x-frame-options"] == "DENY" and r.headers["cache-control"] == "no-store"
        assert r.headers["referrer-policy"] == "no-referrer" and r.headers["x-content-type-options"] == "nosniff"
    assert r.status_code == 403  # a segunda foi barrada pela origem e mesmo assim leva os cabeçalhos


def test_troca_de_senha_avisa_o_dono(logado, emails, caplog):
    caplog.set_level(logging.INFO, logger="auditoria")
    logado.post("/auth/esqueci", json={"email": "aluno@exemplo.com", "turnstile": "ok"})
    token = link(emails[-1][2], "nova-senha")
    assert logado.post("/auth/nova-senha", json={"token": token, "senha": "senha-nova-22"}).status_code == 200
    para, assunto, _ = emails[-1]
    assert para == "aluno@exemplo.com" and "foi trocada" in assunto
    assert any('"evento": "senha_trocada"' in r.message for r in caplog.records)


def test_reuso_da_renovacao_avisa_e_gera_alerta(logado, emails, caplog):
    caplog.set_level(logging.INFO, logger="auditoria")
    antigo = logado.cookies.get("renovacao")
    assert logado.post("/auth/refresh").status_code == 200
    logado.cookies.clear()  # manda só o token antigo, como faria quem o copiou
    assert logado.post("/auth/refresh", headers={"Cookie": f"renovacao={antigo}"}).status_code == 401
    assert "Encerramos suas sessões" in emails[-1][1]
    alerta = [r for r in caplog.records if "renovacao_reusada" in r.message]
    assert alerta and alerta[0].levelno == logging.WARNING


def test_auditoria_nao_grava_email_nem_senha(cliente, caplog):
    caplog.set_level(logging.INFO, logger="auditoria")
    cliente.post("/auth/login", json={"email": "ninguem@exemplo.com", "senha": "senha-errada-1", "turnstile": "ok"})
    linhas = [r.message for r in caplog.records if r.name == "auditoria"]
    assert linhas and '"evento": "login_falhou"' in linhas[0]
    assert all("ninguem@exemplo.com" not in t and "senha-errada-1" not in t for t in linhas)
