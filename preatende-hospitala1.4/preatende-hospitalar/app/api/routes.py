"""
API JSON do sistema de pré-atendimento.

Esta API é a mesma usada pelo site (internamente) e serve como backend pronto
para um aplicativo móvel (Flutter, React Native, Ionic, etc.) ou qualquer
outro cliente HTTP. Autenticação via JWT (Bearer token).
"""

from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from app.api import api_bp
from app.extensions import db, limiter, csrf
from app.models import User, Triagem, CORES_PRIORIDADE
from app.triage_engine import classificar_risco, SINAIS_GRAVIDADE_VALIDOS

# A API usa tokens JWT (não cookies de sessão), então fica isenta do CSRF de formulário.
csrf.exempt(api_bp)


def erro(mensagem, codigo=400):
    return jsonify({"erro": mensagem}), codigo


def usuario_atual():
    user_id = get_jwt_identity()
    return db.session.get(User, user_id)


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

@api_bp.route("/auth/registrar", methods=["POST"])
@limiter.limit("20 per hour")
def api_registrar():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip().lower()
    senha = dados.get("senha") or ""

    if not nome or len(nome) < 3:
        return erro("Informe um nome válido (mínimo 3 caracteres).")
    if not email or "@" not in email:
        return erro("Informe um e-mail válido.")
    if len(senha) < 8:
        return erro("A senha deve ter no mínimo 8 caracteres.")

    if User.query.filter_by(email=email).first():
        return erro("Este e-mail já está cadastrado.", 409)

    usuario = User(nome=nome, email=email, papel="paciente")
    usuario.set_senha(senha)
    db.session.add(usuario)
    db.session.commit()

    token = create_access_token(identity=usuario.id)
    return jsonify({"access_token": token, "usuario": {"id": usuario.id, "nome": usuario.nome, "papel": usuario.papel}}), 201


@api_bp.route("/auth/login", methods=["POST"])
@limiter.limit("15 per minute")
def api_login():
    dados = request.get_json(silent=True) or {}
    email = (dados.get("email") or "").strip().lower()
    senha = dados.get("senha") or ""

    usuario = User.query.filter_by(email=email).first()
    if not usuario or not usuario.ativo or not usuario.checar_senha(senha):
        return erro("E-mail ou senha inválidos.", 401)

    token = create_access_token(identity=usuario.id)
    return jsonify({"access_token": token, "usuario": {"id": usuario.id, "nome": usuario.nome, "papel": usuario.papel}})


@api_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def api_me():
    usuario = usuario_atual()
    if not usuario:
        return erro("Usuário não encontrado.", 404)
    return jsonify({"id": usuario.id, "nome": usuario.nome, "email": usuario.email, "papel": usuario.papel})


# ---------------------------------------------------------------------------
# Pré-triagem
# ---------------------------------------------------------------------------

