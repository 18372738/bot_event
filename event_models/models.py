from django.db import models

class Speaker(models.Model):
    """Спикер"""
    full_name = models.CharField("ФИО", max_length=200)
    topic = models.CharField("Тема доклада", max_length=200)
    phone_number = models.CharField("Номер телефона", max_length=20, null=True, blank=True)
    start_at = models.DateTimeField("Время начала")
    end_at = models.DateTimeField("Время окончания")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    telegram_id = models.CharField("Telegram ID", max_length=50, null=True, blank=True)
    is_active = models.BooleanField("Активен", default=False)

    def __str__(self):
        return self.full_name


class Event(models.Model):
    """Мероприятие"""
    title = models.CharField("Название", max_length=200)
    address = models.CharField("Адрес", max_length=200)
    start_at = models.DateTimeField("Время начала")
    end_at = models.DateTimeField("Время окончания")
    speakers = models.ManyToManyField(Speaker, verbose_name="Спикеры", related_name="events")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    participants = models.ManyToManyField('Listener', verbose_name="Участники", related_name="events", blank=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    """Вопрос"""
    speaker = models.ForeignKey(Speaker, verbose_name="Спикер", on_delete=models.CASCADE, related_name="questions")
    question = models.TextField("Вопрос")
    answer = models.TextField("Ответ", blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    telegram_id = models.CharField("Telegram ID слушателя", max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Question to {self.speaker.full_name}"

class NewSpeaker(models.Model):
    """Заявка на спикера"""
    full_name = models.CharField("ФИО", max_length=200)
    topic = models.CharField("Тема доклада", max_length=200)
    phone_number = models.CharField("Номер телефона", max_length=20, null=True, blank=True)
    telegram_id = models.CharField("Telegram ID", max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

class Listener(models.Model):
    """Слушатель"""
    telegram_id = models.CharField("Telegram ID", max_length=50, unique=True)
    registered_on = models.DateTimeField(auto_now_add=True)
    subscribed = models.BooleanField("Подписан", default=False)

    def __str__(self):
        return f"Listener {self.telegram_id}"
