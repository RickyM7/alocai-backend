from django.db import models
from django.conf import settings
from django.utils import timezone
from resources.models import Recurso, StatusRecurso

class AgendamentoPai(models.Model):
    id_agendamento_pai = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agendamentos_pai"
    )
    id_recurso = models.ForeignKey(
        Recurso,
        on_delete=models.CASCADE
    )
    finalidade = models.CharField(max_length=255, null=True, blank=True)
    observacoes = models.TextField(null=True, blank=True)
    software_necessario = models.TextField(null=True, blank=True)
    id_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="responsabilidades_pai"
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agendamento_pai'

    def __str__(self):
        return f"Solicitação #{self.id_agendamento_pai} - {self.id_recurso}"


class StatusAgendamento(models.TextChoices):
    PENDENTE = 'pendente', 'Pendente'
    APROVADO = 'aprovado', 'Aprovado'
    NEGADO = 'negado', 'Negado'
    CANCELADO = 'cancelado', 'Cancelado'
    CONCLUIDO = 'concluido', 'Concluído'


class Agendamento(models.Model):
    id_agendamento = models.AutoField(primary_key=True)
    agendamento_pai = models.ForeignKey(
        AgendamentoPai,
        on_delete=models.CASCADE,
        related_name="agendamentos_filhos",
        null=True,
        blank=True
    )
    data_inicio = models.DateField()
    hora_inicio = models.TimeField()
    data_fim = models.DateField()
    hora_fim = models.TimeField()
    status_agendamento = models.CharField(
        max_length=20,
        choices=StatusAgendamento.choices,
        default=StatusAgendamento.PENDENTE
    )
    data_ultima_atualizacao = models.DateTimeField(auto_now=True)
    gerenciado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="agendamentos_gerenciados",
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'agendamento'

    def __str__(self):
        return f"Agendamento #{self.id_agendamento} - {self.data_inicio} {self.hora_inicio}-{self.hora_fim} ({self.status_agendamento})"


class UsoImediato(models.Model):
    """Registro de uso imediato de recurso por Terceirizado."""

    id_uso = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usos_imediatos"
    )
    id_recurso = models.ForeignKey(
        Recurso,
        on_delete=models.CASCADE,
        related_name="usos_imediatos"
    )
    finalidade = models.CharField(max_length=255, null=True, blank=True)
    observacoes = models.TextField(null=True, blank=True)
    duracao_minutos = models.PositiveIntegerField(
        default=120,
        help_text='Duração prevista em minutos'
    )
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'uso_imediato'
        ordering = ['-data_inicio']

    def __str__(self):
        return f"Uso #{self.id_uso} - {self.id_recurso} ({'ativo' if self.ativo else 'finalizado'})"

    @property
    def expirado(self):
        """Verifica se o uso excedeu a duração prevista."""
        if not self.ativo:
            return False
        from datetime import timedelta
        limite = self.data_inicio + timedelta(minutes=self.duracao_minutos)
        return timezone.now() > limite

    def finalizar(self):
        """Finaliza o uso e libera o recurso se não houver outros usos ativos."""
        self.ativo = False
        self.data_fim = timezone.now()
        self.save(update_fields=['ativo', 'data_fim'])
        # Só libera o recurso se não houver outros usos ativos para ele
        outros_ativos = UsoImediato.objects.filter(
            id_recurso=self.id_recurso, ativo=True
        ).exclude(pk=self.pk).exists()
        if not outros_ativos:
            self.id_recurso.status_recurso = StatusRecurso.DISPONIVEL
            self.id_recurso.save(update_fields=['status_recurso'])