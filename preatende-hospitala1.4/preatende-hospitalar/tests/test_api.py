import json


def registrar_e_logar(client, email="api@teste.com"):
    resp = client.post(
        "/api/v1/auth/registrar",
        json={"nome": "Usuário API", "email": email, "senha": "SenhaForte123"},
    )
    assert resp.status_code == 201
    return resp.get_json()["access_token"]


def test_registro_api(client):
    token = registrar_e_logar(client)
    assert token


def test_login_api(client):
    registrar_e_logar(client, "login@teste.com")
    resp = client.post("/api/v1/auth/login", json={"email": "login@teste.com", "senha": "SenhaForte123"})
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_login_api_senha_errada(client):
    registrar_e_logar(client, "senhaerrada@teste.com")
    resp = client.post("/api/v1/auth/login", json={"email": "senhaerrada@teste.com", "senha": "errada123"})
    assert resp.status_code == 401


def test_criar_triagem_via_api(client):
    token = registrar_e_logar(client, "triagem@teste.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/v1/triagens",
        json={"queixa_principal": "Febre alta", "escala_dor": 4, "temperatura": 39.8},
        headers=headers,
    )
    assert resp.status_code == 201
    dados = resp.get_json()
    assert dados["queixa_principal"] == "Febre alta"
    assert dados["classificacao_cor"] in ("vermelho", "laranja", "amarelo", "verde", "azul")


def test_criar_triagem_sem_token_falha(client):
    resp = client.post("/api/v1/triagens", json={"queixa_principal": "Teste"})
    assert resp.status_code == 401


def test_paciente_nao_acessa_fila_api(client):
    token = registrar_e_logar(client, "semfila@teste.com")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/fila", headers=headers)
    assert resp.status_code == 403


def test_dados_invalidos_retornam_400(client):
    token = registrar_e_logar(client, "invalido@teste.com")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/v1/triagens",
        json={"queixa_principal": "Teste", "escala_dor": 99},
        headers=headers,
    )
    assert resp.status_code == 400
