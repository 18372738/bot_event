import os
import django
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from django.utils import timezone
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event.settings')
django.setup()

from event_models.models import Event, Speaker, Question, NewSpeaker

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
            keyboard = [
                [InlineKeyboardButton("Хочу выступить", callback_data='new_speaker')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text(
                'Ваш ID не зарегистрирован как спикер. Пожалуйста, свяжитесь с организатором или подайте заявку:',
                reply_markup=reply_markup)


def new_speaker_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.message.reply_text('Пожалуйста, введите ваше ФИО:')
    context.user_data['awaiting_full_name'] = True


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


def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatch
