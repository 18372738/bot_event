import os
import django
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from django.utils import timezone
from dotenv import load_dotenv
import time

# Загрузка переменных окружения из .env файла
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event.settings')
django.setup()

from event_models.models import Event, Speaker, Question, NewSpeaker

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

current_speaker = None

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Слушатель", callback_data='listener')],
        [InlineKeyboardButton("Спикер", callback_data='speaker')],
        [InlineKeyboardButton("Организатор", url='http://127.0.0.1:8000/admin')]
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
                [InlineKeyboardButton("Начать выступление", callback_data='start_presentation')],
                [InlineKeyboardButton("Закончить выступление", callback_data='end_presentation')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text(f'Добро пожаловать, {speaker.full_name}! Выберите действие:', reply_markup=reply_markup)
        else:
            keyboard = [
                [InlineKeyboardButton("Хочу выступить", callback_data='new_speaker')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text('Ваш ID не зарегистрирован как спикер. Пожалуйста, свяжитесь с организатором или подайте заявку:', reply_markup=reply_markup)

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
    global current_speaker
    speaker_id = update.effective_user.id
    speaker = Speaker.objects.filter(telegram_id=speaker_id).first()

    if query.data == 'view_questions' and speaker:
        questions = Question.objects.filter(speaker=speaker)
        if questions.exists():
            question_list = "\n".join([f"{q.question}" for q in questions])
            query.message.reply_text(f'Ваши вопросы:\n{question_list}')
        else:
            query.message.reply_text('У вас пока нет вопросов.')

    elif query.data == 'start_presentation' and speaker:
        current_speaker = speaker
        query.message.reply_text(f'{speaker.full_name}, вы начали своё выступление.')

    elif query.data == 'end_presentation' and speaker:
        if current_speaker == speaker:
            current_speaker = None
            query.message.reply_text(f'{speaker.full_name}, вы закончили своё выступление.')

def new_speaker_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.message.reply_text('Пожалуйста, введите ваше ФИО:')
    context.user_data['awaiting_full_name'] = True

def handle_message(update: Update, context: CallbackContext) -> None:
    global current_speaker
    if context.user_data.get('awaiting_question'):
        question_text = update.message.text
        if not current_speaker:
            update.message.reply_text('Сейчас нет активного выступления.')
        else:
            Question.objects.create(speaker=current_speaker, question=question_text)
            update.message.reply_text(f'Ваш вопрос отправлен спикеру {current_speaker.full_name}.')
        context.user_data['awaiting_question'] = False

    elif context.user_data.get('awaiting_full_name'):
        context.user_data['full_name'] = update.message.text
        update.message.reply_text('Введите тему доклада:')
        context.user_data['awaiting_topic'] = True
        context.user_data['awaiting_full_name'] = False

    elif context.user_data.get('awaiting_topic'):
        context.user_data['topic'] = update.message.text
        update.message.reply_text('Введите номер телефона:')
        context.user_data['awaiting_phone_number'] = True
        context.user_data['awaiting_topic'] = False

    elif context.user_data.get('awaiting_phone_number'):
        context.user_data['phone_number'] = update.message.text
        full_name = context.user_data['full_name']
        topic = context.user_data['topic']
        phone_number = context.user_data['phone_number']
        telegram_id = update.effective_user.id

        NewSpeaker.objects.create(full_name=full_name, topic=topic, phone_number=phone_number, telegram_id=telegram_id)
        update.message.reply_text('Спасибо за вашу заявку. Организатор свяжется с вами.')
        context.user_data['awaiting_phone_number'] = False

# Создание экземпляра Updater
updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True, workers=8, request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
dispatcher = updater.dispatcher

def run_bot() -> None:
    while True:
        try:
            dispatcher.add_handler(CommandHandler("start", start))
            dispatcher.add_handler(CallbackQueryHandler(role_handler, pattern='^(listener|speaker)$'))
            dispatcher.add_handler(CallbackQueryHandler(listener_handler, pattern='^(ask_question|show_schedule)$'))
            dispatcher.add_handler(CallbackQueryHandler(speaker_handler, pattern='^(view_questions|start_presentation|end_presentation)$'))
            dispatcher.add_handler(CallbackQueryHandler(new_speaker_handler, pattern='^new_speaker$'))
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

            updater.start_polling()
            updater.idle()
        except Exception as e:
            logger.error(f"Error: {e}. Restarting bot in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    run_bot()
