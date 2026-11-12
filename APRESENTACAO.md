# Apresentação do Bemoria

## Resumo

Bemoria é um protótipo de aplicação web para organizar medicamentos, horários, confirmação de doses e registros de saúde pessoais.

## Demonstração sugerida

1. Criar uma conta em `/register/`.
2. Cadastrar um medicamento e horários.
3. Mostrar a checklist diária e marcar uma dose como tomada.
4. Abrir o histórico e adicionar uma consulta, exame, vacina ou anotação.
5. Mostrar `/api/docs/` para apresentar a API REST.

Use somente informações fictícias durante a apresentação. O projeto ainda é um protótipo; os lembretes são registrados pelo worker Celery no log e não enviam notificações ao celular.

## Tecnologias

Django, Django REST Framework, PostgreSQL, JWT, Celery, Redis, Swagger/OpenAPI e pytest.

## Limitações atuais

- Upload e visualização de documentos médicos ainda não foram conectados à interface.
- A área de conteúdos educativos e clínicas está planejada, mas não implementada.
- Os lembretes ainda não têm canal de entrega (push, e-mail ou SMS).
