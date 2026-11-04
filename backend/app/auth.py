"""Login de funcionários: senhas com PBKDF2 e tokens de sessão guardados no banco."""
import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException

from .config import config
from .db import agora, get_db

ITERACOES = 200_000


def gerar_hash(senha: str) -> str:
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal), ITERACOES)
    return f"pbkdf2_sha256${ITERACOES}${sal}${digest.hex()}"


def conferir_senha(senha: str, senha_hash: str) -> bool:
    try:
        _, iteracoes, sal, esperado = senha_hash.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal), int(iteracoes))
    return hmac.compare_digest(digest.hex(), esperado)


def criar_usuario(conn: sqlite3.Connection, usuario: str, nome: str, senha: str, admin: bool = False) -> int:
    cur = conn.execute(
        "INSERT INTO usuarios (usuario, nome, senha_hash, admin, criado_em) VALUES (?, ?, ?, ?, ?)",
        (usuario.strip().lower(), nome.strip(), gerar_hash(senha), int(admin), agora()),
    )
    return cur.lastrowid


def criar_sessao(conn: sqlite3.Connection, usuario_id: int, tipo: str = "login", duracao: timedelta | None = None) -> str:
    token = secrets.token_urlsafe(32)
    expira = datetime.now() + (duracao or timedelta(days=config.sessao_dias))
    conn.execute(
        "INSERT INTO sessoes (token, usuario_id, tipo, expira_em) VALUES (?, ?, ?, ?)",
        (token, usuario_id, tipo, expira.strftime("%Y-%m-%d %H:%M:%S")),
    )
    return token


def usuario_do_token(conn: sqlite3.Connection, token: str, tipo: str = "login") -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT u.* FROM sessoes s JOIN usuarios u ON u.id = s.usuario_id
        WHERE s.token = ? AND s.tipo = ? AND s.expira_em > ? AND u.ativo = 1
        """,
        (token, tipo, agora()),
    ).fetchone()


def usuario_atual(
    authorization: str = Header(default=""),
    conn: sqlite3.Connection = Depends(get_db),
) -> sqlite3.Row:
    token = authorization.removeprefix("Bearer ").strip()
    usuario = usuario_do_token(conn, token) if token else None
    if usuario is None:
        raise HTTPException(status_code=401, detail="Sessão expirada. Entre novamente.")
    return usuario


def exigir_admin(usuario: sqlite3.Row = Depends(usuario_atual)) -> sqlite3.Row:
    if not usuario["admin"]:
        raise HTTPException(status_code=403, detail="Apenas administradores podem fazer isso.")
    return usuario
