from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


# Creates an Author profile automatically for all new users (including Google sign-ups)
@receiver(post_save, sender=User)
def create_author_profile(sender, instance, created, **kwargs):
    if created:
        from blog.models import Author

        Author.objects.get_or_create(user=instance)