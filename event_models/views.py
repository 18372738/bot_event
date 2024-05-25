from django.shortcuts import render, get_object_or_404, redirect
from .models import Event, Speaker, Question
from .forms import EventForm, SpeakerForm, QuestionForm

def event_list(request):
    events = Event.objects.all()
    return render(request, 'event_list.html', {'events': events})

def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'event_detail.html', {'event': event})

def question_create(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('event_list')
    else:
        form = QuestionForm()
    return render(request, 'question_form.html', {'form': form})
