"""Leitura da planilha de alunos e geração do relatório de atrasos."""
import io
import sqlite3
import unicodedata
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

# Nomes de coluna aceitos na planilha (sem acento, minúsculos)
COLUNAS = {
    "nome": {"aluno", "nome", "nome do aluno", "estudante"},
    "turma": {"turma", "serie", "classe", "sala"},
    "responsavel": {"responsavel", "nome do responsavel", "responsavel legal"},
    "telefone": {"telefone", "whatsapp", "celular", "telefone do responsavel", "contato"},
    "matricula": {"matricula", "ra", "codigo"},
}

STATUS_WHATSAPP = {"enviado": "Enviado", "falhou": "Falhou", "nao_configurado": "Sem envio"}

_ultima_sincronizacao: float | None = None


def _normalizar(texto: object) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(texto.lower().split())


def _texto(valor: object) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)  # telefones salvos como número no Excel
    return str(valor).strip()


def ler_planilha(caminho: Path) -> list[dict[str, str]]:
    planilha = load_workbook(caminho, read_only=True, data_only=True).worksheets[0]
    linhas = planilha.iter_rows(values_only=True)
    cabecalho = [_normalizar(c) for c in next(linhas, [])]

    indices: dict[str, int] = {}
    for campo, nomes in COLUNAS.items():
        for i, coluna in enumerate(cabecalho):
            if coluna in nomes:
                indices[campo] = i
                break
    if "nome" not in indices or "turma" not in indices:
        raise ValueError("A planilha precisa ter as colunas 'Aluno' e 'Turma' na primeira linha.")

    alunos = []
    for linha in linhas:
        aluno = {campo: _texto(linha[i]) if i < len(linha) else "" for campo, i in indices.items()}
        if aluno["nome"] and aluno["turma"]:
            alunos.append(aluno)
    return alunos


def sincronizar_alunos(conn: sqlite3.Connection, caminho: Path) -> int:
    """Copia a planilha para o banco quando o arquivo muda. Retorna quantos alunos há."""
    global _ultima_sincronizacao
    if not caminho.exists():
        raise FileNotFoundError(f"Planilha de alunos não encontrada: {caminho}")

    modificado = caminho.stat().st_mtime
    if _ultima_sincronizacao != modificado:
        alunos = ler_planilha(caminho)
        conn.execute("UPDATE alunos SET ativo = 0")
        for a in alunos:
            conn.execute(
                """
                INSERT INTO alunos (matricula, nome, turma, responsavel, telefone, ativo)
                VALUES (:matricula, :nome, :turma, :responsavel, :telefone, 1)
                ON CONFLICT (nome, turma) DO UPDATE SET
                    matricula = excluded.matricula,
                    responsavel = excluded.responsavel,
                    telefone = excluded.telefone,
                    ativo = 1
                """,
                {"matricula": "", "responsavel": "", "telefone": "", **a},
            )
        conn.commit()
        _ultima_sincronizacao = modificado

    return conn.execute("SELECT COUNT(*) FROM alunos WHERE ativo = 1").fetchone()[0]


def _planilha_formatada(wb: Workbook, titulo: str, cabecalho: list[str], linhas: list[list]) -> None:
    ws = wb.create_sheet(titulo)
    ws.append(cabecalho)
    for celula in ws[1]:
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = PatternFill("solid", fgColor="1E293B")
    for linha in linhas:
        ws.append(linha)
    for coluna in ws.columns:
        largura = max(len(str(c.value or "")) for c in coluna)
        ws.column_dimensions[coluna[0].column_letter].width = min(largura + 2, 50)
    ws.freeze_panes = "A2"


def gerar_relatorio(atrasos: list[dict], resumo: list[dict]) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    _planilha_formatada(
        wb,
        "Atrasos",
        ["Data e hora", "Aluno", "Turma", "Responsável", "Telefone", "Observação", "Registrado por", "WhatsApp"],
        [
            [a["data_hora"], a["aluno"], a["turma"], a["responsavel"], a["telefone"],
             a["observacao"], a["registrado_por"], STATUS_WHATSAPP.get(a["whatsapp_status"], a["whatsapp_status"])]
            for a in atrasos
        ],
    )
    _planilha_formatada(
        wb,
        "Resumo por aluno",
        ["Aluno", "Turma", "Atrasos no período", "Último atraso"],
        [[r["aluno"], r["turma"], r["total"], r["ultimo"]] for r in resumo],
    )
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
