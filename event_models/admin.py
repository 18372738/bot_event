from django.contrib import admin
from .models import Event, Speaker, Question, NewSpeaker, Listener

@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'topic', 'start_at', 'end_at', 'telegram_id', 'is_active')
    list_filter = ('is_active', 'start_at', 'end_at')
    search_fields = ('full_name', 'topic', 'telegram_id')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_at', 'end_at', 'address')
    list_filter = ('start_at', 'end_at')
    search_fields = ('title', 'address')
    filter_horizontal = ('speakers', 'participants')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('speaker', 'question', 'answer', 'created_on', 'updated_on', 'telegram_id')
    list_filter = ('created_on', 'updated_on')
    search_fields = ('speaker__full_name', 'question', 'answer', 'telegram_id')

@admin.register(NewSpeaker)
class NewSpeakerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'topic', 'phone_number', 'telegram_id', 'created_on')
    list_filter = ('created_on',)
    search_fields = ('full_name', 'topic', 'phone_number', 'telegram_id')

@admin.register(Listener)
class ListenerAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'registered_on', 'subscribed')
    list_filter = ('registered_on', 'subscribed')
    search_fields = ('telegram_id',)
