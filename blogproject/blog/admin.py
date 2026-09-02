from django.contrib import admin, messages
from django.utils import timezone
from django.utils.translation import ngettext

from .models import Author, Category, Comment, Post, Tag


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("username", "website", "location",
                    "joined_date", "updated_at")
    search_fields = (
        "user__username",
        "location",
        "website",
        "github",
        "linkedin",
        "twitter",
    )
    list_filter = ("joined_date", "location")
    readonly_fields = ("joined_date", "updated_at")
    list_per_page = 20
    fieldsets = (
        ("Account", {"fields": ("user",)}),
        (
            "Profile",
            {
                "fields": (
                    "profile_picture",
                    "bio",
                    "location",
                    "website",
                )
            },
        ),
        (
            "Social Links",
            {
                "fields": (
                    "github",
                    "linkedin",
                    "twitter",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "joined_date",
                    "updated_at",
                )
            },
        ),
    )

    def username(self, obj):
        return obj.user.username

    
    username.short_description = "Username"
    username.admin_order_field = "user__username"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = ("name",)

    readonly_fields = (
        "created_at",
    )

    list_per_page = 20

    prepopulated_fields = {
        "slug": ("name",)
    }

    fieldsets = (
        (
            "Category Information",
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "image",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "slug",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )

    list_per_page = 20

    prepopulated_fields = {
        "slug": ("name",)
    }

    fieldsets = (
        (
            "Tag Information",
            {
                "fields": (
                    "name",
                    "slug",
                )
            },
        ),
    )

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "status",
        "is_featured",
        "views",
        "created_date",
        "published_date",
    )
    # Allows fast inline toggling of featured status directly from the list table
    list_editable = ("is_featured",)

    list_select_related = (
        "author",
        "category",
    )

    list_per_page = 20
    save_on_top = True

    search_fields = (
        "title",
        "excerpt",
        "content",
        "author__user__username",
        "category__name",
    )
    list_filter = (
        "status",
        "category",
        "is_featured",
        "created_date",
        "published_date",
    )
    autocomplete_fields = ("author", "category")
    filter_horizontal = ("tags",)
    readonly_fields = (
        "views",
        "reading_time",  # Added if reading_time is auto-calculated
        "created_date",
        "updated_date",
        "published_date",
    )
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_date"
    ordering = ("-created_date",)

    fieldsets = (
        (
            "Content",
            {
                "fields": (
                    "title",
                    "slug",
                    "excerpt",
                    "content",
                    "featured_image",
                )
            },
        ),
        (
            "Classification",
            {
                "fields": (
                    "author",
                    "category",
                    "tags",
                    "status",
                    "is_featured",
                )
            },
        ),
        (
            "Publication",
            {
                "fields": (
                    "created_date",
                    "updated_date",
                    "published_date",
                )
            },
        ),
        (
            "Metrics",
            {
                "fields": ("views", "reading_time"),
            },
        ),
    )

    actions = [
        "publish_selected_posts",
        "unpublish_selected_posts",
        "mark_featured_selected_posts",
        "unmark_featured_selected_posts",
    ]

    @admin.action(description="Publish selected posts")
    def publish_selected_posts(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(
            status=Post.StatusChoices.PUBLISHED,
            published_date=now,
            updated_date=now,
        )
        self.message_user(
            request,
            ngettext(
                "%d post was successfully published.",
                "%d posts were successfully published.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    @admin.action(description="Unpublish selected posts")
    def unpublish_selected_posts(self, request, queryset):
        updated = queryset.update(
            status=Post.StatusChoices.DRAFT,
            published_date=None,
            updated_date=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "%d post was successfully unpublished.",
                "%d posts were successfully unpublished.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    @admin.action(description="Mark selected posts as featured")
    def mark_featured_selected_posts(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            ngettext(
                "%d post was marked as featured.",
                "%d posts were marked as featured.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    @admin.action(description="Unmark selected posts as featured")
    def unmark_featured_selected_posts(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(
            request,
            ngettext(
                "%d post was removed from featured.",
                "%d posts were removed from featured.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "post",
        "name",
        "user",
        "is_approved",
        "is_active",
        "created_date",
    )
    search_fields = ("post__title", "name", "email", "content")
    list_filter = ("is_approved", "is_active", "created_date")
    readonly_fields = ("created_date", "updated_at")
    list_select_related = (
        "post",
        "user",
    )   

    list_per_page = 20
    fieldsets = (
        (
            "Comment",
            {
                "fields": (
                    "post",
                    "name",
                    "email",
                    "user",
                    "content",
                    "parent",
                )
            },
        ),
        (
            "Moderation",
            {
                "fields": (
                    "is_approved",
                    "is_active",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_date", "updated_at")}),
    )

    actions = [
        "approve_selected_comments",
        "disapprove_selected_comments",
    ]

    @admin.action(description="Approve selected comments")
    def approve_selected_comments(self, request, queryset):
        updated = queryset.update(is_approved=True, is_active=True)
        self.message_user(
        request,
        ngettext(
            "%d comment was approved.",
            "%d comments were approved.",
            updated,
        )
        % updated,
        messages.SUCCESS,
    )

    @admin.action(description="Disapprove selected comments")
    def disapprove_selected_comments(self, request, queryset):
        updated = queryset.update(is_approved=False, is_active=False)
        self.message_user(
        request,
        ngettext(
            "%d comment was disapproved.",
            "%d comments were disapproved.",
            updated,
        )
        % updated,
        messages.SUCCESS,
    )


admin.site.site_header = "DevBlog Administration"
admin.site.site_title = "DevBlog Admin"
admin.site.index_title = "Welcome to DevBlog Dashboard"
