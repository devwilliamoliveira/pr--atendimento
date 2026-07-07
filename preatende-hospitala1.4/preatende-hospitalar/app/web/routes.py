from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.web import web_bp
from app.extensions import db
from app.forms import TriagemForm, AtualizarStatusForm
from app.models import Triagem, CORES_PRIORIDADE
from app.triage_engine import classificar_risco
from app.utils import requer_papel


@web_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("web.painel"))
    return render_template("index.html")


@web_bp.route("/painel")
@login_required
def painel():
    if current_user.is_profissional():
        return redirect(url_for("web.fila"))
    return redirect(url_for("web.minhas_triagens"))


@web_bp.route("/pre-atendimento/novo", methods=["GET", "POST"])
@login_required
def nova_triagem():
    form = TriagemForm()
    if form.validate_on_submit():
        cor, pontuacao, motivo = classificar_risco(
            escala_dor=form.escala_dor.data,
            pressao_sistolica=form.pressao_sistolica.data,
            pressao_diastolica=form.pressao_diastolica.data,
            frequencia_cardiaca=form.frequencia_cardiaca.data,
            frequencia_respiratoria=form.frequencia_respiratoria.data,
            temperatura=form.temperatura.data,
            saturacao_o2=form.saturacao_o2.data,
            sinais_gravidade=form.sinais_gravidade.data,
        )

        triagem = Triagem(
            paciente_id=current_user.id,
            queixa_principal=form.queixa_principal.data.strip(),
            sintomas=form.sintomas.data,
            escala_dor=form.escala_dor.data,
            pressao_sistolica=form.pressao_sistolica.data,
            pressao_diastolica=form.pressao_diastolica.data,
            frequencia_cardiaca=form.frequencia_cardiaca.data,
            frequencia_respiratoria=form.frequencia_respiratoria.data,
            temperatura=form.temperatura.data,
            saturacao_o2=form.saturacao_o2.data,
            sinais_gravidade=",".join(form.sinais_gravidade.data) if form.sinais_gravidade.data else None,
            classificacao_cor=cor,
            pontuacao_risco=pontuacao,
            motivo_classificacao=motivo,
        )
        db.session.add(triagem)
        db.session.commit()

        flash("Pré-atendimento registrado com sucesso!", "sucesso")
        return redirect(url_for("web.detalhe_triagem", triagem_id=triagem.id))

    return render_template("triagem_form.html", form=form)


@web_bp.route("/minhas-triagens")
@login_required
def minhas_triagens():
    triagens = (
        Triagem.query.filter_by(paciente_id=current_user.id)
        .order_by(Triagem.criado_em.desc())
        .all()
    )
    return render_template("minhas_triagens.html", triagens=triagens)


@web_bp.route("/fila")
@login_required
@requer_papel("profissional", "admin")
def fila():
    ordem_cor = {cor: dados["ordem"] for cor, dados in CORES_PRIORIDADE.items()}
    triagens = (
        Triagem.query.filter(Triagem.status.in_(["aguardando", "em_atendimento"]))
        .all()
    )
    triagens.sort(key=lambda t: (ordem_cor.get(t.classificacao_cor, 9), t.criado_em))
    return render_template("fila.html", triagens=triagens)


@web_bp.route("/pre-atendimento/<triagem_id>")
@login_required
def detalhe_triagem(triagem_id):
    triagem = Triagem.query.get_or_404(triagem_id)

    pode_ver = (
        triagem.paciente_id == current_user.id or current_user.is_profissional()
    )
    if not pode_ver:
        abort(403)

    form = AtualizarStatusForm(status=triagem.status, observacoes_profissional=triagem.observacoes_profissional)
    return render_template("detalhe_triagem.html", triagem=triagem, form=form)


@web_bp.route("/pre-atendimento/<triagem_id>/status", methods=["POST"])
@login_required
@requer_papel("profissional", "admin")
def atualizar_status(triagem_id):
    triagem = Triagem.query.get_or_404(triagem_id)
    form = AtualizarStatusForm()

    if form.validate_on_submit():
        triagem.status = form.status.data
        triagem.observacoes_profissional = form.observacoes_profissional.data
        triagem.atendido_por_id = current_user.id
        db.session.commit()
        flash("Status atualizado.", "sucesso")
    else:
        flash("Não foi possível atualizar o status.", "erro")

    return redirect(url_for("web.detalhe_triagem", triagem_id=triagem.id))
