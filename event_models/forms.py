from django import forms
from .models import Event, Speaker, Question, NewSpeaker

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'address', 'start_at', 'end_at', 'speakers']

class SpeakerForm(forms.ModelForm):
    class Meta:
        model = Speaker
        fields = ['full_name', 'topic', 'phone_number', 'start_at', 'end_at']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['speaker', 'question', 'answer']

class NewSpeakerForm(forms.ModelForm):
    class Meta:
        model = NewSpeaker
        fields = ['full_name', 'topic', 'phone_number', 'telegram_id']
