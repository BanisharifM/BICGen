from django.contrib import admin
from .models import *


admin.site.register([TelegramState, TelegramUser, TelegramChat, Report])