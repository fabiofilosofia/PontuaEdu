"""API do PontuaEdu: registro de atrasos, histórico, contagem e relatório."""
import sqlite3
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import auth, excel, whatsapp
from .config import config
from .db import agora, conectar, get_db, iniciar_banco


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    iniciar_banco()
    yield


app = FastAPI(title="PontuaEdu API", lifespan=ciclo_de_vida)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------- Modelos ----------

class LoginEntrada(BaseModel):
    usuario: str
    senha: str


class RegistroEntrada(BaseModel):
    aluno_id: int
    nome_responsavel: str = ""
    telefone_responsavel: str = ""
    observacao: str = ""


class UsuarioEntrada(BaseModel):
    usuario: str = Field(min_length=3)
    nome: str = Field(min_length=1)
    senha: str = Field(min_length=6)
    admin: bool = False


# ---------- Auxiliares ----------

def _periodo(inicio: date | None, fim: date | None) -> tuple[str, str]:
    """Converte datas em limites de texto; sem datas, usa o dia de hoje."""
    hoje = date.today()
    inicio = inicio or hoje
    fim = fim or hoje
    if fim < inicio:
        raise HTTPException(400, "A data final é anterior à inicial.")
    return f"{inicio} 00:00:00", f"{fim} 23:59:59"


def _filtro(inicio: str, fim: str, turma: str | None, aluno_id: int | None) -> tuple[str, list]:
    condicoes = ["t.data_hora BETWEEN ? AND ?"]
    params: list = [inicio, fim]
    if turma:
        condicoes.append("a.turma = ?")
        params.append(turma)
    if aluno_id:
        condicoes.append("a.id = ?")
        params.append(aluno_id)
    return " AND ".join(condicoes), params


def _listar_atrasos(conn: sqlite3.Connection, where: str, params: list) -> list[dict]:
    linhas = conn.execute(
        f"""
        SELECT t.id, t.data_hora, a.id AS aluno_id, a.nome AS aluno, a.turma,
               t.responsavel, t.telefone, t.observacao, t.whatsapp_status, t.whatsapp_detalhe,
               u.nome AS registrado_por
        FROM atrasos t
        JOIN alunos a ON a.id = t.aluno_id
        JOIN usuarios u ON u.id = t.usuario_id
        WHERE {where}
        ORDER BY t.data_hora DESC
        """,
        params,
    ).fetchall()
    return [dict(l) for l in linhas]


def _contagem(conn: sqlite3.Connection, where: str, params: list) -> list[dict]:
    linhas = conn.execute(
        f"""
        SELECT a.id AS aluno_id, a.nome AS aluno, a.turma,
               COUNT(*) AS total, MAX(t.data_hora) AS ultimo
        FROM atrasos t JOIN alunos a ON a.id = t.aluno_id
        WHERE {where}
        GROUP BY a.id
        ORDER BY total DESC, a.nome
        """,
        params,
    ).fetchall()
    return [dict(l) | {"alerta": l["total"] >= config.alerta_limite} for l in linhas]


def _atrasos_na_janela(conn: sqlite3.Connection, aluno_id: int) -> int:
    desde = (datetime.now() - timedelta(days=config.alerta_janela_dias)).strftime("%Y-%m-%d %H:%M:%S")
    return conn.execute(
        "SELECT COUNT(*) FROM atrasos WHERE aluno_id = ? AND data_hora >= ?", (aluno_id, desde)
    ).fetchone()[0]


def _sincronizar(conn: sqlite3.Connection) -> None:
    try:
        excel.sincronizar_alunos(conn, config.excel_alunos)
    except (FileNotFoundError, ValueError) as erro:
        raise HTTPException(500, str(erro))


# ---------- Rotas ----------

@app.get("/")
def status():
    return {
        "app": "PontuaEdu",
        "escola": config.nome_escola,
        "whatsapp_configurado": config.whatsapp_configurado,
    }


