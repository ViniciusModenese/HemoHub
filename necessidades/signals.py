from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import NecessidadeSanguinea
from .servicos import notificar_doadores_proximos


@receiver(post_save, sender=NecessidadeSanguinea)
def disparar_notificacao_urgencia(sender, instance, **kwargs):
    if instance.deve_notificar:
        notificar_doadores_proximos(instance)
        NecessidadeSanguinea.objects.filter(pk=instance.pk).update(notificacao_enviada=True)
