def registrar_paciente(client, email="paciente@teste.com"):
    return client.post(
        "/auth/registrar",
        data={"nome": "Paciente Teste", "email": email, "senha": "SenhaForte123", "confirmar_senha": "SenhaForte123"},
        follow_redirects=True,
    )


def test_pagina_inicial_carrega(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Pré-atendimento" in resp.get_data(as_text=True) or "pré-atendimento" in resp.get_data(as_text=True).lower()


def test_registro_e_login_de_paciente(client):
    resp = registrar_paciente(client)
    assert resp.status_code == 200
    assert "Novo pré-atendimento" in resp.get_data(as_text=True) or "Meu histórico" in resp.get_data(as_text=True)


def test_paciente_nao_acessa_fila(client):
    registrar_paciente(client)
    resp = client.get("/fila")
    assert resp.status_code == 403


def test_criar_pre_atendimento_como_paciente(client):
    registrar_paciente(client)
    resp = client.post(
        "/pre-atendimento/novo",
        data={
            "queixa_principal": "Dor de cabeça forte",
            "sintomas": "Dor latejante há 2 dias",
            "escala_dor": "8",
            "sinais_gravidade": [],
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    texto = resp.get_data(as_text=True)
    assert "Dor de cabeça forte" in texto


def test_rota_protegida_exige_login(client):
    resp = client.get("/pre-atendimento/novo", follow_redirects=True)
    assert resp.status_code == 200
    assert "Entrar" in resp.get_data(as_text=True)
