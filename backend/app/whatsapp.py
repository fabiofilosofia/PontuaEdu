"""Envio do aviso de atraso pelo WhatsApp, via Twilio ou WhatsApp Cloud API (Meta).

Mensagens iniciadas pela escola precisam usar um modelo (template) aprovado.
O modelo esperado tem 3 variáveis no corpo:
    {{1}} nome do aluno, {{2}} turma, {{3}} data e hora da chegada.
No Sandbox da Twilio (testes) o texto livre abaixo é aceito sem modelo.
"""
import json
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


def texto_aviso(aluno: str, turma: str, data_hora: str) -> str:
    return (
        f"Olá! Informamos que o(a) aluno(a) {aluno}, da turma {turma}, chegou atrasado(a) "
        f"à escola em {data_hora}. Em caso de dúvidas, procure a coordenação. — {config.nome_escola}"
    )


def enviar_aviso_atraso(telefone: str, aluno: str, turma: str, data_hora: str) -> ResultadoEnvio:
    if not config.whatsapp_configurado:
        return ResultadoEnvio("nao_configurado", "WhatsApp não configurado no servidor (.env).")

    numero = normalizar_telefone(telefone)
    if len(numero) < 12:
        return ResultadoEnvio("falhou", f"Telefone inválido: {telefone!r}")

    if config.whatsapp_provedor == "meta":
        return _enviar_meta(numero, aluno, turma, data_hora)
    return _enviar_twilio(numero, aluno, turma, data_hora)


def _enviar_twilio(numero: str, aluno: str, turma: str, data_hora: str) -> ResultadoEnvio:
    url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages.json"
    remetente = config.twilio_whatsapp_from
    if not remetente.startswith("whatsapp:"):
        remetente = f"whatsapp:{remetente}"
    dados = {"From": remetente, "To": f"whatsapp:+{numero}"}
    if config.twilio_content_sid:
        dados["ContentSid"] = config.twilio_content_sid
        dados["ContentVariables"] = json.dumps({"1": aluno, "2": turma, "3": data_hora}, ensure_ascii=False)
    else:
        dados["Body"] = texto_aviso(aluno, turma, data_hora)

    try:
        resposta = httpx.post(
            url, data=dados, auth=(config.twilio_account_sid, config.twilio_auth_token), timeout=15
        )
    except httpx.HTTPError as erro:
        return ResultadoEnvio("falhou", f"Sem conexão com a Twilio: {erro}")

    if resposta.is_success:
        return ResultadoEnvio("enviado", resposta.json().get("sid", ""))
    try:
        erro = resposta.json()
        detalhe = f"{erro.get('message')} (código {erro.get('code')})"
    except ValueError:
        detalhe = resposta.text[:300]
    return ResultadoEnvio("falhou", f"HTTP {resposta.status_code}: {detalhe}")


def _enviar_meta(numero: str, aluno: str, turma: str, data_hora: str) -> ResultadoEnvio:
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