@api_bp.route("/triagens", methods=["POST"])
@jwt_required()
@limiter.limit("30 per hour")
def api_criar_triagem():
    usuario = usuario_atual()
    if not usuario:
        return erro("Usuário não encontrado.", 404)

    dados = request.get_json(silent=True) or {}
    queixa_principal = (dados.get("queixa_principal") or "").strip()
    if not queixa_principal:
        return erro("O campo 'queixa_principal' é obrigatório.")

    try:
        escala_dor = int(dados.get("escala_dor", 0))
    except (TypeError, ValueError):
        return erro("'escala_dor' deve ser um número entre 0 e 10.")
    if not (0 <= escala_dor <= 10):
        return erro("'escala_dor' deve estar entre 0 e 10.")

    sinais_gravidade = dados.get("sinais_gravidade") or []
    if not isinstance(sinais_gravidade, list):
        return erro("'sinais_gravidade' deve ser uma lista.")
    sinais_invalidos = [s for s in sinais_gravidade if s not in SINAIS_GRAVIDADE_VALIDOS]
    if sinais_invalidos:
        return erro(f"Sinais de gravidade inválidos: {sinais_invalidos}")

    def campo_numerico(nome, minimo, maximo, tipo=int):
        valor = dados.get(nome)
        if valor is None or valor == "":
            return None, None
        try:
            valor = tipo(valor)
        except (TypeError, ValueError):
            return None, f"'{nome}' deve ser numérico."
        if not (minimo <= valor <= maximo):
            return None, f"'{nome}' fora da faixa aceitável ({minimo}-{maximo})."
        return valor, None

    campos_numericos = {}
    for nome, minimo, maximo, tipo in [
        ("pressao_sistolica", 40, 300, int),
        ("pressao_diastolica", 20, 200, int),
        ("frequencia_cardiaca", 20, 250, int),
        ("frequencia_respiratoria", 4, 60, int),
        ("temperatura", 30, 43, float),
        ("saturacao_o2", 50, 100, int),
    ]:
        valor, msg_erro = campo_numerico(nome, minimo, maximo, tipo)
        if msg_erro:
            return erro(msg_erro)
        campos_numericos[nome] = valor

    cor, pontuacao, motivo = classificar_risco(
        escala_dor=escala_dor,
        sinais_gravidade=sinais_gravidade,
        **campos_numericos,
    )

    triagem = Triagem(
        paciente_id=usuario.id,
        queixa_principal=queixa_principal,
        sintomas=dados.get("sintomas"),
        escala_dor=escala_dor,
        sinais_gravidade=",".join(sinais_gravidade) if sinais_gravidade else None,
        classificacao_cor=cor,
        pontuacao_risco=pontuacao,
        motivo_classificacao=motivo,
        **campos_numericos,
    )
    db.session.add(triagem)
    db.session.commit()

    return jsonify(triagem.to_dict()), 201


@api_bp.route("/triagens", methods=["GET"])
@jwt_required()
def api_listar_triagens():
    usuario = usuario_atual()
    if not usuario:
        return erro("Usuário não encontrado.", 404)

    if usuario.is_profissional():
        triagens = Triagem.query.order_by(Triagem.criado_em.desc()).limit(200).all()
    else:
        triagens = (
            Triagem.query.filter_by(paciente_id=usuario.id)
            .order_by(Triagem.criado_em.desc())
            .all()
        )
    return jsonify([t.to_dict() for t in triagens])


@api_bp.route("/triagens/<triagem_id>", methods=["GET"])
@jwt_required()
def api_detalhe_triagem(triagem_id):
    usuario = usuario_atual()
    triagem = db.session.get(Triagem, triagem_id)
    if not triagem:
        return erro("Pré-atendimento não encontrado.", 404)
    if triagem.paciente_id != usuario.id and not usuario.is_profissional():
        return erro("Acesso negado.", 403)
    return jsonify(triagem.to_dict())


@api_bp.route("/fila", methods=["GET"])
@jwt_required()
def api_fila():
    usuario = usuario_atual()
    if not usuario or not usuario.is_profissional():
        return erro("Apenas profissionais podem ver a fila.", 403)

    ordem_cor = {cor: dados["ordem"] for cor, dados in CORES_PRIORIDADE.items()}
    triagens = Triagem.query.filter(Triagem.status.in_(["aguardando", "em_atendimento"])).all()
    triagens.sort(key=lambda t: (ordem_cor.get(t.classificacao_cor, 9), t.criado_em))
    return jsonify([t.to_dict() for t in triagens])


@api_bp.route("/triagens/<triagem_id>/status", methods=["PATCH"])
@jwt_required()
def api_atualizar_status(triagem_id):
    usuario = usuario_atual()
    if not usuario or not usuario.is_profissional():
        return erro("Apenas profissionais podem atualizar o status.", 403)

    triagem = db.session.get(Triagem, triagem_id)
    if not triagem:
        return erro("Pré-atendimento não encontrado.", 404)

    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status")
    if novo_status not in ("aguardando", "em_atendimento", "atendido", "cancelado"):
        return erro("Status inválido.")

    triagem.status = novo_status
    triagem.observacoes_profissional = dados.get("observacoes_profissional", triagem.observacoes_profissional)
    triagem.atendido_por_id = usuario.id
    db.session.commit()

    return jsonify(triagem.to_dict())
