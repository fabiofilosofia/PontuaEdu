"""Cria um funcionário que pode entrar no app.

Uso:  python criar_usuario.py            (pergunta os dados)
      python criar_usuario.py --admin    (cria um administrador)
"""
import getpass
import sqlite3
import sys

from app.auth import criar_usuario
from app.db import conectar, iniciar_banco


def main() -> None:
    admin = "--admin" in sys.argv
    iniciar_banco()
    print("Novo administrador" if admin else "Novo funcionário")
    usuario = input("Login (ex.: maria): ").strip()
    nome = input("Nome completo: ").strip()
    senha = getpass.getpass("Senha (mínimo 6 caracteres): ")
    if len(usuario) < 3 or not nome or len(senha) < 6:
        sys.exit("Dados inválidos: login com 3+ letras, nome preenchido e senha com 6+ caracteres.")
    if senha != getpass.getpass("Repita a senha: "):
        sys.exit("As senhas não conferem.")

    with conectar() as conn:
        try:
            criar_usuario(conn, usuario, nome, senha, admin)
        except sqlite3.IntegrityError:
            sys.exit(f"Já existe um usuário '{usuario}'.")
    print(f"Pronto! '{usuario}' já pode entrar no app.")


if __name__ == "__main__":
    main()
