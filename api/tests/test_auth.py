import time

import jwt

from app.db import Usuario, _fabrica
from app.seguranca import confere_senha, emitir_acesso, gerar_hash, ler_acesso
from conftest import link

CONTA = {"email": "aluno@exemplo.com", "senha": "senha-forte-1", "turnstile": "ok"}


def cadastra(cliente, **extra):
    return cliente.post("/auth/cadastro", json={**CONTA, "aceite_termos": True, **extra})


def test_bcrypt_guarda_hash_e_recusa_senha_fora_do_limite():
    h = gerar_hash("senha-forte-1")
    assert h.startswith("$2b$12$") and confere_senha("senha-forte-1", h)
    assert not confere_senha("outra-senha", h)
    assert not confere_senha("á" * 37, h)  # 74 bytes: acima do limite do bcrypt


def test_jwt_recusa_alg_none_assinatura_errada_e_vencido():
    assert ler_acesso(emitir_acesso("u1")) == "u1"
    agora = int(time.time())
    base = {"sub": "u1", "iat": agora, "exp": agora + 60, "iss": "api.bancoenem", "aud": "bancoenem"}
    assert ler_acesso(jwt.encode(base, None, algorithm="none")) is None
    assert ler_acesso(jwt.encode(base, "y" * 40, algorithm="HS256")) is None
    assert ler_acesso(jwt.encode({**base, "exp": agora - 1}, "x" * 40, algorithm="HS256")) is None
    assert ler_acesso(jwt.encode({**base, "aud": "outro"}, "x" * 40, algorithm="HS256")) is None


def test_cadastro_confirmacao_e_login(cliente, emails):
    assert cadastra(cliente).status_code == 202
    para, _, texto = emails[-1]
    assert para == CONTA["email"]
    assert cliente.post("/auth/login", json=CONTA).status_code == 403  # e-mail ainda não confirmado
    assert cliente.post("/auth/confirmar", json={"token": link(texto, "confirmar")}).status_code == 200
    assert cliente.post("/auth/confirmar", json={"token": link(texto, "confirmar")}).status_code == 400  # uso único
    r = cliente.post("/auth/login", json=CONTA)
    assert r.status_code == 200 and "token" not in r.text
    cookies = r.headers.get_list("set-cookie")
    assert all("HttpOnly" in c and "SameSite=strict" in c for c in cookies)
    assert cliente.get("/me").json()["email"] == CONTA["email"]


def test_senha_nunca_fica_no_banco(cliente):
    cadastra(cliente)
    with _fabrica()() as s:
        usuario = s.query(Usuario).one()
    assert CONTA["senha"] not in usuario.senha_hash


def test_cadastro_repetido_nao_revela_conta(cliente, emails):
    cadastra(cliente)
    r = cadastra(cliente)
    assert r.status_code == 202 and len(emails) == 1


def test_cadastro_exige_termos_turnstile_e_senha_valida(cliente):
    assert cadastra(cliente, aceite_termos=False).status_code == 400
    assert cadastra(cliente, turnstile="robo").status_code == 400
    assert cadastra(cliente, senha="curta").status_code == 400


def test_login_errado_tem_mensagem_generica_e_limite(cliente):
    cadastra(cliente)
    inexistente = cliente.post("/auth/login", json={**CONTA, "email": "ninguem@exemplo.com"})
    errada = cliente.post("/auth/login", json={**CONTA, "senha": "senha-errada"})
    assert inexistente.status_code == errada.status_code == 401
    assert inexistente.json() == errada.json()
    for _ in range(4):
        cliente.post("/auth/login", json={**CONTA, "senha": "senha-errada"})
    assert cliente.post("/auth/login", json=CONTA).status_code == 429


def test_pedido_de_outro_site_e_barrado(cliente):
    r = cliente.post("/auth/cadastro", json={**CONTA, "aceite_termos": True}, headers={"Origin": "https://malicioso.exemplo"})
    assert r.status_code == 403


def test_rota_protegida_sem_login(cliente):
    assert cliente.get("/me").status_code == 401


def test_refresh_rotaciona_e_detecta_reuso(logado):
    velho = logado.cookies.get("renovacao")
    assert logado.post("/auth/refresh").status_code == 200
    novo = logado.cookies.get("renovacao")
    assert novo and novo != velho
    # Alguém reaproveita o token velho: todas as sessões caem, inclusive a nova.
    logado.cookies.set("renovacao", velho, path="/auth")
    assert logado.post("/auth/refresh").status_code == 401
    logado.cookies.set("renovacao", novo, path="/auth")
    assert logado.post("/auth/refresh").status_code == 401


def test_logout_revoga_a_sessao(logado):
    renovacao = logado.cookies.get("renovacao")
    assert logado.post("/auth/logout").status_code == 200
    logado.cookies.set("renovacao", renovacao, path="/auth")
    assert logado.post("/auth/refresh").status_code == 401


def test_recuperacao_de_senha(logado, emails):
    sessao_antiga = logado.cookies.get("renovacao")
    assert logado.post("/auth/esqueci", json={"email": CONTA["email"], "turnstile": "ok"}).status_code == 202
    token = link(emails[-1][2], "nova-senha")
    assert logado.post("/auth/nova-senha", json={"token": token, "senha": "senha-nova-22"}).status_code == 200
    assert logado.post("/auth/nova-senha", json={"token": token, "senha": "outra-senha-3"}).status_code == 400
    logado.cookies.set("renovacao", sessao_antiga, path="/auth")
    assert logado.post("/auth/refresh").status_code == 401  # trocar a senha derruba as sessões
    assert logado.post("/auth/login", json={**CONTA, "senha": "senha-nova-22"}).status_code == 200


def test_trocar_senha_invalida_links_antigos(cliente, emails):
    cadastra(cliente)
    for _ in range(2):
        cliente.post("/auth/esqueci", json={"email": CONTA["email"], "turnstile": "ok"})
    primeiro, segundo = (link(e[2], "nova-senha") for e in emails[-2:])
    assert cliente.post("/auth/nova-senha", json={"token": segundo, "senha": "senha-nova-22"}).status_code == 200
    assert cliente.post("/auth/nova-senha", json={"token": primeiro, "senha": "senha-do-atacante"}).status_code == 400


def test_esqueci_nao_revela_conta(cliente, emails):
    r = cliente.post("/auth/esqueci", json={"email": "ninguem@exemplo.com", "turnstile": "ok"})
    assert r.status_code == 202 and emails == []
