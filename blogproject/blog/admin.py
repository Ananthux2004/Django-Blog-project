from django.contrib import admin

from .models import Author, Post, Comment


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("user", "joined_date")
    search_fields = ("user__username",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status",
                    "created_date", "published_date")
    list_filter = ("status", "created_date")
    search_fields = ("title", "content", "author__user__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "post", "is_approved", "created_date")
    list_filter = ("is_approved", "created_date")
    search_fields = ("name", "email", "post__title")
