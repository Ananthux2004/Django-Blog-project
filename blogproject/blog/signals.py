from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models import Post
from rest_framework.authtoken.models import Token

User = get_user_model()


@receiver(post_save, sender=Post)
def handle_post_save(sender, instance, created, **kwargs):
    # 1. Invalidate homepage cache whenever a post is created or updated
    cache.delete('homepage_latest_posts')
    print("[SIGNAL TRIGGERED] Invalidated 'homepage_latest_posts' cache key.")

    # 2. Email notification logic (triggers only if published)
    is_published = getattr(instance, 'status', 'published') == 'published'
    
    if created and is_published:
        recipient_list = list(
            User.objects.filter(is_active=True)
            .exclude(email='')
            .values_list('email', flat=True)
        )

        if recipient_list:
            subject = f"New Post Alert: {instance.title}"
            message = (
                f"A new post titled '{instance.title}' has just been published on DevBlog!\n\n"
                f"Check it out now on the website!"
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@devblog.com'),
                recipient_list=recipient_list,
                fail_silently=True,
            )
            print(f"[SIGNAL TRIGGERED] Email notification sent to {len(recipient_list)} user(s).")


@receiver(post_delete, sender=Post)
def handle_post_delete(sender, instance, **kwargs):
    # Invalidate cache when a post is removed
    cache.delete('homepage_latest_posts')
    print("[SIGNAL TRIGGERED] Invalidated 'homepage_latest_posts' cache key on deletion.")

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)