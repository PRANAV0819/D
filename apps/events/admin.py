from django.contrib import admin
from .models import Event, EventRegistration

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'starts_at', 'is_online', 'registration_count']
    list_filter  = ['event_type', 'is_online']