"""
apps/lost_found/admin.py

Register Lost & Found models in Django admin for easy management.
"""

from django.contrib import admin
from .models import Item, ClaimRequest


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["title", "item_type", "category", "location", "date", "status", "user", "created_at"]
    list_filter = ["item_type", "category", "status"]
    search_fields = ["title", "description", "location", "user__email"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25


@admin.register(ClaimRequest)
class ClaimRequestAdmin(admin.ModelAdmin):
    list_display = ["item", "claimant", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["item__title", "claimant__email"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
