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

## :construction: Status do Projeto  
Em desenvolvimento  
Entrega parcial referente à 2ª VA (Gerência de Configuração)

## 📂 Organização

Este repositório está organizado com:
- `apps/` – Aplicações internas do sistema (ex: auth, reservas, laboratórios)
- `core/` – Configurações globais do projeto Django
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
Usuários reais ainda não foram cadastrados. A tela de login e rotas protegidas estão sendo integradas ao backend.

## 📎 Links relacionados
🔜 [Frontend do Alocaí (Nuxt 3)](https://github.com/Projeto-Des-SW/alocai-frontend)

## 👨‍🏫 Professor Responsável
[Rodrigo Gusmão de Carvalho Rocha](https://github.com/rgcrochaa)

Disciplina: Projeto de Desenvolvimento – UFAPE

Período: 2025.1
