import importlib

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    planilha = tmp_path / "alunos.xlsx"
    wb = Workbook()
    wb.active.append(["Nome do Aluno", "Série", "Responsável", "WhatsApp"])
    wb.active.append(["Ana Souza", "6º A", "Carla", 11987654321])
    wb.active.append(["Bruno Lima", "7º B", "Marcos", "(11) 97654-3210"])
    wb.save(planilha)

    from app import config as config_mod
    monkeypatch.setattr(config_mod.config, "db_path", tmp_path / "teste.db")
    monkeypatch.setattr(config_mod.config, "excel_alunos", planilha)
    monkeypatch.setattr(config_mod.config, "whatsapp_token", "")
    monkeypatch.setattr(config_mod.config, "alerta_limite", 2)

    from app import excel, main
    importlib.reload(excel)
    main.excel = excel
    from app.auth import criar_usuario
    from app.db import conectar, iniciar_banco

    iniciar_banco()
    with conectar() as conn:
        criar_usuario(conn, "admin", "Admin", "segredo123", admin=True)
        criar_usuario(conn, "porteiro", "Porteiro", "segredo123")

    with TestClient(main.app) as c:
        yield c


def entrar(c, usuario="porteiro"):
    r = c.post("/login", json={"usuario": usuario, "senha": "segredo123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_login_errado_e_rota_protegida(cliente):
    assert cliente.post("/login", json={"usuario": "porteiro", "senha": "x"}).status_code == 401
    assert cliente.get("/alunos").status_code == 401


def test_alunos_vem_do_excel(cliente):
    alunos = cliente.get("/alunos", headers=entrar(cliente)).json()
    assert [a["nome"] for a in alunos] == ["Ana Souza", "Bruno Lima"]
    assert alunos[0]["telefone"] == "11987654321"
    assert cliente.get("/turmas", headers=entrar(cliente)).json() == ["6º A", "7º B"]


def test_registrar_historico_contagem_e_relatorio(cliente):
    h = entrar(cliente)
    ana = cliente.get("/alunos", headers=h).json()[0]

    r1 = cliente.post("/registrar", headers=h, json={"aluno_id": ana["id"]}).json()
    assert r1["whatsapp_status"] == "nao_configurado"
    assert r1["alerta"] is False
    r2 = cliente.post("/registrar", headers=h, json={"aluno_id": ana["id"], "observacao": "Ônibus"}).json()
    assert r2["total_atrasos"] == 2 and r2["alerta"] is True

    historico = cliente.get("/atrasos", headers=h).json()
    assert len(historico) == 2
    assert historico[0]["telefone"] == "11987654321"
    assert historico[0]["registrado_por"] == "Porteiro"

    contagem = cliente.get("/contagem", headers=h).json()
    assert contagem["alunos"][0]["total"] == 2 and contagem["alunos"][0]["alerta"]

    assert cliente.get("/atrasos", headers=h, params={"turma": "7º B"}).json() == []

    token = cliente.post("/relatorio/link", headers=h).json()["token"]
    arquivo = cliente.get("/relatorio.xlsx", params={"token": token})
    assert arquivo.status_code == 200
    assert arquivo.content[:2] == b"PK"  # arquivo .xlsx é um zip
    assert cliente.get("/relatorio.xlsx", params={"token": "invalido"}).status_code == 401


def test_aluno_inexistente(cliente):
    r = cliente.post("/registrar", headers=entrar(cliente), json={"aluno_id": 999})
    assert r.status_code == 404


def test_somente_admin_cria_usuario_e_exclui(cliente):
    novo = {"usuario": "maria", "nome": "Maria", "senha": "123456"}
    assert cliente.post("/usuarios", headers=entrar(cliente), json=novo).status_code == 403
    assert cliente.post("/usuarios", headers=entrar(cliente, "admin"), json=novo).status_code == 201

    h = entrar(cliente)
    ana = cliente.get("/alunos", headers=h).json()[0]
    atraso = cliente.post("/registrar", headers=h, json={"aluno_id": ana["id"]}).json()
    assert cliente.delete(f"/atrasos/{atraso['id']}", headers=h).status_code == 403
    assert cliente.delete(f"/atrasos/{atraso['id']}", headers=entrar(cliente, "admin")).status_code == 200


def test_whatsapp_monta_template(monkeypatch):
    from app import whatsapp
    from app.config import config

    monkeypatch.setattr(config, "whatsapp_token", "tok")
    monkeypatch.setattr(config, "whatsapp_phone_number_id", "123")
    enviado = {}

    class Resposta:
        is_success = True
        def json(self):
            return {"messages": [{"id": "wamid.X"}]}

    def falso_post(url, json, headers, timeout):
        enviado.update(url=url, json=json, headers=headers)
        return Resposta()

    monkeypatch.setattr(whatsapp.httpx, "post", falso_post)
    r = whatsapp.enviar_aviso_atraso("(11) 98765-4321", "Ana", "6º A", "03/11/2026 às 07:40")
    assert r.status == "enviado" and r.detalhe == "wamid.X"
    assert enviado["json"]["to"] == "5511987654321"
    assert enviado["url"].endswith("/123/messages")
    params = enviado["json"]["template"]["components"][0]["parameters"]
    assert [p["text"] for p in params] == ["Ana", "6º A", "03/11/2026 às 07:40"]

    assert whatsapp.enviar_aviso_atraso("123", "Ana", "6º A", "x").status == "falhou"
