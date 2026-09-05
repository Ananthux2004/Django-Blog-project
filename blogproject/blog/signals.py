from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from rest_framework.authtoken.models import Token

from .models import Notification, Post

User = get_user_model()


def clear_homepage_cache():
    """Helper function to invalidate all home page related cache keys."""
    # Delete fixed section keys
    cache.delete("home_top_viewed")
    cache.delete("home_sidebar_tags")

    # Clear initial pages for main feed tabs
    feed_keys = [
        "home_feed_for_you_page_1",
        "home_feed_featured_page_1",
    ]
    cache.delete_many(feed_keys)

    # Note: If using Redis or wanting a complete reset on post updates,
    # cache.clear() can also be called here.
    print(
        "[SIGNAL TRIGGERED] Invalidated home page cache keys (hero, sidebar, and initial feed pages).",
        flush=True,
    )


# ------------------------------------------------------------------
# 1. PRE-SAVE SIGNALS (Cache previous state before model saves)
# ------------------------------------------------------------------
@receiver(pre_save, sender=Post)
def cache_previous_post_state(sender, instance, **kwargs):
    """Tracks if the post was already featured or published before saving."""
    if instance.pk:
        try:
            old_post = Post.objects.get(pk=instance.pk)
            instance._was_featured = old_post.is_featured
            instance._was_published = old_post.status in ["published", "P"]
        except Post.DoesNotExist:
            instance._was_featured = False
            instance._was_published = False
    else:
        instance._was_featured = False
        instance._was_published = False


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def cache_previous_user_state(sender, instance, **kwargs):
    """Tracks email and password changes before user model saves."""
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            instance._old_email = old_user.email
            instance._old_password = old_user.password
        except User.DoesNotExist:
            instance._old_email = ""
            instance._old_password = ""


# ------------------------------------------------------------------
# 2. POST-SAVE SIGNALS (Post Created / Updated)
# ------------------------------------------------------------------
@receiver(post_save, sender=Post)
def handle_post_save(sender, instance, created, **kwargs):
    # A. Invalidate home page cache whenever a post is created or updated
    clear_homepage_cache()

    was_featured = getattr(instance, "_was_featured", False)
    was_published = getattr(instance, "_was_published", False)
    is_now_published = instance.status in ["published", "P"]

    author_user = (
        instance.author.user
        if hasattr(instance.author, "user")
        else instance.author
    )

    # B. Trigger In-App Notification: Admin marked post as featured
    if instance.is_featured and not was_featured:
        Notification.objects.create(
            recipient=author_user,
            verb=f"Your post '{instance.title}' is a featured post of DevBlog",
            target_url=reverse(
                "blog:post_detail", kwargs={"slug": instance.slug}
            ),
            notification_type=Notification.Type.POST_FEATURED,
        )
        print(
            f"[SIGNAL TRIGGERED] Featured notification sent to author.",
            flush=True,
        )

    # C. Trigger In-App Notifications + Email Alert: Newly Published Article
    if is_now_published and not was_published:
        active_recipients = User.objects.filter(is_active=True).exclude(
            pk=author_user.pk
        )

        # 1. Create In-App Notifications
        in_app_notifications = [
            Notification(
                recipient=user,
                actor=author_user,
                verb=f"{author_user.username} published a new article: '{instance.title}'",
                target_url=reverse(
                    "blog:post_detail", kwargs={"slug": instance.slug}
                ),
                notification_type=Notification.Type.POST_PUBLISHED,
            )
            for user in active_recipients
        ]
        if in_app_notifications:
            Notification.objects.bulk_create(in_app_notifications)
            print(
                f"[SIGNAL TRIGGERED] Created in-app notifications for {len(in_app_notifications)} user(s).",
                flush=True,
            )

        # 2. Send Email Notification
        email_list = list(
            active_recipients.exclude(email="").values_list("email", flat=True)
        )
        if email_list:
            subject = f"New Post Alert: {instance.title}"
            message = (
                f"A new post titled '{instance.title}' has just been published on DevBlog by {author_user.username}!\n\n"
                f"Check it out now on the website!"
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(
                    settings, "DEFAULT_FROM_EMAIL", "noreply@devblog.com"
                ),
                recipient_list=email_list,
                fail_silently=True,
            )
            print(
                f"[SIGNAL TRIGGERED] Email notification sent to {len(email_list)} user(s).",
                flush=True,
            )


# ------------------------------------------------------------------
# 3. POST-DELETE SIGNAL (Post Deleted)
# ------------------------------------------------------------------
@receiver(post_delete, sender=Post)
def handle_post_delete(sender, instance, **kwargs):
    # Invalidate cache when a post is removed
    clear_homepage_cache()


# ------------------------------------------------------------------
# 4. USER SIGNALS (Token Generation & Security Alerts)
# ------------------------------------------------------------------
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def handle_user_save(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)
        print(
            f"[SIGNAL TRIGGERED] Auth Token created for user: {instance.username}",
            flush=True,
        )
    else:
        old_email = getattr(instance, "_old_email", None)
        old_password = getattr(instance, "_old_password", None)

        if old_email and old_email != instance.email:
            Notification.objects.create(
                recipient=instance,
                verb="🔒 Your account email address was recently updated.",
                notification_type=Notification.Type.SECURITY,
            )
            print(
                f"[SIGNAL TRIGGERED] Security notification sent (Email Changed) to {instance.username}",
                flush=True,
            )
        elif old_password and old_password != instance.password:
            Notification.objects.create(
                recipient=instance,
                verb="🔒 Your account password was successfully changed.",
                notification_type=Notification.Type.SECURITY,
            )
            print(
                f"[SIGNAL TRIGGERED] Security notification sent (Password Changed) to {instance.username}",
                flush=True,
            )