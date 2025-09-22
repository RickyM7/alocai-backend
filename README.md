# Sistema de Gerenciamento de Laboratórios - Alocaí (Backend)

## :octocat: Integrantes  
[Gison Vilaça](https://github.com/gison-vilaca) | [Lucas Victor](https://github.com/lucasvictoor) | [Ricardo Martins](https://github.com/RickyM7) | [Sara Abreu](https://github.com/ynjisng)

## :page_with_curl: Sobre o Projeto  
Este repositório contém a API backend do sistema **Alocaí**, uma aplicação web para gerenciamento e agendamento de uso de laboratórios, desenvolvida com **Django** e **Django Rest Framework**. O projeto está sendo realizado para a disciplina de **Projeto de Desenvolvimento** do curso de **Bacharelado em Ciência da Computação** da **UFAPE**, sob orientação do professor [Rodrigo Gusmão de Carvalho Rocha](https://github.com/rgcrochaa), como parte da **2ª Verificação de Aprendizagem**.

O backend fornece os endpoints REST necessários para autenticação, cadastro de laboratórios, agendamento de uso e controle de permissões, funcionando como base de dados e lógica da aplicação. O frontend correspondente está disponível [neste repositório](https://github.com/Projeto-Des-SW/alocai-frontend).

## :round_pushpin: Objetivos do Sistema  
- Permitir que servidores da instituição solicitem horários em laboratórios de forma digital, segura e centralizada.  
- Automatizar o fluxo antes realizado manualmente via planilhas e e-mail.  
- Oferecer diferentes visões conforme o tipo de usuário (ex: coordenador, secretaria, etc).  
- Permitir especificações como:
  - Capacidade mínima de alunos  
  - Softwares específicos desejados  
  - Tipo de laboratório (comum ou especializado)

## :hammer_and_wrench: Tecnologias Usadas  
- [Python 3](https://www.python.org/)  
- [Django](https://www.djangoproject.com/)  
- [Django Rest Framework](https://www.django-rest-framework.org/)  
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)

## :construction: Status do Projeto  
Finalizado 
Entrega Final referente à 2ª VA

## 📂 Organização

Este repositório está organizado com:
- `alocai/` – Projeto Django (configurações, `settings.py`, `urls.py`, etc.)
- `booking/` – App de agendamentos (CRUD de solicitações, aprovação e status)
- `login/` – App de autenticação (Google OAuth, JWT, administração)
- `notification/` – App de notificações (listar e marcar como lidas)
- `resources/` – App de recursos (laboratórios e administração dos recursos)
- `user_profile/` – Perfis de acesso e visibilidade
- `requirements.txt` – Dependências do projeto
- `manage.py` – Comando principal para execução

## 🚀 Instruções para rodar localmente

1. **Clonar o repositório:**
   
   git clone https://github.com/Projeto-Des-SW/alocai-backend.git

   cd alocai-backend

2. **Criar ambiente virtual e ativar:**
   
   python -m venv venv

   Windows: venv\Scripts\activate

   Linux/Mac: source venv/bin/activate

3. **Instalar as dependências:**

   pip install -r requirements.txt

4. **Rodar as migrações e iniciar o servidor:**

   python manage.py migrate  

   python manage.py runserver

   O backend estará disponível em: http://localhost:8000

## 🔐 Acesso
O backend utiliza autenticação via **JWT** e login com **Google OAuth**.

- Por padrão, as permissões globais exigem autenticação (`IsAuthenticated`), conforme `REST_FRAMEWORK` em `alocai/settings.py`.
- Endpoints públicos incluem: `POST /api/token/`, `POST /api/token/refresh/`, `GET /health_check` e rotas de login Google.
- Usuário Administrador: defina `ADMIN_EMAIL` e `ADMIN_PASSWORD` no `.env` antes de rodar `migrate` para criação/atualização automática (ver migração `login/migrations/0002_create_admin_user.py`).

Fluxos de autenticação:
- JWT: obtenha o par de tokens em `POST /api/token/` e use o `access` no header `Authorization: Bearer <token>`.
- Google: `POST /api/google-sign-in/` com o `credential` do Google One Tap; `POST /api/google-sign-out/` para logout.

## 📎 Links relacionados
🔜 [Frontend do Alocaí (Nuxt 3)](https://github.com/Projeto-Des-SW/alocai-frontend)

## 🔗 Endpoints principais

Base URL local: `http://localhost:8000`

- Autenticação (JWT):
  - `POST /api/token/` – Obter tokens
  - `POST /api/token/refresh/` – Renovar token

- Login (Google/Admin) – `login/urls.py`:
  - `POST /api/google-sign-in/`
  - `POST /api/google-sign-out/`
  - `GET /api/user/<id_usuario>/`
  - `GET /api/admin/users/`
  - `POST /api/admin/login/`
  - `POST /api/admin/link-google/`
  - `POST /api/admin/change-password/`

- Agendamentos – `booking/urls.py` (prefixo `api/`):
  - `POST /api/agendamentos/`
  - `GET /api/agendamentos/minhas-reservas/`
  - `GET /api/agendamentos/pai/<id_agendamento_pai>/`
  - `GET /api/admin/agendamentos/`
  - `PATCH /api/admin/agendamentos/<id_agendamento>/status/`
  - `PUT|PATCH|DELETE /api/admin/agendamentos/pai/<id_agendamento_pai>/`
  - `PATCH /api/agendamentos/pai/<id_agendamento_pai>/status/`
  - `PATCH /api/agendamentos/<id_agendamento>/status/`
  - `GET /api/recursos/<recurso_id>/disponibilidade/`

- Recursos – `resources/urls.py` (prefixo `api/admin/` para rotas administrativas):
  - `GET|POST /api/admin/recursos/`
  - `GET|PUT|PATCH|DELETE /api/admin/recursos/<id>/`
  - `GET /api/admin/recursos/<id_recurso>/agendamentos/`
  - Público autenticado: `GET /api/recursos/` (lista recursos)

- Notificações – `notification/urls.py` (prefixo `api/`):
  - `GET /api/notificacoes/`
  - `POST /api/notificacoes/marcar-como-lidas/`
  - `GET|PATCH|DELETE /api/notificacoes/<id>/`

- Perfis de Acesso – `user_profile/urls.py` (prefixo `api/`):
  - `GET /api/perfil-acesso/`

- Dashboard – `alocai/urls.py`:
  - `GET /api/dashboard/`
  - `GET /api/dashboard/calendar/`

- Saúde do serviço:
  - `GET /health_check`

## 👨‍🏫 Professor Responsável
[Rodrigo Gusmão de Carvalho Rocha](https://github.com/rgcrochaa)

Disciplina: Projeto de Desenvolvimento – UFAPE

Período: 2025.1