from app.triage_engine import classificar_risco


def test_sinal_critico_gera_vermelho():
    cor, pontuacao, motivo = classificar_risco(escala_dor=2, sinais_gravidade=["inconsciencia"])
    assert cor == "vermelho"


def test_saturacao_muito_baixa_gera_vermelho():
    cor, _, _ = classificar_risco(escala_dor=0, saturacao_o2=85)
    assert cor == "vermelho"


def test_dor_toracica_gera_alta_prioridade():
    cor, pontuacao, _ = classificar_risco(escala_dor=5, sinais_gravidade=["dor_toracica"])
    assert cor in ("laranja", "amarelo")
    assert pontuacao > 0


def test_sem_sintomas_gera_baixa_prioridade():
    cor, pontuacao, _ = classificar_risco(escala_dor=0)
    assert cor == "azul"
    assert pontuacao == 0


def test_dor_leve_isolada_gera_verde_ou_azul():
    cor, _, _ = classificar_risco(escala_dor=3)
    assert cor in ("verde", "azul")

    cor_moderada, _, _ = classificar_risco(escala_dor=6)
    assert cor_moderada in ("amarelo", "verde")
