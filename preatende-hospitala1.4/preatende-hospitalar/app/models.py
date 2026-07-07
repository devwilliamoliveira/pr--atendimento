import uuid
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


def gerar_uuid():
    return str(uuid.uuid4())


class User(db.Model, UserMixin):
    __tablename__ = "usuarios"

    id = db.Column(db.String(36), primary_key=True, default=gerar_uuid)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    # papel: paciente | profissional | admin
    papel = db.Column(db.String(20), nullable=False, default="paciente")
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    triagens = db.relationship(
        "Triagem", back_populates="paciente", foreign_keys="Triagem.paciente_id"
    )

    def set_senha(self, senha_plana):
        self.senha_hash = generate_password_hash(senha_plana)

    def checar_senha(self, senha_plana):
        return check_password_hash(self.senha_hash, senha_plana)

    def is_profissional(self):
        return self.papel in ("profissional", "admin")

    def is_admin(self):
        return self.papel == "admin"

    def __repr__(self):
        return f"<User {self.email} ({self.papel})>"


# Ordem de prioridade clínica (menor número = mais urgente), estilo Protocolo de Manchester
CORES_PRIORIDADE = {
    "vermelho": {"ordem": 0, "label": "Emergência", "tempo_alvo": "Atendimento imediato"},
    "laranja": {"ordem": 1, "label": "Muito urgente", "tempo_alvo": "Até 10 minutos"},
    "amarelo": {"ordem": 2, "label": "Urgente", "tempo_alvo": "Até 60 minutos"},
    "verde": {"ordem": 3, "label": "Pouco urgente", "tempo_alvo": "Até 120 minutos"},
    "azul": {"ordem": 4, "label": "Não urgente", "tempo_alvo": "Até 240 minutos"},
}


class Triagem(db.Model):
    __tablename__ = "triagens"

    id = db.Column(db.String(36), primary_key=True, default=gerar_uuid)
    paciente_id = db.Column(db.String(36), db.ForeignKey("usuarios.id"), nullable=False)

    # Queixa e sinais vitais informados no pré-atendimento
    queixa_principal = db.Column(db.String(255), nullable=False)
    sintomas = db.Column(db.Text, nullable=True)  # texto livre, sintomas relatados
    escala_dor = db.Column(db.Integer, nullable=False, default=0)  # 0 a 10

    pressao_sistolica = db.Column(db.Integer, nullable=True)
    pressao_diastolica = db.Column(db.Integer, nullable=True)
    frequencia_cardiaca = db.Column(db.Integer, nullable=True)
    frequencia_respiratoria = db.Column(db.Integer, nullable=True)
    temperatura = db.Column(db.Float, nullable=True)
    saturacao_o2 = db.Column(db.Integer, nullable=True)

    sinais_gravidade = db.Column(db.Text, nullable=True)  # ex.: "sangramento;falta_de_ar"

    classificacao_cor = db.Column(db.String(20), nullable=False, default="verde")
    pontuacao_risco = db.Column(db.Integer, nullable=False, default=0)
    motivo_classificacao = db.Column(db.Text, nullable=True)

    # status: aguardando | em_atendimento | atendido | cancelado
    status = db.Column(db.String(20), nullable=False, default="aguardando")
    atendido_por_id = db.Column(db.String(36), db.ForeignKey("usuarios.id"), nullable=True)
    observacoes_profissional = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paciente = db.relationship("User", back_populates="triagens", foreign_keys=[paciente_id])
    profissional = db.relationship("User", foreign_keys=[atendido_por_id])

    def info_prioridade(self):
        return CORES_PRIORIDADE.get(self.classificacao_cor, CORES_PRIORIDADE["verde"])

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "paciente_nome": self.paciente.nome if self.paciente else None,
            "queixa_principal": self.queixa_principal,
            "sintomas": self.sintomas,
            "escala_dor": self.escala_dor,
            "pressao_sistolica": self.pressao_sistolica,
            "pressao_diastolica": self.pressao_diastolica,
            "frequencia_cardiaca": self.frequencia_cardiaca,
            "frequencia_respiratoria": self.frequencia_respiratoria,
            "temperatura": self.temperatura,
            "saturacao_o2": self.saturacao_o2,
            "sinais_gravidade": self.sinais_gravidade,
            "classificacao_cor": self.classificacao_cor,
            "classificacao_label": self.info_prioridade()["label"],
            "tempo_alvo": self.info_prioridade()["tempo_alvo"],
            "pontuacao_risco": self.pontuacao_risco,
            "motivo_classificacao": self.motivo_classificacao,
            "status": self.status,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }
