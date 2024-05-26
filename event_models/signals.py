from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.conf import settings
from telegram import Bot
from .models import Event, Speaker

@receiver(m2m_changed, sender=Event.speakers.through)
def notify_speaker_added(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add':
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        for speaker_id in pk_set:
            speaker = Speaker.objects.get(pk=speaker_id)
            if speaker.telegram_id:
                bot.send_message(chat_id=speaker.telegram_id, text=f'Вы были добавлены в мероприятие "{instance.title}"')
