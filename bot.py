import sys
import os
import django
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from django.utils import timezone
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event.settings')

django.setup()

from event_models.models import Event, Speaker, Question, NewSpeaker, Listener

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Установка кодировки по умолчанию
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

class TelegramBot:
    def __init__(self):
        self.updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True, workers=8, request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
        self.dispatcher = self.updater.dispatcher
        self.current_speaker = None

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CallbackQueryHandler(self.role_handler, pattern='^(listener|speaker|main_menu)$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.listener_handler, pattern='^(ask_question|show_schedule)$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.speaker_handler, pattern='^(view_questions|start_presentation|end_presentation|show_schedule)$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.new_speaker_handler, pattern='^new_speaker$'))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))

        # Планировщик для напоминаний
        self.scheduler = BackgroundScheduler()
        # Указание часового пояса для планировщика задач
        tz = pytz.timezone('Europe/Moscow')
        self.scheduler.add_job(self.send_event_reminder, 'cron', hour=9, minute=0, timezone=tz)
        self.scheduler.start()

    def start(self, update: Update, context: CallbackContext) -> None:
        self.save_listener(update.effective_user.id)
        self.show_main_menu(update.message)

    def save_listener(self, telegram_id: str) -> None:
        if not Listener.objects.filter(telegram_id=telegram_id).exists():
            Listener.objects.create(telegram_id=telegram_id)

    def show_main_menu(self, message) -> None:
        keyboard = [
            [InlineKeyboardButton("Слушатель", callback_data='listener')],
            [InlineKeyboardButton("Спикер", callback_data='speaker')],
            [InlineKeyboardButton("Организатор", url='http://127.0.0.1:8000/admin')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message.reply_text('Привет! Выберите свою роль:', reply_markup=reply_markup)

    def role_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()

        if query.data == 'listener':
            self.show_listener_menu(query.message)
        elif query.data == 'speaker':
            self.show_speaker_menu(query)
        elif query.data == 'main_menu':
            self.show_main_menu(query.message)

    def show_listener_menu(self, message) -> None:
        keyboard = [
            [InlineKeyboardButton("Задать вопрос", callback_data='ask_question')],
            [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')],
            [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message.reply_text('Выберите действие:', reply_markup=reply_markup)

    def show_speaker_menu(self, query) -> None:
        speaker_id = query.from_user.id
        speaker = Speaker.objects.filter(telegram_id=speaker_id).first()
        if speaker:
            current_event = Event.objects.filter(start_at__date=timezone.now().date(), speakers=speaker).first()
            now = timezone.now()
            if current_event:
                keyboard = [
                    [InlineKeyboardButton("Посмотреть вопросы", callback_data='view_questions')],
                    [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')],
                    [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
                ]
                if now >= speaker.start_at:
                    keyboard.append([InlineKeyboardButton("Начать выступление", callback_data='start_presentation')])
                if speaker.is_active:
                    keyboard.append([InlineKeyboardButton("Закончить выступление", callback_data='end_presentation')])
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.message.reply_text(f'Добро пожаловать, {speaker.full_name}! Выберите действие:', reply_markup=reply_markup)
            else:
                query.message.reply_text('Вы не зарегистрированы на текущее мероприятие.')
        else:
            keyboard = [
                [InlineKeyboardButton("Хочу выступить", callback_data='new_speaker')],
                [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text('Ваш ID не зарегистрирован как спикер. Пожалуйста, свяжитесь с организатором или подайте заявку:', reply_markup=reply_markup)

    def listener_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()

        if query.data == 'ask_question':
            query.message.reply_text('Введите ваш вопрос:')
            context.user_data['awaiting_question'] = True
        elif query.data == 'show_schedule':
            self.logger.info("Fetching event schedule...")
            events = Event.objects.all()
            if events.exists():
                schedule = "\n".join([f"{event.title} - {event.start_at.strftime('%Y-%m-%d %H:%M')}" for event in events])
                query.message.reply_text(f'Программа мероприятия:\n{schedule}')
            else:
                query.message.reply_text('Пока нет запланированных мероприятий.')

    def speaker_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()
        speaker_id = query.from_user.id
        speaker = Speaker.objects.filter(telegram_id=speaker_id).first()

        if query.data == 'view_questions' and speaker:
            self.view_questions(query, speaker)
        elif query.data == 'start_presentation' and speaker:
            self.start_presentation(query, speaker)
        elif query.data == 'end_presentation' and speaker:
            self.end_presentation(query, speaker)
        elif query.data == 'show_schedule':
            self.logger.info("Fetching event schedule...")
            events = Event.objects.all()
            if events.exists():
                schedule = "\n".join([f"{event.title} - {event.start_at.strftime('%Y-%m-%d %H:%M')}" for event in events])
                query.message.reply_text(f'Программа мероприятия:\n{schedule}')
            else:
                query.message.reply_text('Пока нет запланированных мероприятий.')

    def view_questions(self, query, speaker) -> None:
        questions = Question.objects.filter(speaker=speaker, approved=True)
        if questions.exists():
            question_list = "\n".join([f"{q.question}" for q in questions])
            query.message.reply_text(f'Ваши вопросы:\n{question_list}')
        else:
            query.message.reply_text('У вас пока нет вопросов.')

    def start_presentation(self, query, speaker) -> None:
        speaker.is_active = True
        speaker.save()
        self.current_speaker = speaker
        query.message.reply_text(f'{speaker.full_name}, вы начали своё выступление.')

    def end_presentation(self, query, speaker) -> None:
        speaker.is_active = False
        speaker.save()
        if self.current_speaker == speaker:
            self.current_speaker = None
            query.message.reply_text(f'{speaker.full_name}, вы закончили своё выступление.')

    def new_speaker_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()
        query.message.reply_text('Пожалуйста, введите ваше ФИО:')
        context.user_data['awaiting_full_name'] = True

    def handle_message(self, update: Update, context: CallbackContext) -> None:
        if context.user_data.get('awaiting_question'):
            self.process_question(update, context)
        elif context.user_data.get('awaiting_full_name'):
            self.process_full_name(update, context)
        elif context.user_data.get('awaiting_topic'):
            self.process_topic(update, context)
        elif context.user_data.get('awaiting_phone_number'):
            self.process_phone_number(update, context)

    def process_question(self, update: Update, context: CallbackContext) -> None:
        question_text = update.message.text
        active_speaker = Speaker.objects.filter(is_active=True).first()
        if not active_speaker:
            update.message.reply_text('Сейчас нет активного выступления.')
        else:
            Question.objects.create(speaker=active_speaker, question=question_text, approved=False)
            update.message.reply_text(f'Ваш вопрос отправлен спикеру.')
        context.user_data['awaiting_question'] = False

    def process_full_name(self, update: Update, context: CallbackContext) -> None:
        context.user_data['full_name'] = update.message.text
        update.message.reply_text('Введите тему доклада:')
        context.user_data['awaiting_topic'] = True
        context.user_data['awaiting_full_name'] = False

    def process_topic(self, update: Update, context: CallbackContext) -> None:
        context.user_data['topic'] = update.message.text
        update.message.reply_text('Введите номер телефона:')
        context.user_data['awaiting_phone_number'] = True
        context.user_data['awaiting_topic'] = False

    def process_phone_number(self, update: Update, context: CallbackContext) -> None:
        context.user_data['phone_number'] = update.message.text
        full_name = context.user_data['full_name']
        topic = context.user_data['topic']
        phone_number = context.user_data['phone_number']
        telegram_id = update.effective_user.id

        NewSpeaker.objects.create(full_name=full_name, topic=topic, phone_number=phone_number, telegram_id=telegram_id)
        update.message.reply_text('Спасибо за вашу заявку. Организатор свяжется с вами.')
        context.user_data['awaiting_phone_number'] = False

    def approve_question(self, question_id: int) -> None:
        question = Question.objects.get(id=question_id)
        question.approved = True
        question.save()

    def send_event_reminder(self):
        events = Event.objects.filter(start_at__date=timezone.now().date())
        for event in events:
            for participant in event.participants.all():
                self.updater.bot.send_message(chat_id=participant.telegram_id, text=f'Сегодня в {event.start_at.strftime("%H:%M")} начнется {event.title}')

    def run(self) -> None:
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()
