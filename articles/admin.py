from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content')
    ordering = ('-created_at',)