@app.post("/login")
def login(dados: LoginEntrada, conn: sqlite3.Connection = Depends(get_db)):
    usuario = conn.execute(
        "SELECT * FROM usuarios WHERE usuario = ? AND ativo = 1", (dados.usuario.strip().lower(),)
    ).fetchone()
    if usuario is None or not auth.conferir_senha(dados.senha, usuario["senha_hash"]):
        raise HTTPException(401, "Usuário ou senha incorretos.")
    token = auth.criar_sessao(conn, usuario["id"])
    return {"token": token, "nome": usuario["nome"], "admin": bool(usuario["admin"])}


@app.post("/logout")
def logout(request: Request, conn: sqlite3.Connection = Depends(get_db), _=Depends(auth.usuario_atual)):
    token = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    conn.execute("DELETE FROM sessoes WHERE token = ?", (token,))
    return {"ok": True}


@app.get("/me")
def eu(usuario=Depends(auth.usuario_atual)):
    return {"usuario": usuario["usuario"], "nome": usuario["nome"], "admin": bool(usuario["admin"])}


@app.post("/usuarios", status_code=201)
def novo_usuario(dados: UsuarioEntrada, conn: sqlite3.Connection = Depends(get_db), _=Depends(auth.exigir_admin)):
    try:
        novo_id = auth.criar_usuario(conn, dados.usuario, dados.nome, dados.senha, dados.admin)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Já existe um usuário com esse login.")
    return {"id": novo_id}


