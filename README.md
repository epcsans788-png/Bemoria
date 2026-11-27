# Bemoria

Bemoria é um espaço pessoal para organizar medicamentos, horários, informações de saúde, documentos e locais de cuidado. A interface foi desenhada para celular e computador.

## Recursos

- Conta, login e recuperação de senha.
- Painel diário com checklist de doses, registros tomados ou desmarcados e histórico.
- Cadastro, edição e arquivamento de medicamentos, horários e dias da semana.
- Perfil editável com tipo sanguíneo, alergias, data de nascimento, altura, peso, telefone, foto e contato de emergência.
- Cartão privado de acesso rápido às informações de emergência cadastradas.
- Linha do tempo de consultas, exames, vacinas e anotações.
- Envio, download e remoção de documentos médicos; os arquivos exigem autenticação.
- Acompanhamento pessoal de condições de saúde.
- Biblioteca de materiais públicos com fonte identificada.
- Lista privada de clínicas salvas, com busca por nome, especialidade ou endereço.
- Lembretes de medicamento enviados por e-mail quando o Celery está rodando.
- API REST com autenticação JWT e documentação Swagger.

## Tecnologias

- Django, Django REST Framework e Django ORM
- PostgreSQL
- Simple JWT e Django Auth
- Celery e Redis
- Django Storage local para desenvolvimento
- drf-spectacular / Swagger e django-cors-headers
- pytest, pytest-django e DRF APIClient
- Django Templates e CSS responsivo; Node.js não é necessário

## Requisitos locais

- Python 3.13 (64 bits)
- Docker Desktop com WSL 2, para PostgreSQL e Redis

## Preparar e iniciar

No terminal PowerShell do VS Code, na pasta do projeto:

1. Se ainda não existir `.env`, crie a partir do exemplo: `Copy-Item .env.example .env`.
2. Crie o ambiente virtual: `python -m venv .venv`.
3. Instale as dependências: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
4. Inicie PostgreSQL e Redis: `docker compose up -d`.
5. Aplique as migrações: `.\.venv\Scripts\python.exe manage.py migrate`.
6. Inicie o site: `.\.venv\Scripts\python.exe manage.py runserver`.
7. Abra `http://127.0.0.1:8000` e crie sua conta em `/register/`.

O PostgreSQL do Docker usa a porta local `5433`. No modo de desenvolvimento, os e-mails de recuperação e os lembretes aparecem no terminal do Django. Para receber e-mails de verdade, configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` e `DEFAULT_FROM_EMAIL` no ambiente.

## Ativar lembretes

Mantenha o Django em um terminal. Em outros dois terminais do VS Code, inicie o worker e o agendador:

```powershell
.\.venv\Scripts\celery.exe -A bemoria worker -l info --pool=solo
```

```powershell
.\.venv\Scripts\celery.exe -A bemoria beat -l info
```

O agendador verifica os horários a cada minuto. Em desenvolvimento, os e-mails são impressos no terminal do worker por meio do backend de e-mail do Django.

## Endereços úteis

- `/perfil/` — informações pessoais e foto
- `/emergencia/` — cartão de emergência privado
- `/medicamentos/` — rotina e horários
- `/historico/` e `/historico/doses/` — linha do tempo de saúde e doses
- `/documentos/` — arquivos privados
- `/saude/` — condições e biblioteca educativa
- `/clinicas/` — locais salvos e busca
- `/api/docs/` — documentação da API

## Testes e segurança

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Use apenas dados fictícios nesta versão acadêmica local. Antes de qualquer implantação pública ou uso com dados médicos reais, é necessário configurar armazenamento, envio de e-mail, backups, HTTPS e os controles de privacidade adequados. Os materiais educativos são referências públicas e não substituem aconselhamento profissional.
