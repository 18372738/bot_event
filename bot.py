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
        [InlineKeyboardButton("Слушатель", callback_data='listener')],
        [InlineKeyboardButton("Спикер", callback_data='speaker')],
        [InlineKeyboardButton("Организатор", url='http://127.0.0.1:8000/admin')]  # Обнови URL на свой
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Привет! Выберите свою роль:', reply_markup=reply_markup)


def role_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'listener':
        keyboard = [
            [InlineKeyboardButton("Задать вопрос", callback_data='ask_question')],
            [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text('Выберите действие:', reply_markup=reply_markup)

    elif query.data == 'speaker':
        speaker_id = update.effective_user.id
        speaker = Speaker.objects.filter(telegram_id=speaker_id).first()
        if speaker:
            keyboard = [
                [InlineKeyboardButton("Посмотреть вопросы", callback_data='view_questions')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text(f'Добро пожаловать, {speaker.full_name}! Выберите действие:',
                                     reply_markup=reply_markup)
        else:
            query.message.reply_text('Ваш ID не зарегистрирован как спикер. Пожалуйста, свяжитесь с организатором.')


def listener_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'ask_question':
        query.message.reply_text('Введите ваш вопрос:')
        context.user_data['awaiting_question'] = True
    elif query.data == 'show_schedule':
        events = Event.objects.all()
        schedule = "\n".join([f"{event.title} - {event.start_at.strftime('%Y-%m-%d %H:%M')}" for event in events])
        query.message.reply_text(f'Программа мероприятия:\n{schedule}')


def speaker_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    speaker_id = update.effective_user.id
    speaker = Speaker.objects.filter(telegram_id=speaker_id).first()

    if query.data == 'view_questions' and speaker:
        questions = Question.objects.filter(speaker=speaker)
        if questions.exists():
            question_list = "\n".join([f"{q.question}" for q in questions])
            query.message.reply_text(f'Ваши вопросы:\n{question_list}')
        else:
            query.message.reply_text('У вас пока нет вопросов.')


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
    dispatcher.add_handler(CallbackQueryHandler(role_handler, pattern='^(listener|speaker)$'))
    dispatcher.add_handler(CallbackQueryHandler(listener_handler, pattern='^(ask_question|show_schedule)$'))
    dispatcher.add_handler(CallbackQueryHandler(speaker_handler, pattern='^view_questions$'))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
