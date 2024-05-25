from django.db import models
from django.utils import timezone

class Speaker(models.Model):
    """Спикер"""
    full_name = models.CharField("ФИО", max_length=200)
    topic = models.CharField("Тема доклада", max_length=200)
    phone_number = models.CharField("Номер телефона", max_length=20, null=True, blank=True)
    start_at = models.DateTimeField("Время начала")
    end_at = models.DateTimeField("Время окончания")
    created_at = models.DateTimeField(auto_now_add=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, default=timezone.now)

    def __str__(self):
        return self.full_name


class Event(models.Model):
    """Мероприятие"""
    title = models.CharField("Название", max_length=200)
    address = models.CharField("Адрес", max_length=200)
    start_at = models.DateTimeField("Время начала")
    end_at = models.DateTimeField("Время окончания")
    speakers = models.ManyToManyField(Speaker, verbose_name="Спикеры", related_name="events")
    created_at = models.DateTimeField(auto_now_add=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, default=timezone.now)

    def __str__(self):
        return self.title


class Question(models.Model):
    """Вопрос"""
    speaker = models.ForeignKey(Speaker, verbose_name="Спикер", on_delete=models.CASCADE, related_name="questions")
    question = models.TextField("Вопрос")
    answer = models.TextField("Ответ", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, default=timezone.now)

    def __str__(self):
        return f"Question to {self.speaker.full_name}"
