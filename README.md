# Alocaí — Backend

API REST do sistema **Alocaí**, uma plataforma para gerenciamento e agendamento de uso de laboratórios em instituições de ensino.

Desenvolvido com **Django 5** e **Django REST Framework**.

## :octocat: Integrantes

[Gison Vilaça](https://github.com/gison-vilaca) | [Lucas Victor](https://github.com/lucasvictoor) | [Ricardo Martins](https://github.com/RickyM7) | [Sara Abreu](https://github.com/ynjisng)

## :page_with_curl: Sobre o Projeto

Projeto da disciplina de **Projeto de Desenvolvimento** do curso de **Bacharelado em Ciência da Computação** da **UFAPE**, orientado pelo professor [Rodrigo Gusmão de Carvalho Rocha](https://github.com/rgcrochaa).

O backend fornece os endpoints REST para autenticação (Google OAuth + JWT), cadastro de recursos, agendamentos, uso imediato, notificações e controle de permissões. O frontend correspondente está em [alocai-frontend](https://github.com/Projeto-Des-SW/alocai-frontend).

## :hammer_and_wrench: Tecnologias

- [Python 3](https://www.python.org/)
- [Django 5](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Google Auth](https://google-auth.readthedocs.io/) (OAuth 2.0)
- [Gunicorn](https://gunicorn.org/) + [WhiteNoise](http://whitenoise.evans.io/) (produção)
- SQLite (dev) / PostgreSQL (produção via `dj-database-url`)

## 📂 Estrutura

```
alocai/          → Configurações do projeto Django (settings, urls, wsgi)
booking/         → Agendamentos e uso imediato (models, views, serializers)
login/           → Autenticação (Google OAuth, JWT, management commands)
notification/    → Notificações por e-mail e no sistema
resources/       → Cadastro e administração de recursos (laboratórios)
user_profile/    → Perfis de acesso e permissões
```

## 🚀 Configuração local

### 1. Clonar e criar ambiente virtual

```bash
git clone https://github.com/Projeto-Des-SW/alocai-backend.git
cd alocai-backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

Variáveis obrigatórias:
| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta do Django |
| `GOOGLE_OAUTH_CLIENT_ID` | Client ID do Google OAuth |
| `ADMIN_EMAIL` | E-mail do administrador inicial |
| `ADMIN_PASSWORD` | Senha do administrador inicial |

Variáveis opcionais:
| Variável | Descrição | Padrão |
|---|---|---|
| `DEBUG` | Modo de depuração | `True` |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos | `localhost,127.0.0.1` |
| `CORS_EXTRA_ORIGINS` | Origens CORS extras | (vazio) |
| `DATABASE_URL` | URL do banco de dados | SQLite local |
| `EMAIL_HOST_USER` | E-mail SMTP para notificações | (vazio) |
| `EMAIL_HOST_PASSWORD` | Senha do e-mail SMTP | (vazio) |

### 4. Rodar migrações e criar admin

```bash
python manage.py migrate
python manage.py create_admin
```

### 5. Iniciar o servidor

```bash
python manage.py runserver
```

O backend estará disponível em `http://localhost:8000`.

## 🧪 Testes

```bash
python manage.py test
```

O projeto possui **154 testes** cobrindo models, serializers, views, permissões, auto-expiração, notificações e health check.

## 🔐 Autenticação

- **JWT**: `POST /api/token/` para obter tokens; use `Authorization: Bearer <access>` nos headers.
- **Google OAuth**: `POST /api/google-sign-in/` com o `credential` do Google One Tap.
- **Admin**: login com e-mail e senha via `POST /api/admin/login/`.
- O refresh token é armazenado em cookie HttpOnly seguro.

## 🔗 Endpoints principais

| Grupo | Método | Rota | Descrição |
|---|---|---|---|
| **Auth** | POST | `/api/token/` | Obter par de tokens JWT |
| | POST | `/api/token/refresh/` | Renovar access token |
| **Login** | POST | `/api/google-sign-in/` | Login com Google |
| | POST | `/api/google-sign-out/` | Logout |
| | POST | `/api/admin/login/` | Login admin (e-mail + senha) |
| | POST | `/api/admin/link-google/` | Vincular Google ao admin |
| | POST | `/api/admin/change-password/` | Alterar senha do admin |
| | GET | `/api/admin/users/` | Listar usuários |
| | GET/PUT | `/api/user/<id>/` | Ver/editar usuário |
| **Agendamentos** | POST | `/api/agendamentos/` | Criar agendamento |
| | GET | `/api/agendamentos/minhas-reservas/` | Minhas reservas |
| | GET | `/api/agendamentos/pai/<id>/` | Detalhe do agendamento pai |
| | PATCH | `/api/agendamentos/pai/<id>/status/` | Alterar status (usuário) |
| | PATCH | `/api/agendamentos/<id>/status/` | Alterar status individual |
| | GET | `/api/admin/agendamentos/` | Listar todos (admin) |
| | PATCH | `/api/admin/agendamentos/<id>/status/` | Alterar status (admin) |
| | PUT/PATCH/DELETE | `/api/admin/agendamentos/pai/<id>/` | Gerenciar pai (admin) |
| | GET | `/api/recursos/<id>/disponibilidade/` | Disponibilidade do recurso |
| **Uso Imediato** | GET/POST | `/api/uso-imediato/` | Listar/registrar uso |
| | PATCH | `/api/uso-imediato/<id>/finalizar/` | Finalizar uso |
| **Recursos** | GET | `/api/recursos/` | Listar recursos (público) |
| | GET/POST | `/api/admin/recursos/` | CRUD admin |
| | GET/PUT/PATCH/DELETE | `/api/admin/recursos/<id>/` | Detalhe admin |
| **Notificações** | GET | `/api/notificacoes/` | Listar notificações |
| | POST | `/api/notificacoes/marcar-como-lidas/` | Marcar todas como lidas |
| | GET/PATCH/DELETE | `/api/notificacoes/<id>/` | Detalhe da notificação |
| **Dashboard** | GET | `/api/dashboard/` | Dados do dashboard |
| | GET | `/api/dashboard/calendar/` | Dados do calendário |
| **Perfis** | GET | `/api/perfil-acesso/` | Listar perfis |
| **Saúde** | GET | `/health_check` | Status do serviço |

## 👨‍🏫 Professor Responsável

[Rodrigo Gusmão de Carvalho Rocha](https://github.com/rgcrochaa)

Disciplina: Projeto de Desenvolvimento — UFAPE · 2025.1