@app.get("/alunos")
def alunos(conn: sqlite3.Connection = Depends(get_db), _=Depends(auth.usuario_atual)):
    _sincronizar(conn)
    linhas = conn.execute(
        "SELECT id, matricula, nome, turma, responsavel, telefone FROM alunos WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    return [dict(l) for l in linhas]


@app.get("/turmas")
def turmas(conn: sqlite3.Connection = Depends(get_db), _=Depends(auth.usuario_atual)):
    _sincronizar(conn)
    linhas = conn.execute("SELECT DISTINCT turma FROM alunos WHERE ativo = 1 ORDER BY turma").fetchall()
    return [l["turma"] for l in linhas]


@app.post("/registrar", status_code=201)
def registrar(dados: RegistroEntrada, conn: sqlite3.Connection = Depends(get_db), usuario=Depends(auth.usuario_atual)):
    aluno = conn.execute("SELECT * FROM alunos WHERE id = ? AND ativo = 1", (dados.aluno_id,)).fetchone()
    if aluno is None:
        raise HTTPException(404, "Aluno não encontrado. Atualize a lista e tente de novo.")

    responsavel = dados.nome_responsavel.strip() or aluno["responsavel"] or ""
    telefone = dados.telefone_responsavel.strip() or aluno["telefone"] or ""
    if (responsavel, telefone) != (aluno["responsavel"] or "", aluno["telefone"] or ""):
        # Guarda o contato digitado para os próximos registros desse aluno
        conn.execute("UPDATE alunos SET responsavel = ?, telefone = ? WHERE id = ?", (responsavel, telefone, aluno["id"]))
    data_hora = agora()
    data_hora_exibicao = datetime.now().strftime("%d/%m/%Y às %H:%M")

    envio = whatsapp.enviar_aviso_atraso(telefone, aluno["nome"], aluno["turma"], data_hora_exibicao)

    cur = conn.execute(
        """
        INSERT INTO atrasos (aluno_id, usuario_id, data_hora, responsavel, telefone, observacao,
                             whatsapp_status, whatsapp_detalhe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (aluno["id"], usuario["id"], data_hora, responsavel, telefone,
         dados.observacao.strip(), envio.status, envio.detalhe),
    )
    total = _atrasos_na_janela(conn, aluno["id"])

    mensagens = {
        "enviado": "Atraso registrado e responsável avisado pelo WhatsApp.",
        "falhou": "Atraso registrado, mas o WhatsApp não foi enviado.",
        "nao_configurado": "Atraso registrado. O envio pelo WhatsApp ainda não está configurado.",
    }
    return {
        "id": cur.lastrowid,
        "mensagem": mensagens[envio.status],
        "whatsapp_status": envio.status,
        "whatsapp_detalhe": envio.detalhe,
        "total_atrasos": total,
        "janela_dias": config.alerta_janela_dias,
        "alerta": total >= config.alerta_limite,
    }


@app.post("/atrasos/{atraso_id}/reenviar")
def reenviar(atraso_id: int, conn: sqlite3.Connection = Depends(get_db), _=Depends(auth.usuario_atual)):
    atraso = conn.execute(
        """
        SELECT t.*, a.nome AS aluno, a.turma FROM atrasos t JOIN alunos a ON a.id = t.aluno_id
        WHERE t.id = ?
        """,
        (atraso_id,),
    ).fetchone()
    if atraso is None:
        raise HTTPException(404, "Registro não encontrado.")
    quando = datetime.strptime(atraso["data_hora"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y às %H:%M")
    envio = whatsapp.enviar_aviso_atraso(atraso["telefone"], atraso["aluno"], atraso["turma"], quando)
    conn.execute(
        "UPDATE atrasos SET whatsapp_status = ?, whatsapp_detalhe = ? WHERE id = ?",
        (envio.status, envio.detalhe, atraso_id),
    )
    return {"whatsapp_status": envio.status, "whatsapp_detalhe": envio.detalhe}


@app.delete("/atrasos/{atraso_id}")
def excluir_atraso(atraso_id: int, conn: sqlite3.Connection = Depends(get_db), _=Depends(auth.exigir_admin)):
    if conn.execute("DELETE FROM atrasos WHERE id = ?", (atraso_id,)).rowcount == 0:
        raise HTTPException(404, "Registro não encontrado.")
    return {"ok": True}


@app.get("/atrasos")
def historico(
    inicio: date | None = None,
    fim: date | None = None,
    turma: str | None = None,
    aluno_id: int | None = None,
    conn: sqlite3.Connection = Depends(get_db),
    _=Depends(auth.usuario_atual),
):
    where, params = _filtro(*_periodo(inicio, fim), turma, aluno_id)
    return _listar_atrasos(conn, where, params)


@app.get("/contagem")
def contagem(
    inicio: date | None = None,
    fim: date | None = None,
    turma: str | None = None,
    conn: sqlite3.Connection = Depends(get_db),
    _=Depends(auth.usuario_atual),
):
    where, params = _filtro(*_periodo(inicio, fim), turma, None)
    return {"limite_alerta": config.alerta_limite, "alunos": _contagem(conn, where, params)}


@app.post("/relatorio/link")
def link_relatorio(conn: sqlite3.Connection = Depends(get_db), usuario=Depends(auth.usuario_atual)):
    """Gera um token de 5 minutos para baixar o relatório pelo navegador do celular."""
    token = auth.criar_sessao(conn, usuario["id"], tipo="download", duracao=timedelta(minutes=5))
    return {"token": token}


@app.get("/relatorio.xlsx")
def relatorio(
    token: str = Query(),
    inicio: date | None = None,
    fim: date | None = None,
    turma: str | None = None,
):
    with conectar() as conn:
        if auth.usuario_do_token(conn, token, tipo="download") is None:
            raise HTTPException(401, "Link expirado. Gere o relatório novamente pelo app.")
        ini, fim_txt = _periodo(inicio, fim)
        where, params = _filtro(ini, fim_txt, turma, None)
        conteudo = excel.gerar_relatorio(_listar_atrasos(conn, where, params), _contagem(conn, where, params))

    nome = f"atrasos_{ini[:10]}_a_{fim_txt[:10]}.xlsx"
    return Response(
        conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
