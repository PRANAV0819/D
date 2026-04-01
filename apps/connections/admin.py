from django.contrib import admin
from .models import Connection


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display  = ['sender', 'receiver', 'status', 'created_at']
    list_filter   = ['status']
    search_fields = ['sender__email', 'receiver__email']