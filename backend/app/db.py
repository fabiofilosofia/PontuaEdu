"""Banco SQLite: usuários, sessões, alunos (sincronizados do Excel) e atrasos."""
import sqlite3
from datetime import datetime
from typing import Iterator

from .config import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    usuario TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    senha_hash TEXT NOT NULL,
    admin INTEGER NOT NULL DEFAULT 0,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessoes (
    token TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    tipo TEXT NOT NULL DEFAULT 'login',
    expira_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY,
    matricula TEXT,
    nome TEXT NOT NULL,
    turma TEXT NOT NULL,
    responsavel TEXT,
    telefone TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    UNIQUE (nome, turma)
);

CREATE TABLE IF NOT EXISTS atrasos (
    id INTEGER PRIMARY KEY,
    aluno_id INTEGER NOT NULL REFERENCES alunos(id),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    data_hora TEXT NOT NULL,
    responsavel TEXT,
    telefone TEXT,
    observacao TEXT,
    whatsapp_status TEXT NOT NULL,
    whatsapp_detalhe TEXT
);

CREATE INDEX IF NOT EXISTS idx_atrasos_data ON atrasos (data_hora);
CREATE INDEX IF NOT EXISTS idx_atrasos_aluno ON atrasos (aluno_id);
"""


def agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def conectar() -> sqlite3.Connection:
    config.db_path.parent.mkdir(parents=True, exist_ok=True)
    # O FastAPI pode abrir e usar a conexão em threads diferentes da mesma requisição.
    # Cada requisição tem a sua própria conexão, então isso é seguro.
    conn = sqlite3.connect(config.db_path, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def iniciar_banco() -> None:
    with conectar() as conn:
        conn.executescript(ESQUEMA)


def get_db() -> Iterator[sqlite3.Connection]:
    """Dependência do FastAPI: uma conexão por requisição."""
    conn = conectar()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
