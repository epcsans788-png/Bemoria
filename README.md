# Bemoria

Aplicação web para organizar medicamentos, lembretes e informações de saúde, baseada nas referências visuais fornecidas.

## Escopo inicial

- Cadastro e autenticação de usuários
- Painel com resumo dos medicamentos do dia
- Cadastro de medicamentos, horários e confirmação de doses
- Histórico médico com consultas, exames, vacinas e documentos
- Área de saúde com condições e materiais educativos
- API Django REST Framework e banco PostgreSQL

## Estrutura

- `bemoria/`: configuração Django e Celery
- `health/`: modelos e páginas da área de saúde
- `templates/` e `static/`: interface responsiva
- `docs/`: requisitos iniciais
- `docker-compose.yml`: PostgreSQL e Redis para desenvolvimento local

## Desenvolvimento

Os requisitos e dados exibidos nas imagens são referências; nomes, diagnósticos e valores são exemplos, não dados reais. A versão atual é um primeiro esqueleto funcional e ainda não deve receber dados médicos reais.

## Requisitos locais

- Python 3.13 (64 bits)
- Docker Desktop com WSL 2, para PostgreSQL e Redis locais

Não é necessário instalar Node.js para esta primeira interface, que usa templates Django.

## Preparar o ambiente

1. Crie o arquivo local de ambiente a partir do exemplo: `Copy-Item .env.example .env`.
2. Crie e ative um ambiente virtual: `python -m venv .venv` e `\.venv\Scripts\Activate.ps1`.
3. Instale os pacotes Python: `python -m pip install -r requirements.txt`.
4. Inicie os serviços: `docker compose up -d`.
5. Aplique as migrações: `python manage.py migrate`.
6. Inicie o app: `python manage.py runserver` e abra `http://127.0.0.1:8000`.

Crie a conta pela interface em `/register/`; o endpoint de documentação da API fica em `/api/docs/`. A API usa JWT em `/api/token/` e `/api/token/refresh/`. O PostgreSQL do Docker é publicado na porta `5433` para evitar conflito com instalações locais.

Para processar lembretes em desenvolvimento, abra dois terminais adicionais com o ambiente virtual ativo e rode `celery -A bemoria worker -l info --pool=solo` e `celery -A bemoria beat -l info`. Nesta etapa o worker registra os horários devidos no log; entrega de notificações ainda será integrada.

As credenciais de `.env.example` são somente para desenvolvimento local; substitua-as antes de qualquer publicação.
