from django.contrib import admin
from .models import Event, Speaker, Question, NewSpeaker, Listener

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_at', 'end_at', 'created_on', 'updated_on')
    search_fields = ('title',)
    list_filter = ('start_at', 'end_at')

@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'topic', 'start_at', 'end_at', 'created_on', 'updated_on', 'telegram_id')
    search_fields = ('full_name', 'topic')
    list_filter = ('start_at', 'end_at')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('speaker', 'question', 'answer', 'created_on', 'updated_on')
    search_fields = ('speaker__full_name', 'question', 'answer')
    list_filter = ('created_on', 'updated_on')

@admin.register(NewSpeaker)
class NewSpeakerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'topic', 'phone_number', 'telegram_id', 'created_on')
    search_fields = ('full_name', 'topic')
    list_filter = ('created_on',)

@admin.register(Listener)
class ListenerAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'registered_on')
    search_fields = ('telegram_id',)
    list_filter = ('registered_on',)
