import os

from flask import Flask, jsonify, render_template

from app.config import config_by_name, validar_config_producao
from app.extensions import db, login_manager, jwt, csrf, limiter


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    if config_name == "production":
        validar_config_producao()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    os.makedirs(app.instance_path, exist_ok=True)

    # --- Extensões ---
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)

    # --- Blueprints ---
    from app.web import web_bp
    from app.auth import auth_bp
    from app.api import api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # --- Cabeçalhos de segurança básicos em toda resposta ---
    @app.after_request
    def aplicar_cabecalhos_seguranca(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if not app.debug and not app.testing:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; img-src 'self' data:; "
                "frame-ancestors 'none'; base-uri 'self'; form-action 'self';"
            )
            if app.config.get("SESSION_COOKIE_SECURE"):
                # HSTS: só faz sentido quando o site é servido via HTTPS (produção).
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains"
                )
        return response

    # --- Tratadores de erro amigáveis ---
    @app.errorhandler(403)
    def acesso_negado(e):
        if _quer_json():
            return jsonify({"erro": "Acesso negado."}), 403
        return render_template("erro.html", codigo=403, mensagem="Você não tem permissão para acessar esta página."), 403

    @app.errorhandler(404)
    def nao_encontrado(e):
        if _quer_json():
            return jsonify({"erro": "Recurso não encontrado."}), 404
        return render_template("erro.html", codigo=404, mensagem="Página não encontrada."), 404

    @app.errorhandler(401)
    def nao_autorizado(e):
        if _quer_json():
            return jsonify({"erro": "Autenticação necessária."}), 401
        return render_template("erro.html", codigo=401, mensagem="Faça login para continuar."), 401

    @app.errorhandler(500)
    def erro_interno(e):
        if _quer_json():
            return jsonify({"erro": "Erro interno do servidor."}), 500
        return render_template("erro.html", codigo=500, mensagem="Algo deu errado no servidor."), 500

    def _quer_json():
        from flask import request
        return request.path.startswith("/api/")

    # --- Manifest PWA (permite "instalar" o site como app no celular) ---
    @app.route("/manifest.json")
    def manifest():
        return app.send_static_file("manifest.json")

    with app.app_context():
        db.create_all()

    _registrar_comandos_cli(app)

    return app


def _registrar_comandos_cli(app):
    import click

    @app.cli.command("criar-profissional")
    @click.argument("nome")
    @click.argument("email")
    @click.argument("senha")
    @click.option("--admin", is_flag=True, help="Cria como administrador em vez de profissional.")
    def criar_profissional(nome, email, senha, admin):
        """Cria um usuário da equipe de saúde (profissional ou admin).

        Exemplo: flask criar-profissional "Dra. Ana" ana@hospital.com SenhaForte123
        """
        from app.models import User

        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            click.echo("Já existe um usuário com esse e-mail.")
            return

        if len(senha) < 8:
            click.echo("A senha deve ter no mínimo 8 caracteres.")
            return

        usuario = User(nome=nome, email=email, papel="admin" if admin else "profissional")
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuário {'admin' if admin else 'profissional'} criado: {email}")
