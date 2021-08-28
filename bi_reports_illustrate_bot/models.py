from bi_report.settings import BI_SITE_URL
from django.db import models
from django.db.models import CASCADE
from django.conf import settings

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
    owner = models.ForeignKey(TelegramUser, related_name='reports', on_delete=CASCADE)
    name = models.CharField(max_length=200)
    fig = models.ImageField(upload_to='figs')
    params = models.JSONField()
    target = models.CharField(max_length=30)

    def __str__(self):
        repr_string = f"{self.name}\n"\
        f"{self.created.date()}\n"\
        f"{settings.BI_SITE_URL + self.fig.url}\n"
        return repr_string
    
    # def get_with_icon(self):
    #     repr_string = \
    #     f"🗒 {self.name}\n" \
    #     f"📅 {self.created.date()}\n" \
    #     f"⬇ [Download Link]({settings.BI_SITE_URL + self.fig.url})\n"
    #     return repr_string
    
    def get_with_icon(self):
        repr_string = \
        f"🗒 `{self.name}`\n" \
        f"📅 `{self.created.date()}`\n" \
        f"⬇ [Download Link]({settings.BI_SITE_URL + self.fig.url})\n"
        return repr_string
        