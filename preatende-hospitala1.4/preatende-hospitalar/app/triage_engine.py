"""
Motor de classificação de risco do pré-atendimento.

Este módulo implementa uma versão SIMPLIFICADA e educacional, inspirada no
Protocolo de Manchester, para apoiar a priorização de pacientes. Ele NÃO
substitui a avaliação de um profissional de saúde qualificado — serve apenas
para ordenar a fila de pré-atendimento por urgência aparente.

Cores de saída (da mais para a menos urgente):
    vermelho > laranja > amarelo > verde > azul
"""

SINAIS_GRAVIDADE_VALIDOS = {
    "dor_toracica": "Dor no peito",
    "falta_de_ar_grave": "Falta de ar intensa",
    "inconsciencia": "Perda de consciência / não responde",
    "sangramento_intenso": "Sangramento intenso",
    "confusao_mental": "Confusão mental súbita",
    "convulsao": "Convulsão",
    "reacao_alergica_grave": "Reação alérgica grave (inchaço/engasgo)",
    "trauma_grave": "Trauma / acidente grave",
    "gravidez_risco": "Gestante com sangramento ou dor forte",
}


def _clamp(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def classificar_risco(
    escala_dor=0,
    pressao_sistolica=None,
    pressao_diastolica=None,
    frequencia_cardiaca=None,
    frequencia_respiratoria=None,
    temperatura=None,
    saturacao_o2=None,
    sinais_gravidade=None,
):
    """
    Recebe sinais vitais e sintomas relatados e retorna:
        (cor:str, pontuacao:int, motivo:str)

    A pontuação é apenas um score interno (quanto maior, mais grave).
    """
    sinais_gravidade = sinais_gravidade or []
    pontuacao = 0
    motivos = []

    escala_dor = _clamp(int(escala_dor or 0), 0, 10)

    # --- 1. Sinais de alerta imediato (bandeira vermelha) ---
    sinais_criticos = {
        "inconsciencia",
        "sangramento_intenso",
        "reacao_alergica_grave",
        "convulsao",
    }
    if any(s in sinais_criticos for s in sinais_gravidade):
        motivos.append("Sinal de alerta crítico relatado")
        return "vermelho", 100, "; ".join(motivos)

    # Saturação de O2 muito baixa é sempre emergência
    if saturacao_o2 is not None and saturacao_o2 < 90:
        motivos.append(f"Saturação de O2 criticamente baixa ({saturacao_o2}%)")
        return "vermelho", 98, "; ".join(motivos)

    # --- 2. Dor torácica / falta de ar grave -> muito urgente (laranja) na ausência de outros críticos ---
    if "dor_toracica" in sinais_gravidade or "falta_de_ar_grave" in sinais_gravidade:
        pontuacao += 40
        motivos.append("Sintoma cardiorrespiratório de risco")

    if "trauma_grave" in sinais_gravidade:
        pontuacao += 35
        motivos.append("Trauma grave relatado")

    if "confusao_mental" in sinais_gravidade:
        pontuacao += 35
        motivos.append("Confusão mental")

    if "gravidez_risco" in sinais_gravidade:
        pontuacao += 35
        motivos.append("Gestante com sinais de risco")

    # --- 3. Sinais vitais alterados ---
    if saturacao_o2 is not None and saturacao_o2 < 94:
        pontuacao += 25
        motivos.append(f"Saturação de O2 baixa ({saturacao_o2}%)")

    if frequencia_respiratoria is not None and (frequencia_respiratoria >= 28 or frequencia_respiratoria <= 8):
        pontuacao += 25
        motivos.append(f"Frequência respiratória alterada ({frequencia_respiratoria} rpm)")

    if frequencia_cardiaca is not None and (frequencia_cardiaca >= 130 or frequencia_cardiaca <= 40):
        pontuacao += 22
        motivos.append(f"Frequência cardíaca alterada ({frequencia_cardiaca} bpm)")

    if pressao_sistolica is not None and (pressao_sistolica >= 200 or pressao_sistolica <= 80):
        pontuacao += 22
        motivos.append(f"Pressão sistólica alterada ({pressao_sistolica} mmHg)")

    if temperatura is not None and (temperatura >= 39.5 or temperatura <= 35.0):
        pontuacao += 15
        motivos.append(f"Temperatura alterada ({temperatura}°C)")

    # --- 4. Dor relatada (escala 0-10) ---
    if escala_dor >= 8:
        pontuacao += 20
        motivos.append(f"Dor intensa (escala {escala_dor}/10)")
    elif escala_dor >= 5:
        pontuacao += 10
        motivos.append(f"Dor moderada (escala {escala_dor}/10)")
    elif escala_dor >= 1:
        pontuacao += 3

    # --- 5. Conversão de pontuação em cor ---
    if pontuacao >= 60:
        cor = "laranja"
    elif pontuacao >= 30:
        cor = "amarelo"
    elif pontuacao >= 10:
        cor = "verde"
    else:
        cor = "azul"

    if not motivos:
        motivos.append("Sem sinais de alerta identificados no pré-atendimento")

    return cor, pontuacao, "; ".join(motivos)
