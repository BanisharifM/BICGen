from django.db import models
from django.db.models import CASCADE

from django_tgbot.models import AbstractTelegramUser, AbstractTelegramChat, AbstractTelegramState


class TelegramUser(AbstractTelegramUser):
    pass


class TelegramChat(AbstractTelegramChat):
    pass


class TelegramState(AbstractTelegramState):
    telegram_user = models.ForeignKey(TelegramUser, related_name='telegram_states', on_delete=CASCADE, blank=True, null=True)
    telegram_chat = models.ForeignKey(TelegramChat, related_name='telegram_states', on_delete=CASCADE, blank=True, null=True)

    class Meta:
        unique_together = ('telegram_user', 'telegram_chat')


class Report(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    fig = models.ImageField(upload_to='figs')
    params = models.JSONField()
    target = models.CharField(max_length=30)

