import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """Configuração base. Segredos SEMPRE vêm de variáveis de ambiente."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-troque-isto-em-producao")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-troque-isto-em-producao")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'preatende.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_TOKEN_LOCATION = ["headers"]

    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True

    # Em produção, sirva atrás de HTTPS e ajuste para True.
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


def validar_config_producao():
    """Recusa subir em produção com chaves-padrão de desenvolvimento, fracas ou ausentes."""
    chave_secreta = os.environ.get("SECRET_KEY", "")
    chave_jwt = os.environ.get("JWT_SECRET_KEY", "")
    valores_fracos = {"", "dev-key-troque-isto-em-producao", "dev-jwt-troque-isto-em-producao"}

    if chave_secreta in valores_fracos or chave_jwt in valores_fracos:
        raise RuntimeError(
            "SECRET_KEY e JWT_SECRET_KEY precisam ser definidas como variáveis de ambiente "
            "com valores fortes e únicos antes de rodar em produção. "
            'Gere com: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    if len(chave_secreta) < 32 or len(chave_jwt) < 32:
        raise RuntimeError(
            "SECRET_KEY e JWT_SECRET_KEY devem ter pelo menos 32 caracteres em produção."
        )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
