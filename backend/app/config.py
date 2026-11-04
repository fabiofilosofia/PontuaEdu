"""Configurações lidas do arquivo backend/.env (veja .env.example)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


def _caminho(var: str, padrao: str) -> Path:
    valor = Path(os.getenv(var, padrao))
    return valor if valor.is_absolute() else BACKEND_DIR / valor


class Config:
    def __init__(self) -> None:
        self.nome_escola = os.getenv("NOME_ESCOLA", "Escola")
        self.db_path = _caminho("DB_PATH", "dados/pontuaedu.db")
        self.excel_alunos = _caminho("EXCEL_ALUNOS", "dados/alunos.xlsx")

        # Alerta: aluno com N atrasos ou mais nos últimos X dias
        self.alerta_limite = int(os.getenv("ALERTA_LIMITE", "3"))
        self.alerta_janela_dias = int(os.getenv("ALERTA_JANELA_DIAS", "30"))

        self.sessao_dias = int(os.getenv("SESSAO_DIAS", "30"))

        # Quem envia o WhatsApp: "twilio" ou "meta". Sem credenciais, nada é enviado.
        self.whatsapp_provedor = os.getenv("WHATSAPP_PROVEDOR", "twilio").strip().lower()

        # Twilio
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        self.twilio_content_sid = os.getenv("TWILIO_CONTENT_SID", "")

        # WhatsApp Cloud API (Meta)
        self.whatsapp_token = os.getenv("WHATSAPP_TOKEN", "")
        self.whatsapp_phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.whatsapp_template = os.getenv("WHATSAPP_TEMPLATE", "aviso_atraso")
        self.whatsapp_idioma = os.getenv("WHATSAPP_IDIOMA", "pt_BR")
        self.whatsapp_api_versao = os.getenv("WHATSAPP_API_VERSAO", "v23.0")

    @property
    def whatsapp_configurado(self) -> bool:
        if self.whatsapp_provedor == "meta":
            return bool(self.whatsapp_token and self.whatsapp_phone_number_id)
        return bool(self.twilio_account_sid and self.twilio_auth_token)


config = Config()
