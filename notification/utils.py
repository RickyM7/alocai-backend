import smtplib
import threading
from collections import defaultdict
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import Notificacao
from login.models import Usuario

def _send_mail_async(subject, message, from_email, recipient_list, html_message):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
            html_message=html_message
        )
    except smtplib.SMTPException as e:
        print(f"AVISO: Falha ao enviar e-mail de notificação para {recipient_list}: {e}")

def criar_notificacao_resumida_conflito(destinatario, agendamento_pai_conflitante, agendamentos_negados):
    """
    Cria uma única notificação e envia um email resumido para múltiplos conflitos
    """
    quantidade = len(agendamentos_negados)
    recurso_nome = agendamento_pai_conflitante.id_recurso.nome_recurso
    mensagem_curta = f"{quantidade} de seus horários para '{recurso_nome}' foram negados por conflito."

    # Cria a notificação curta no sistema
    Notificacao.objects.create(
        destinatario=destinatario,
        agendamento_pai=agendamento_pai_conflitante,
        mensagem=mensagem_curta
    )
    
    # Constrói e envia o email detalhado
    if settings.EMAIL_HOST_USER:
        horarios_html = "<ul>"
        for agendamento in agendamentos_negados:
            data_formatada = agendamento.data_inicio.strftime('%d/%m/%Y')
            hora_inicio = agendamento.hora_inicio.strftime('%H:%M')
            hora_fim = agendamento.hora_fim.strftime('%H:%M')
            horarios_html += f"<li>{data_formatada} das {hora_inicio} às {hora_fim}</li>"
        horarios_html += "</ul>"
        
        html_message = f"""
        <html>
            <body style="font-family: sans-serif;">
                <p>{mensagem_curta}</p>
                <p>Os seguintes horários não puderam ser aprovados pois outro agendamento foi confirmado para o mesmo recurso e horário:</p>
                {horarios_html}
                <p><br>Para mais detalhes, acesse o sistema Alocaí.</p>
            </body>
        </html>
        """
        
        thread = threading.Thread(target=_send_mail_async, args=(
            'Alocaí - Conflito de Agendamento',
            mensagem_curta,
            settings.DEFAULT_FROM_EMAIL,
            [destinatario.email],
            html_message
        ))
        thread.start()


def criar_e_enviar_notificacao(destinatario, agendamento_pai, mensagem):
    """
    Cria uma notificação curta no banco de dados e envia um email detalhado
    """
    Notificacao.objects.create(
        destinatario=destinatario,
        agendamento_pai=agendamento_pai,
        mensagem=mensagem
    )

    # Constrói e envia o email detalhado
    if settings.EMAIL_HOST_USER:
        solicitante = agendamento_pai.id_usuario.nome
        recurso = agendamento_pai.id_recurso.nome_recurso
        finalidade = agendamento_pai.finalidade
        observacoes = agendamento_pai.observacoes

        horarios_html = ""
        agendamentos_ordenados = agendamento_pai.agendamentos_filhos.select_related().order_by('data_inicio', 'hora_inicio')
        quantidade_agendamentos = agendamentos_ordenados.count()

        if quantidade_agendamentos > 5:
            primeira_data = agendamentos_ordenados.first().data_inicio.strftime('%d/%m/%Y')
            ultima_data = agendamentos_ordenados.last().data_inicio.strftime('%d/%m/%Y')
            horarios_html = f"<p>Esta solicitação contém <strong>{quantidade_agendamentos} agendamentos</strong> no período de <strong>{primeira_data}</strong> até <strong>{ultima_data}</strong>.</p>"
        else:
            horarios_html = "<ul>"
            for agendamento in agendamentos_ordenados:
                data_formatada = agendamento.data_inicio.strftime('%d/%m/%Y')
                hora_inicio = agendamento.hora_inicio.strftime('%H:%M')
                hora_fim = agendamento.hora_fim.strftime('%H:%M')
                horarios_html += f"<li>{data_formatada} das {hora_inicio} às {hora_fim}</li>"
            horarios_html += "</ul>"

        html_message = f"""
        <html>
            <body style="font-family: sans-serif;">
                <p>{mensagem}</p>
                <hr>
                <h3 style="color: #333;">Detalhes do Agendamento:</h3>
                <p><strong>Solicitante:</strong> {solicitante}</p>
                <p><strong>Recurso:</strong> {recurso}</p>
                <p><strong>Finalidade:</strong> {finalidade}</p>
        """
        if observacoes:
            html_message += f"<p><strong>Observações:</strong> {observacoes}</p>"

        html_message += f"""
                <p><strong>Datas e Horários Solicitados:</strong></p>
                {horarios_html}
                <p><br>Para gerenciar esta solicitação, acesse o sistema Alocaí.</p>
            </body>
        </html>
        """

        thread = threading.Thread(target=_send_mail_async, args=(
            'Alocaí - Notificação de Agendamento',
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [destinatario.email],
            html_message
        ))
        thread.start()

