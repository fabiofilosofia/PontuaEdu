"""Envia uma mensagem de teste para conferir a configuração do WhatsApp.

Uso:  python testar_whatsapp.py 11987654321
"""
import sys
import time
from datetime import datetime

import httpx

from app.config import config
from app.whatsapp import enviar_aviso_atraso, normalizar_telefone


def conferir_entrega_twilio(sid: str) -> None:
    """A Twilio aceita a mensagem na hora e entrega depois; aqui vemos se deu certo."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages/{sid}.json"
    for _ in range(6):
        time.sleep(2)
        msg = httpx.get(url, auth=(config.twilio_account_sid, config.twilio_auth_token), timeout=15).json()
        if msg.get("status") in ("sent", "delivered", "read", "failed", "undelivered"):
            break
    print(f"Situação na Twilio: {msg.get('status')}")
    if msg.get("error_code"):
        print(f"Erro {msg['error_code']}: {msg.get('error_message') or 'veja twilio.com/docs/api/errors'}")
        if msg["error_code"] in (63015, 63016):
            print("Dica (Sandbox): o destino precisa ter enviado 'join <código>' para +1 415 523 8886.")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Informe o telefone de destino. Ex.: python testar_whatsapp.py 11987654321")
    if not config.whatsapp_configurado:
        if config.whatsapp_provedor == "meta":
            sys.exit("Preencha WHATSAPP_TOKEN e WHATSAPP_PHONE_NUMBER_ID no arquivo .env primeiro.")
        sys.exit("Preencha TWILIO_ACCOUNT_SID e TWILIO_AUTH_TOKEN no arquivo .env primeiro.")

    telefone = sys.argv[1]
    print(f"Enviando pela {config.whatsapp_provedor.title()} para +{normalizar_telefone(telefone)}...")
    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    resultado = enviar_aviso_atraso(telefone, "ALUNO TESTE", "1A", agora)

    if resultado.status == "enviado":
        print(f"Aceito pelo provedor (id {resultado.detalhe}).")
        if config.whatsapp_provedor != "meta":
            conferir_entrega_twilio(resultado.detalhe)
        print("Confira o WhatsApp do número de destino.")
    else:
        print(f"Não enviado: {resultado.detalhe}")
        if "template" in resultado.detalhe.lower():
            print("Dica: confira se o modelo foi aprovado e se o nome/SID batem com o .env.")
        if "recipient" in resultado.detalhe.lower() or "allowed list" in resultado.detalhe.lower():
            print("Dica: com o número de teste da Meta, o destino precisa estar na lista de números permitidos.")
        if "63015" in resultado.detalhe or "63016" in resultado.detalhe:
            print("Dica (Twilio Sandbox): o destino precisa ter enviado 'join <código>' para +1 415 523 8886.")
        if "20003" in resultado.detalhe:
            print("Dica: Account SID ou Auth Token incorretos no .env.")
        sys.exit(1)


if __name__ == "__main__":
    main()
