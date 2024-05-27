import sys
import os
import django
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from django.utils import timezone
from django.db.models import Q
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event.settings')

django.setup()

from event_models.models import Event, Speaker, Question, NewSpeaker, Listener

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


class TelegramBot:
    def __init__(self):
        self.updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True, workers=8,
                               request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
        self.dispatcher = self.updater.dispatcher
        self.current_speaker = None

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(
            CommandHandler("send_mass_message", self.mass_message_handler))
        self.dispatcher.add_handler(CallbackQueryHandler(self.role_handler, pattern='^(listener|speaker|main_menu)$'))
        self.dispatcher.add_handler(
            CallbackQueryHandler(self.listener_handler, pattern='^(ask_question|show_schedule|subscribe)$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.speaker_handler,
                                                         pattern='^(view_questions|start_presentation|end_presentation|show_schedule)$'))
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
        message.reply_text('Привет! Я бот PythonMeetup. Я помогу тебе задать вопросы спикерам, посмотреть программу наших мероприятий и подписаться на уведомления о новых событиях. Пожалуйста, выбери свою роль:', reply_markup=reply_markup)

    def role_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()

        if query.data == 'listener':
            self.show_listener_menu(query)
        elif query.data == 'speaker':
            self.show_speaker_menu(query)
        elif query.data == 'main_menu':
            self.show_main_menu(query.message)

    def show_listener_menu(self, query) -> None:
        keyboard = [
            [InlineKeyboardButton("Задать вопрос", callback_data='ask_question')],
            [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')],
            [InlineKeyboardButton("Подписаться на новые мероприятия", callback_data='subscribe')],
            [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.message.reply_markup and query.message.reply_markup.inline_keyboard == reply_markup.inline_keyboard:
            return
        query.edit_message_reply_markup(reply_markup=reply_markup)

    def show_speaker_menu(self, query) -> None:
        speaker_id = query.from_user.id
        speaker = Speaker.objects.filter(telegram_id=speaker_id).first()
        if speaker:
            now = timezone.now()
            current_event = Event.objects.filter(start_at__lte=now, end_at__gte=speaker.start_at,
                                                 speakers=speaker).first()
            if current_event:
                keyboard = [
                    [InlineKeyboardButton("Посмотреть вопросы", callback_data='view_questions')],
                    [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')]
                ]
                if speaker.start_at <= now <= speaker.end_at and not speaker.is_active:
                    keyboard.append([InlineKeyboardButton("Начать выступление", callback_data='start_presentation')])
                elif speaker.is_active:
                    keyboard.append([InlineKeyboardButton("Закончить выступление", callback_data='end_presentation')])

                keyboard.append([InlineKeyboardButton("Главное меню", callback_data='main_menu')])
                reply_markup = InlineKeyboardMarkup(keyboard)
                if query.message.reply_markup and query.message.reply_markup.inline_keyboard == reply_markup.inline_keyboard:
                    return
                query.edit_message_reply_markup(reply_markup=reply_markup)
                query.message.reply_text(f'Добро пожаловать, {speaker.full_name}! Выберите действие:',
                                         reply_markup=reply_markup)
            else:
                query.message.reply_text('Вы не зарегистрированы на текущее мероприятие.')
        else:
            keyboard = [
                [InlineKeyboardButton("Хочу выступить", callback_data='new_speaker')],
                [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if query.message.reply_markup and query.message.reply_markup.inline_keyboard == reply_markup.inline_keyboard:
                return
            query.edit_message_reply_markup(reply_markup=reply_markup)
            query.message.reply_text(
                'Ваш ID не зарегистрирован как спикер. Пожалуйста, свяжитесь с организатором или подайте заявку:',
                reply_markup=reply_markup)

    def listener_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()

        if query.data == 'ask_question':
            query.message.reply_text('Введите ваш вопрос:')
            context.user_data['awaiting_question'] = True
            self.update_listener_menu(query)
        elif query.data == 'show_schedule':
            self.logger.info("Fetching event schedule...")
            now = timezone.now()
            events = Event.objects.filter(Q(start_at__lte=now, end_at__gte=now) | Q(start_at__gte=now))
            if events.exists():
                schedule = "\n".join([
                    f"*** {event.title} - {event.start_at.strftime('%Y-%m-%d %H:%M')} to {event.end_at.strftime('%Y-%m-%d %H:%M')} ***" if event.start_at <= now <= event.end_at else f"{event.title} - {event.start_at.strftime('%Y-%m-%d %H:%M')} to {event.end_at.strftime('%Y-%m-%d %H:%M')}"
                    for event in events
                ])
                query.message.reply_text(f'Программа мероприятия:\n{schedule}', parse_mode='Markdown')
            else:
                query.message.reply_text('Пока нет запланированных мероприятий.')
            self.update_listener_menu(query)
        elif query.data == 'subscribe':
            self.subscribe_handler(update, context)
            self.update_listener_menu(query)

    def update_listener_menu(self, query) -> None:
        keyboard = [
            [InlineKeyboardButton("Задать вопрос", callback_data='ask_question')],
            [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')],
            [InlineKeyboardButton("Подписаться на новые мероприятия", callback_data='subscribe')],
            [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.message.reply_markup and query.message.reply_markup.inline_keyboard == reply_markup.inline_keyboard:
            return
        query.edit_message_reply_markup(reply_markup=reply_markup)

    def speaker_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()
        speaker_id = query.from_user.id
        speaker = Speaker.objects.filter(telegram_id=speaker_id).first()

        if query.data == 'view_questions' and speaker:
            self.view_questions(query, speaker)
            self.update_speaker_menu(query, speaker)
        elif query.data == 'start_presentation' and speaker:
            self.start_presentation(query, context)
            self.update_speaker_menu(query, speaker)
        elif query.data == 'end_presentation' and speaker:
            self.end_presentation(query, context)
            self.update_speaker_menu(query, speaker)
        elif query.data == 'show_schedule':
            self.logger.info("Fetching event schedule...")
            now = timezone.now()
            events = Event.objects.filter(Q(start_at__lte=now, end_at__gte=now) | Q(start_at__gte=now))
            if events.exists():
                schedule = "\n".join([
                    f"*** {event.title} - {event.start_at.strftime('%Y-%m-%d %H:%M')} to {event.end_at.strftime('%Y-%m-%d %H-%M')} ***" if event.start_at <= now <= event.end_at else f"{event.title} - {event.start_at.strftime('%Y-%m-%d %H-%М')} to {event.end_at.strftime('%Y-%m-%d %H-%М')}"
                    for event in events
                ])
                query.message.reply_text(f'Программа мероприятия:\n{schedule}', parse_mode='Markdown')
            else:
                query.message.reply_text('Пока нет запланированных мероприятий.')
            self.update_speaker_menu(query, speaker)

    def update_speaker_menu(self, query, speaker) -> None:
        keyboard = [
            [InlineKeyboardButton("Посмотреть вопросы", callback_data='view_questions')],
            [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')]
        ]
        if speaker.is_active:
            keyboard.append([InlineKeyboardButton("Закончить выступление", callback_data='end_presentation')])
        else:
            keyboard.append([InlineKeyboardButton("Начать выступление", callback_data='start_presentation')])

        keyboard.append([InlineKeyboardButton("Главное меню", callback_data='main_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.message.reply_markup and query.message.reply_markup.inline_keyboard == reply_markup.inline_keyboard:
            return
        query.edit_message_reply_markup(reply_markup=reply_markup)

    def view_questions(self, query, speaker) -> None:
        questions = Question.objects.filter(speaker=speaker)
        if questions.exists():
            question_list = "\n".join([f"{q.id}. {q.question}" for q in questions])
            query.message.reply_text(
                f'Ваши вопросы:\n{question_list}\n\nВведите номер вопроса и ответ через тире, например "1 - ваш ответ"')
            self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.answer_question))
        else:
            query.message.reply_text('У вас пока нет вопросов.')

    def answer_question(self, update: Update, context: CallbackContext) -> None:
        message_text = update.message.text
        self.logger.info(f"Received answer: {message_text}")
        if "-" in message_text:
            question_id, answer = message_text.split(" - ", 1)
            question = Question.objects.filter(id=question_id.strip(), speaker__telegram_id=update.effective_user.id).first()
            if question:
                question.answer = answer
                question.save()
                self.logger.info(f"Answer saved for question {question_id}")
                context.bot.send_message(chat_id=question.telegram_id, text=f"Ответ на ваш вопрос: {answer}")
                update.message.reply_text("Ответ отправлен слушателю.")
            else:
                self.logger.error(f"Question with id {question_id} not found for speaker {update.effective_user.id}")
                update.message.reply_text("Вопрос не найден.")
        else:
            self.logger.error(f"Invalid answer format: {message_text}")
            update.message.reply_text("Неправильный формат. Пожалуйста, используйте формат 'номер вопроса - ваш ответ'.")

    def start_presentation(self, query: CallbackQuery, context: CallbackContext) -> None:
        speaker_id = query.from_user.id
        speaker = Speaker.objects.filter(telegram_id=speaker_id).first()
        if speaker:
            speaker.is_active = True
            speaker.save()
            self.current_speaker = speaker
            keyboard = [
                [InlineKeyboardButton("Посмотреть вопросы", callback_data='view_questions')],
                [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')],
                [InlineKeyboardButton("Закончить выступление", callback_data='end_presentation')],
                [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if query.message.reply_markup and query.message.reply_markup.inline_keyboard == reply_markup.inline_keyboard:
                return
            query.edit_message_reply_markup(reply_markup=reply_markup)
            query.message.reply_text(f'{speaker.full_name}, вы начали своё выступление.')

    def end_presentation(self, query: CallbackQuery, context: CallbackContext) -> None:
        speaker_id = query.from_user.id
        speaker = Speaker.objects.filter(telegram_id=speaker_id).first()
        if speaker:
            speaker.is_active = False
            speaker.save()
            if self.current_speaker == speaker:
                self.current_speaker = None
            keyboard = [
                [InlineKeyboardButton("Посмотреть вопросы", callback_data='view_questions')],
                [InlineKeyboardButton("Программа мероприятия", callback_data='show_schedule')],
                [InlineKeyboardButton("Начать выступление", callback_data='start_presentation')],
                [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if query.message.reply_markup and query.message.reply_markup.inline_keyboard == reply_markup.inline_keyboard:
                return
            query.edit_message_reply_markup(reply_markup=reply_markup)
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
            Question.objects.create(speaker=active_speaker, question=question_text,
                                    telegram_id=update.effective_user.id)
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

    def subscribe_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()
        telegram_id = query.from_user.id
        listener, created = Listener.objects.get_or_create(telegram_id=telegram_id)
        listener.subscribed = True
        listener.save()
        query.message.reply_text('Вы успешно подписаны на уведомления о новых мероприятиях.')

    def send_event_reminder(self):
        events = Event.objects.filter(start_at__date=timezone.now().date())
        for event in events:
            for participant in event.participants.all():
                self.updater.bot.send_message(chat_id=participant.telegram_id,
                                              text=f'Сегодня в {event.start_at.strftime("%H:%M")} начнется {event.title}')

    def send_mass_message(self, message_text: str) -> None:
        listeners = Listener.objects.filter(subscribed=True)
        for listener in listeners:
            self.updater.bot.send_message(chat_id=listener.telegram_id, text=message_text)

    def mass_message_handler(self, update: Update, context: CallbackContext) -> None:
        if context.args:
            message_text = " ".join(context.args)
            self.send_mass_message(message_text)
            update.message.reply_text("Сообщение отправлено всем подписанным пользователям.")
        else:
            update.message.reply_text("Пожалуйста, введите текст сообщения после команды.")

    def run(self) -> None:
        self.updater.start_polling()
        self.updater.idle()


if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()
