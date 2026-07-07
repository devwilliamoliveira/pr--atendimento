from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SelectField,
    IntegerField,
    FloatField,
    TextAreaField,
    SelectMultipleField,
    widgets,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional

from app.triage_engine import SINAIS_GRAVIDADE_VALIDOS


class RegistroForm(FlaskForm):
    nome = StringField("Nome completo", validators=[DataRequired(), Length(min=3, max=120)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=150)])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(min=8, message="Mínimo de 8 caracteres")])
    confirmar_senha = PasswordField(
        "Confirmar senha", validators=[DataRequired(), EqualTo("senha", message="As senhas não coincidem")]
    )


class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired()])


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class TriagemForm(FlaskForm):
    queixa_principal = StringField(
        "Qual o principal motivo da sua busca por atendimento?",
        validators=[DataRequired(), Length(max=255)],
    )
    sintomas = TextAreaField("Descreva seus sintomas com mais detalhes", validators=[Optional(), Length(max=2000)])
    escala_dor = IntegerField(
        "Nível de dor (0 = nenhuma, 10 = pior dor possível)",
        validators=[DataRequired(), NumberRange(min=0, max=10)],
        default=0,
    )

    pressao_sistolica = IntegerField("Pressão sistólica (mmHg)", validators=[Optional(), NumberRange(min=40, max=300)])
    pressao_diastolica = IntegerField("Pressão diastólica (mmHg)", validators=[Optional(), NumberRange(min=20, max=200)])
    frequencia_cardiaca = IntegerField("Frequência cardíaca (bpm)", validators=[Optional(), NumberRange(min=20, max=250)])
    frequencia_respiratoria = IntegerField("Frequência respiratória (rpm)", validators=[Optional(), NumberRange(min=4, max=60)])
    temperatura = FloatField("Temperatura (°C)", validators=[Optional(), NumberRange(min=30, max=43)])
    saturacao_o2 = IntegerField("Saturação de O2 (%)", validators=[Optional(), NumberRange(min=50, max=100)])

    sinais_gravidade = MultiCheckboxField(
        "Você sente algum destes sinais agora?",
        choices=list(SINAIS_GRAVIDADE_VALIDOS.items()),
    )


class AtualizarStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[
            ("aguardando", "Aguardando"),
            ("em_atendimento", "Em atendimento"),
            ("atendido", "Atendido"),
            ("cancelado", "Cancelado"),
        ],
    )
    observacoes_profissional = TextAreaField("Observações", validators=[Optional(), Length(max=2000)])
