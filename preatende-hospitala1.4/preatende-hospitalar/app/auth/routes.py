from urllib.parse import urlsplit

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.auth import auth_bp
from app.extensions import db, limiter
from app.forms import RegistroForm, LoginForm
from app.models import User


def _redirecionamento_seguro(destino):
    """Só permite redirecionar para caminhos internos (evita open redirect via ?next=)."""
    if not destino:
        return None
    partes = urlsplit(destino)
    # Precisa ser um caminho relativo, sem host/esquema (netloc vazio) e começar com "/"
    if partes.netloc or partes.scheme or not destino.startswith("/"):
        return None
    return destino


@auth_bp.route("/registrar", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def registrar():
    if current_user.is_authenticated:
        return redirect(url_for("web.painel"))

    form = RegistroForm()
    if form.validate_on_submit():
        email_normalizado = form.email.data.strip().lower()
        if User.query.filter_by(email=email_normalizado).first():
            flash("Este e-mail já está cadastrado.", "erro")
            return render_template("registrar.html", form=form)

        usuario = User(nome=form.nome.data.strip(), email=email_normalizado, papel="paciente")
        usuario.set_senha(form.senha.data)
        db.session.add(usuario)
        db.session.commit()

        login_user(usuario)
        flash("Cadastro realizado com sucesso! Bem-vindo(a).", "sucesso")
        return redirect(url_for("web.painel"))

    return render_template("registrar.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.painel"))

    form = LoginForm()
    if form.validate_on_submit():
        email_normalizado = form.email.data.strip().lower()
        usuario = User.query.filter_by(email=email_normalizado).first()

        if usuario and usuario.ativo and usuario.checar_senha(form.senha.data):
            login_user(usuario)
            proxima = _redirecionamento_seguro(request.args.get("next"))
            flash(f"Bem-vindo(a), {usuario.nome.split()[0]}!", "sucesso")
            return redirect(proxima or url_for("web.painel"))

        # Mensagem genérica de propósito: não revelar se o e-mail existe ou não
        flash("E-mail ou senha inválidos.", "erro")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("web.index"))
