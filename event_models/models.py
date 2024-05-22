from django.conf import settings
from django.db import models
from django.utils import timezone





class Speaker(models.Model):
    """Спикер"""

    full_name = models.CharField('ФИО', max_length=200)
    topic = models.CharField('Тема доклада', max_length=200)
    phone_number = models.IntegerField("Номер телефона", null=True, blank=True)
    start_at = models.DateTimeField("Время начала")
    end_at = models.DateTimeField("Время окончания")

    def __str__(self):
        return self.full_name


class Event(models.Model):
    """Мероприятие"""

    title = models.CharField('Название', max_length=200)
    address = models.CharField('Адрес', max_length=200)
    start_at = models.DateTimeField("Время начала")
    end_at = models.DateTimeField("Время окончания")
    speakers = models.ManyToManyField(Speaker, verbose_name="Спикеры", related_name="events")

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Вопрос, ответ"""

    speaker = models.ForeignKey(Speaker, verbose_name="Спикер", on_delete=models.CASCADE, related_name="speakers")
    question = models.TextField('Вопрос')
    answer = models.TextField('Ответ')

    def __str__(self):
        return self.speaker.full_name
