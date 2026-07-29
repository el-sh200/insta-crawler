from django.contrib import admin

# Register your models here.
from posts.models import Page, Post


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    pass


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_filter = ('page', )

    list_display = ('short_code', 'page', )
