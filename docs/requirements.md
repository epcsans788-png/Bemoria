# Requisitos iniciais — Bemoria

Este documento organiza os requisitos visíveis nas referências fornecidas. Elementos como nomes, diagnósticos, peso, idade e eventos médicos das capturas são dados ilustrativos e não devem ser usados como dados reais.

## Problema e objetivo

Pessoas que usam medicamentos de forma contínua ou recorrente precisam de uma forma simples de organizar horários, doses e informações de saúde. O Bemoria centraliza esses registros e facilita o acompanhamento pessoal.

## Funcionalidades

1. Conta de usuário com cadastro e login.
2. Painel inicial com próximos horários e doses do dia.
3. Cadastro de medicamentos, instruções, frequência e horários.
4. Registro de dose tomada ou não tomada, com histórico.
5. Histórico de saúde com informações básicas, consultas, exames, vacinas e documentos.
6. Armazenamento privado de documentos e imagens médicas.
7. Área de saúde com condições registradas e conteúdo educativo.
8. Busca de clínicas e acesso rápido a informações de emergência.
9. Lembretes de horários por notificação.

## Base técnica indicada na apresentação

- Backend: Django e Django REST Framework
- Banco de dados: PostgreSQL
- Autenticação: JWT
- Tarefas de lembrete: Celery e Redis
- Armazenamento de arquivos: Django Storage
- Documentação da API: OpenAPI/Swagger
- Testes: pytest, pytest-django e DRF APIClient

## Telas de referência

- Login e cadastro
- Meus medicamentos / cronograma
- Histórico médico com abas
- Educação e Saúde
- Apresentação do projeto, etapas e cronograma

## Cuidados com os dados

Informações médicas e documentos são sensíveis. A aplicação deve restringir cada registro ao seu titular, validar uploads, manter segredos fora do Git e nunca usar as informações fictícias das capturas como registros de usuários.
