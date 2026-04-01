from django.contrib import admin
from .models import ChatRoom, RoomMember, Message


class RoomMemberInline(admin.TabularInline):
    model = RoomMember
    extra = 0


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display  = ['pk', 'room_type', 'name', 'created_by', 'created_at']
    list_filter   = ['room_type']
    inlines       = [RoomMemberInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ['sender', 'room', 'content_preview', 'is_seen', 'created_at']
    list_filter   = ['is_seen', 'created_at']
    search_fields = ['sender__email', 'content']

    def content_preview(self, obj):
        return obj.content[:60]
    content_preview.short_description = 'Content'