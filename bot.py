import os
import django
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from django.utils import timezone
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event.settings')
django.setup()

from event_models.models import Event, Speaker, Question

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Задать вопрос", callback_data='ask_question')],
        [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Привет! Это бот для мероприятия PythonMeetup. Выберите действие:', reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'ask_question':
        query.message.reply_text('Введите ваш вопрос:')
        context.user_data['awaiting_question'] = True
    elif query.data == 'show_schedule':
        events = Event.objects.all()
        schedule = "\n".join([f"{event.title} - {event.start_at.strftime('%Y-%m-%d %H:%M')}" for event in events])
        query.message.reply_text(f'Программа мероприятия:\n{schedule}')

def handle_message(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_question'):
        question_text = update.message.text
        current_speaker = Speaker.objects.filter(start_at__lte=timezone.now(), end_at__gte=timezone.now()).first()
        if not current_speaker:
            update.message.reply_text('Сейчас нет активного выступления.')
        else:
            Question.objects.create(speaker=current_speaker, question=question_text)
            update.message.reply_text(f'Ваш вопрос отправлен спикеру {current_speaker.full_name}.')
        context.user_data['awaiting_question'] = False

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
