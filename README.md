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

**Planilha de alunos:** coloque a planilha em `backend/dados/alunos.xlsx` ou aponte `EXCEL_ALUNOS` no `.env` para o arquivo (ex.: `C:/Users/.../Controle Atrasos.xlsx`). A planilha precisa de uma linha de títulos com **Aluno** e **Turma**; **Responsável**, **Telefone (WhatsApp)**, **Situação/SIT** e **Matrícula** são opcionais. Só alunos com situação "Ativo" (ou vazia) entram no app. O servidor procura a aba certa sozinho. Para testar sem a planilha real: `python gerar_planilha_exemplo.py`.

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

Enquanto não estiver configurado, o app registra os atrasos normalmente e mostra "Sem envio". As credenciais ficam só no `backend/.env` (que não vai para o GitHub).

### Pela Twilio (padrão)

**Testes de campo — Sandbox (gratuito, sem aprovação):**

1. No [Console da Twilio](https://console.twilio.com/), copie o **Account SID** e o **Auth Token** (em *Account Info*).
2. Vá em **Messaging > Try it out > Send a WhatsApp message**. Ali aparece o número do Sandbox (**+1 415 523 8886**) e um código do tipo `join palavra-palavra`.
3. **Cada responsável que vai participar do teste** precisa mandar essa mensagem `join palavra-palavra` para +1 415 523 8886 pelo WhatsApp dele. Só esses números recebem os avisos. A adesão vale por 72 h; depois é só mandar o `join` de novo.
4. No `backend/.env`:

   ```
   WHATSAPP_PROVEDOR=twilio
   TWILIO_ACCOUNT_SID=ACxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxx
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```

5. Teste e reinicie o servidor:

   ```bash
   .venv\Scripts\python testar_whatsapp.py 11987654321
   ```

   O script mostra se a mensagem foi entregue ou o código de erro (ex.: 63015 = o número não fez o `join`).

**Uso definitivo (número próprio da escola):** registre um remetente de WhatsApp na Twilio (*Messaging > Senders > WhatsApp senders*, exige um perfil do Facebook Business), crie um modelo no **Content Template Builder** com as variáveis `{{1}}` aluno, `{{2}}` turma e `{{3}}` data/hora, envie para aprovação e preencha `TWILIO_WHATSAPP_FROM` com o número da escola e `TWILIO_CONTENT_SID` com o SID do modelo (`HX...`). Texto sugerido:

> Olá! Informamos que o(a) aluno(a) {{1}}, da turma {{2}}, chegou atrasado(a) à escola em {{3}}. Em caso de dúvidas, procure a coordenação.

A Twilio cobra por mensagem (mais a tarifa da Meta); confira os preços atuais.

### Pela Meta (alternativa)

Com `WHATSAPP_PROVEDOR=meta`, o envio usa a WhatsApp Cloud API direto: crie um app em [developers.facebook.com](https://developers.facebook.com/) com o produto WhatsApp, aprove um modelo `aviso_atraso` com as mesmas 3 variáveis e preencha `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`.

Os telefones podem estar na planilha com ou sem DDI/máscara — o servidor acrescenta o `55` quando falta. Se a planilha não tiver o telefone, o funcionário pode digitá-lo no app; ele fica salvo para os próximos registros.

## Alertas

No `backend/.env`: `ALERTA_LIMITE=3` e `ALERTA_JANELA_DIAS=30` → o app avisa quando um aluno chega ao 3º atraso em 30 dias.

## Desenvolvimento

```bash
cd backend && .venv\Scripts\python -m pytest     # testes do servidor
npx tsc --noEmit && npx expo lint                 # checagem do app
```
