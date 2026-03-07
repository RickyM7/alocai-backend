import html
import logging
import threading
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import Notificacao
from login.models import Usuario

logger = logging.getLogger(__name__)


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
    except Exception as e:
        logger.warning('Falha ao enviar e-mail de notificação para %s: %s', recipient_list, e)


def _disparar_email(subject, mensagem_texto, destinatario_email, html_message):
    thread = threading.Thread(
        target=_send_mail_async,
        args=(subject, mensagem_texto, settings.DEFAULT_FROM_EMAIL, [destinatario_email], html_message),
        daemon=True
    )
    thread.start()


def _build_horarios_html(agendamentos):
    """Renderiza a lista de horários de um agendamento como HTML."""
    if len(agendamentos) > 5:
        primeira_data = agendamentos[0].data_inicio.strftime('%d/%m/%Y')
        ultima_data = agendamentos[-1].data_inicio.strftime('%d/%m/%Y')
        return (
            f'<p>Esta solicitação contém <strong>{len(agendamentos)} agendamentos</strong> '
            f'no período de <strong>{primeira_data}</strong> até <strong>{ultima_data}</strong>.</p>'
        )
    items = ''.join(
        f'<li>{ag.data_inicio.strftime("%d/%m/%Y")} das {ag.hora_inicio.strftime("%H:%M")} às {ag.hora_fim.strftime("%H:%M")}</li>'
        for ag in agendamentos
    )
    return f'<ul>{items}</ul>'


def _build_email_html(agendamento_pai, mensagem, saudacao=''):
    """Constrói o corpo HTML padrão de notificação de agendamento."""
    solicitante = html.escape(agendamento_pai.id_usuario.nome)
    recurso = html.escape(agendamento_pai.id_recurso.nome_recurso)
    finalidade = html.escape(agendamento_pai.finalidade or '')
    observacoes = html.escape(agendamento_pai.observacoes or '') if agendamento_pai.observacoes else ''

    agendamentos = list(
        agendamento_pai.agendamentos_filhos.order_by('data_inicio', 'hora_inicio')
    )
    horarios_html = _build_horarios_html(agendamentos)

    obs_html = f'<p><strong>Observações:</strong> {observacoes}</p>' if observacoes else ''
    saudacao_html = f'<p>{html.escape(saudacao)}</p>' if saudacao else ''

    return f"""
    <html>
        <body style="font-family: sans-serif;">
            {saudacao_html}
            <p>{html.escape(mensagem)}</p>
            <hr>
            <h3 style="color: #333;">Detalhes do Agendamento:</h3>
            <p><strong>Solicitante:</strong> {solicitante}</p>
            <p><strong>Recurso:</strong> {recurso}</p>
            <p><strong>Finalidade:</strong> {finalidade}</p>
            {obs_html}
            <p><strong>Datas e Horários Solicitados:</strong></p>
            {horarios_html}
            <p><br>Para mais detalhes, acesse o sistema Alocaí.</p>
        </body>
    </html>
    """


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

    if settings.EMAIL_HOST_USER:
        horarios_html = _build_horarios_html(agendamentos_negados)
        html_message = f"""
        <html>
            <body style="font-family: sans-serif;">
                <p>{html.escape(mensagem_curta)}</p>
                <p>Os seguintes horários não puderam ser aprovados pois outro agendamento foi confirmado para o mesmo recurso e horário:</p>
                {horarios_html}
                <p><br>Para mais detalhes, acesse o sistema Alocaí.</p>
            </body>
        </html>
        """
        _disparar_email('Alocaí - Conflito de Agendamento', mensagem_curta, destinatario.email, html_message)


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
        html_message = _build_email_html(agendamento_pai, mensagem)
        _disparar_email('Alocaí - Notificação de Agendamento', mensagem, destinatario.email, html_message)

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
                html_message = _build_email_html(agendamento_pai, mensagem, saudacao=f'Olá {admin.nome},')
                _disparar_email('Alocaí - Nova Solicitação de Agendamento', mensagem, admin.email, html_message)