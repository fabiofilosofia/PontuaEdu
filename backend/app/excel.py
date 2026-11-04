"""Leitura da planilha de alunos e geração do relatório de atrasos."""
import io
import re
import sqlite3
import unicodedata
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

# Nomes de coluna aceitos na planilha (sem acento, minúsculos).
# Texto entre parênteses também vale: "Telefone (WhatsApp)" é reconhecido.
COLUNAS = {
    "nome": {"aluno", "nome", "nome do aluno", "estudante"},
    "turma": {"turma", "serie", "classe", "sala"},
    "responsavel": {"responsavel", "nome do responsavel", "responsavel legal"},
    "telefone": {"telefone", "whatsapp", "celular", "telefone do responsavel", "contato"},
    "matricula": {"matricula", "ra", "codigo"},
    "situacao": {"sit", "situacao", "status", "situacao do aluno"},
}

# Valores da coluna de situação que contam como aluno ativo (vazio também conta)
SITUACOES_ATIVAS = {"", "ativo", "ativa", "matriculado", "matriculada", "regular", "cursando"}

STATUS_WHATSAPP = {"enviado": "Enviado", "falhou": "Falhou", "nao_configurado": "Sem envio"}

_ultima_sincronizacao: float | None = None


def _normalizar(texto: object) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(texto.lower().split())


def _variantes(cabecalho: str) -> set[str]:
    """'telefone (whatsapp)' -> {'telefone (whatsapp)', 'telefone', 'whatsapp'}"""
    sem_parenteses = re.sub(r"\(.*?\)", "", cabecalho).strip()
    return {cabecalho, sem_parenteses, *re.findall(r"\((.*?)\)", cabecalho)}


def _texto(valor: object) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)  # telefones salvos como número no Excel
    return str(valor).strip()


def _mapear_colunas(linha: tuple) -> dict[str, int]:
    cabecalho = [_variantes(_normalizar(c)) for c in linha]
    indices: dict[str, int] = {}
    for campo, nomes in COLUNAS.items():
        for i, variantes in enumerate(cabecalho):
            if i not in indices.values() and variantes & nomes:
                indices[campo] = i
                break
    return indices


def ler_planilha(caminho: Path) -> list[dict[str, str]]:
    """Procura, em todas as abas, a linha de títulos com 'Aluno' e 'Turma' e lê os alunos ativos."""
    for planilha in load_workbook(caminho, read_only=True, data_only=True).worksheets:
        linhas = planilha.iter_rows(values_only=True)
        for _, linha in zip(range(10), linhas):
            indices = _mapear_colunas(linha)
            if "nome" in indices and "turma" in indices:
                break
        else:
            continue

        alunos = []
        for linha in linhas:
            aluno = {campo: _texto(linha[i]) if i < len(linha) else "" for campo, i in indices.items()}
            if not (aluno["nome"] and aluno["turma"]):
                continue
            if _normalizar(aluno.pop("situacao", "")) in SITUACOES_ATIVAS:
                alunos.append(aluno)
        return alunos

    raise ValueError("Nenhuma aba da planilha tem as colunas 'Aluno' e 'Turma'.")


def sincronizar_alunos(conn: sqlite3.Connection, caminho: Path) -> int:
    """Copia a planilha para o banco quando o arquivo muda. Retorna quantos alunos há.

    Responsável e telefone vazios na planilha não apagam os que já foram
    informados pelo app no momento do registro.
    """
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
                    responsavel = COALESCE(NULLIF(excluded.responsavel, ''), alunos.responsavel),
                    telefone = COALESCE(NULLIF(excluded.telefone, ''), alunos.telefone),
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
