"""Envio do aviso de atraso pela WhatsApp Cloud API (Meta).

Mensagens iniciadas pela escola precisam usar um modelo (template) aprovado
pela Meta. O modelo esperado tem 3 variáveis no corpo:
    {{1}} nome do aluno, {{2}} turma, {{3}} data e hora da chegada.
"""
import re
from dataclasses import dataclass

import httpx

from .config import config


@dataclass
class ResultadoEnvio:
    status: str  # enviado | falhou | nao_configurado
    detalhe: str = ""


def normalizar_telefone(telefone: str) -> str:
    """Deixa só dígitos e acrescenta o código do Brasil (55) quando falta."""
    digitos = re.sub(r"\D", "", telefone or "")
    if len(digitos) in (10, 11):  # DDD + número
        digitos = "55" + digitos
    return digitos


def enviar_aviso_atraso(telefone: str, aluno: str, turma: str, data_hora: str) -> ResultadoEnvio:
    if not config.whatsapp_configurado:
        return ResultadoEnvio("nao_configurado", "WhatsApp não configurado no servidor (.env).")

    numero = normalizar_telefone(telefone)
    if len(numero) < 12:
        return ResultadoEnvio("falhou", f"Telefone inválido: {telefone!r}")

    url = (
        f"https://graph.facebook.com/{config.whatsapp_api_versao}/"
        f"{config.whatsapp_phone_number_id}/messages"
    )
    corpo = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {
            "name": config.whatsapp_template,
            "language": {"code": config.whatsapp_idioma},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": aluno},
                        {"type": "text", "text": turma},
                        {"type": "text", "text": data_hora},
                    ],
                }
            ],
        },
    }
    try:
        resposta = httpx.post(
            url,
            json=corpo,
            headers={"Authorization": f"Bearer {config.whatsapp_token}"},
            timeout=15,
        )
    except httpx.HTTPError as erro:
        return ResultadoEnvio("falhou", f"Sem conexão com o WhatsApp: {erro}")

    if resposta.is_success:
        mensagens = resposta.json().get("messages") or [{}]
        return ResultadoEnvio("enviado", mensagens[0].get("id", ""))

    try:
        detalhe = resposta.json()["error"]["message"]
    except (ValueError, KeyError, TypeError):
        detalhe = resposta.text[:300]
    return ResultadoEnvio("falhou", f"HTTP {resposta.status_code}: {detalhe}")
