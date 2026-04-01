from django.contrib import admin
from .models import Post, Like, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display  = ['author', 'content_preview', 'visibility', 'like_count', 'comment_count', 'created_at']
    list_filter   = ['visibility', 'created_at']
    search_fields = ['author__email', 'content']

    def content_preview(self, obj):
        return obj.content[:60]
    content_preview.short_description = 'Content'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ['author', 'post', 'content', 'created_at']
    search_fields = ['author__email', 'content']