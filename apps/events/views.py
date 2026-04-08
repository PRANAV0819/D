from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.accounts.decorators import verified_required, alumni_or_teacher_required
from .models import Event, EventRegistration
from .forms import EventForm


@login_required
@verified_required
def event_list_view(request):
    from django.utils import timezone
    events = Event.objects.filter(starts_at__gte=timezone.now())
    event_type = request.GET.get('type', '')
    if event_type:
        events = events.filter(event_type=event_type)
    registered_ids = set(EventRegistration.objects.filter(user=request.user).values_list('event_id', flat=True))
    return render(request, 'events/list.html', {
        'events': events, 'registered_ids': registered_ids,
        'event_type': event_type, 'type_choices': Event.EventType.choices,
    })


@login_required
@verified_required
def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    registered = EventRegistration.objects.filter(event=event, user=request.user).exists()
    return render(request, 'events/detail.html', {'event': event, 'registered': registered})


@login_required
@verified_required
@alumni_or_teacher_required
def create_event_view(request):
    form = EventForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.organizer = request.user
        event.save()
        messages.success(request, 'Event created!')
        return redirect('events:detail', pk=event.pk)
    return render(request, 'events/form.html', {'form': form})


@login_required
@verified_required
def register_event_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not EventRegistration.objects.filter(event=event, user=request.user).exists():
        EventRegistration.objects.create(event=event, user=request.user)
        messages.success(request, f'Registered for "{event.title}"!')
    else:
        messages.info(request, 'Already registered.')
    return redirect('events:detail', pk=pk)