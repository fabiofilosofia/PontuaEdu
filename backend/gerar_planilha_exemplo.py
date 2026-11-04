"""Cria dados/alunos.xlsx com alunos fictícios para testar o sistema."""
from openpyxl import Workbook

from app.config import config

ALUNOS = [
    ("Ana Beatriz Souza", "6º A", "Carla Souza", "11987654321"),
    ("Bruno Henrique Lima", "6º A", "Marcos Lima", "11976543210"),
    ("Carolina Mendes", "7º B", "Patrícia Mendes", "11965432109"),
    ("Daniel Oliveira", "7º B", "Roberto Oliveira", "11954321098"),
    ("Eduarda Santos", "8º C", "Juliana Santos", "11943210987"),
    ("Felipe Araújo", "9º A", "Sandra Araújo", "11932109876"),
]


def main() -> None:
    if config.excel_alunos.exists():
        print(f"Já existe {config.excel_alunos}; nada foi alterado.")
        return
    wb = Workbook()
    ws = wb.active
    ws.title = "Alunos"
    ws.append(["Aluno", "Turma", "Responsável", "Telefone"])
    for linha in ALUNOS:
        ws.append(linha)
    config.excel_alunos.parent.mkdir(parents=True, exist_ok=True)
    wb.save(config.excel_alunos)
    print(f"Planilha de exemplo criada em {config.excel_alunos}")


if __name__ == "__main__":
    main()
