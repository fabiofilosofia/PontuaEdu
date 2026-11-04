# PontuaEdu — Controle de atrasos escolares

App para a portaria/coordenação registrar a chegada atrasada de alunos e avisar o responsável pelo WhatsApp automaticamente.

- **Registrar**: busca o aluno pelo nome (lista vinda da planilha Excel da escola), confirma responsável/telefone e registra. O responsável recebe a mensagem no WhatsApp.
- **Histórico**: atrasos de hoje, 7 dias, 30 dias ou do ano, por turma. Toque num envio que falhou para reenviar. Botão para baixar relatório em Excel.
- **Por aluno**: quantos atrasos cada aluno teve no período; quem passou do limite aparece destacado.
- **Login**: só funcionários cadastrados usam o app.

```
app/            telas do app (Expo / React Native)
lib/            comunicação com o servidor e login
backend/        servidor (Python + FastAPI + SQLite)
```

---

## 1. Servidor (no computador da escola)

Precisa do [Python 3.11+](https://www.python.org/downloads/). No terminal, dentro da pasta `backend`:

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

**Planilha de alunos:** coloque a planilha em `backend/dados/alunos.xlsx`. A primeira linha deve ter os títulos das colunas: **Aluno**, **Turma**, **Responsável**, **Telefone** (Matrícula é opcional; variações como "Nome", "Série", "WhatsApp" também são aceitas). Para testar sem a planilha real: `python gerar_planilha_exemplo.py`.

Sempre que a planilha for salva, o servidor recarrega os alunos sozinho.

**Primeiro usuário (administrador):**

```bash
python criar_usuario.py --admin
```

Funcionários comuns: `python criar_usuario.py`. Administradores também podem criar usuários pela API (`POST /usuarios`) e excluir registros feitos por engano.

**Ligar o servidor:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Descubra o IP do computador com `ipconfig` (ex.: `192.168.0.12`). Se o Windows perguntar, permita o acesso na rede privada.

> Os dados reais (planilha e banco `dados/pontuaedu.db`) ficam só no computador da escola — a pasta `dados/` não vai para o GitHub. Faça backup do arquivo `.db` periodicamente.

## 2. App

Na pasta raiz do projeto:

```bash
npm install
copy .env.example .env.local
```

Edite `.env.local` com o IP do servidor: `EXPO_PUBLIC_API_URL=http://192.168.0.12:8000`

```bash
npx expo start
```

Abra no celular com o Expo Go (mesmo Wi-Fi do servidor) ou pressione `w` para abrir no navegador.

## 3. WhatsApp (envio automático)

O envio usa a **WhatsApp Cloud API** oficial da Meta. Enquanto não estiver configurado, o app registra os atrasos normalmente e mostra "Sem envio".

1. Crie uma conta no [Meta for Developers](https://developers.facebook.com/), crie um app do tipo **Business** e adicione o produto **WhatsApp**.
2. Cadastre e verifique o número de telefone da escola (precisa ser um número que **não** esteja em uso no WhatsApp comum).
3. Em **Gerenciador do WhatsApp > Modelos de mensagem**, crie um modelo chamado `aviso_atraso`, categoria **Utilidade**, idioma **Português (BR)**, com 3 variáveis. Exemplo de texto:

   > Olá! Informamos que o(a) aluno(a) {{1}}, da turma {{2}}, chegou atrasado(a) à escola em {{3}}. Em caso de dúvidas, procure a coordenação.

4. Aguarde a aprovação do modelo (costuma levar de minutos a 1 dia).
5. Crie um **token de acesso permanente** (Usuário do sistema no Gerenciador de Negócios, com permissão `whatsapp_business_messaging`).
6. Preencha no `backend/.env`:

   ```
   WHATSAPP_TOKEN=<token permanente>
   WHATSAPP_PHONE_NUMBER_ID=<ID do número, em "Configuração da API">
   WHATSAPP_TEMPLATE=aviso_atraso
   ```

7. Reinicie o servidor.

A Meta cobra por conversa iniciada pela empresa (modelos de "Utilidade" têm custo baixo; confira a tabela de preços atual para o Brasil). Os telefones podem estar na planilha com ou sem DDI/máscara — o servidor acrescenta o `55` quando falta.

## Alertas

No `backend/.env`: `ALERTA_LIMITE=3` e `ALERTA_JANELA_DIAS=30` → o app avisa quando um aluno chega ao 3º atraso em 30 dias.

## Desenvolvimento

```bash
cd backend && .venv\Scripts\python -m pytest     # testes do servidor
npx tsc --noEmit && npx expo lint                 # checagem do app
```
