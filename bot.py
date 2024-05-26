import os
import django
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from django.utils import timezone
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event.settings')
django.setup()

from event_models.models import Event, Speaker, Question, NewSpeaker

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

class TelegramBot:
    def __init__(self):
        self.updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True, workers=8,
                               request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
        self.dispatcher = self.updater.dispatcher
        self.current_speaker = None

        # Настройка логирования
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Register handlers
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CallbackQueryHandler(self.role_handler,
                                                         pattern='^(listener|speaker|main_menu)$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.listener_handler,
                                                         pattern='^(ask_question|show_schedule)$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.speaker_handler,
                                                         pattern='^(view_questions|start_presentation|end_presentation)$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.new_speaker_handler,
                                                         pattern='^new_speaker$'))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))

    def start(self, update: Update, context: CallbackContext) -> None:
        self.show_main_menu(update.message)

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
            keyboard = [
                [InlineKeyboardButton("Задать вопрос", callback_data='ask_question')],
                [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')],
                [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
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
                    [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.message.reply_text(f'Добро пожаловать, {speaker.full_name}! Выберите действие:',
                                         reply_markup=reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("Хочу выступить", callback_data='new_speaker')],
                    [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.message.reply_text(
                    'Ваш ID не зарегистрирован как спикер. Пожалуйста, свяжитесь с организатором или подайте заявку:',
                    reply_markup=reply_markup)

        elif query.data == 'main_menu':
            self.show_main_menu(query.message)

    def listener_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()

        if query.data == 'ask_question':
            query.message.reply_text('Введите ваш вопрос:')
            context.user_data['awaiting_question'] = True
        elif query.data == 'show_schedule':
            events = Event.objects.all()
            schedule = "\n".join([f"{event.title} - {event.start_at.strftime('%Y-%м-%d %H:%М')}" for event in events])
            query.message.reply_text(f'Программа мероприятия:\n{schedule}')

    def speaker_handler(self, update: Update, context: CallbackContext) -> None:
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

        elif query.data == 'start_presentation' and speaker:
            self.current_speaker = speaker
            query.message.reply_text(f'{speaker.full_name}, вы начали своё выступление.')

        elif query.data == 'end_presentation' and speaker:
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
            question_text = update.message.text
            if not self.current_speaker:
                update.message.reply_text('Сейчас нет активного выступления.')
            else:
                Question.objects.create(speaker=self.current_speaker, question=question_text)
                update.message.reply_text(f'Ваш вопрос отправлен спикеру {self.current_speaker.full_name}.')
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

    def run(self) -> None:
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()