def notificar_admins(agendamento_pai, mensagem):
    """
    Cria notificações e envia emails para todos os admins
    """
    admins = Usuario.objects.select_related('id_perfil').filter(id_perfil__nome_perfil='Administrador')
    
    with transaction.atomic():
        notificacoes = [
            Notificacao(
                destinatario=admin,
                agendamento_pai=agendamento_pai,
                mensagem=mensagem
            )
            for admin in admins
        ]
        Notificacao.objects.bulk_create(notificacoes)
        
        for admin in admins:
            if settings.EMAIL_HOST_USER:
                solicitante = agendamento_pai.id_usuario.nome
                recurso = agendamento_pai.id_recurso.nome_recurso
                finalidade = agendamento_pai.finalidade
                observacoes = agendamento_pai.observacoes

                horarios_html = ""
                agendamentos_ordenados = agendamento_pai.agendamentos_filhos.select_related().order_by('data_inicio', 'hora_inicio')
                quantidade_agendamentos = agendamentos_ordenados.count()

                if quantidade_agendamentos > 5:
                    primeira_data = agendamentos_ordenados.first().data_inicio.strftime('%d/%m/%Y')
                    ultima_data = agendamentos_ordenados.last().data_inicio.strftime('%d/%m/%Y')
                    horarios_html = f"<p>Esta solicitação contém <strong>{quantidade_agendamentos} agendamentos</strong> no período de <strong>{primeira_data}</strong> até <strong>{ultima_data}</strong>.</p>"
                else:
                    horarios_html = "<ul>"
                    for agendamento in agendamentos_ordenados:
                        data_formatada = agendamento.data_inicio.strftime('%d/%m/%Y')
                        hora_inicio = agendamento.hora_inicio.strftime('%H:%M')
                        hora_fim = agendamento.hora_fim.strftime('%H:%M')
                        horarios_html += f"<li>{data_formatada} das {hora_inicio} às {hora_fim}</li>"
                    horarios_html += "</ul>"

                html_message = f"""
                <html>
                    <body style="font-family: sans-serif;">
                        <p>Olá {admin.nome},</p>
                        <p>{mensagem}</p>
                        <hr>
                        <h3 style="color: #333;">Detalhes do Agendamento:</h3>
                        <p><strong>Solicitante:</strong> {solicitante}</p>
                        <p><strong>Recurso:</strong> {recurso}</p>
                        <p><strong>Finalidade:</strong> {finalidade}</p>
                """
                if observacoes:
                    html_message += f"<p><strong>Observações:</strong> {observacoes}</p>"

                html_message += f"""
                        <p><strong>Datas e Horários Solicitados:</strong></p>
                        {horarios_html}
                        <p><br>Para gerenciar esta solicitação, acesse o sistema Alocaí.</p>
                    </body>
                </html>
                """
                
                thread = threading.Thread(target=_send_mail_async, args=(
                    'Alocaí - Nova Solicitação de Agendamento',
                    mensagem,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin.email],
                    html_message
                ))
                thread.start()

def criar_notificacoes_em_massa(notificacoes_data):
    """
    Função auxiliar para criar múltiplas notificações de uma vez
    Parâmetro notificacoes_data: lista de dicts com chaves: destinatario, agendamento_pai, mensagem
    """
    with transaction.atomic():
        notificacoes = [
            Notificacao(
                destinatario=dados['destinatario'],
                agendamento_pai=dados['agendamento_pai'],
                mensagem=dados['mensagem']
            )
            for dados in notificacoes_data
        ]
        Notificacao.objects.bulk_create(notificacoes)