from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_profile(sender, instance, created, **kwargs):
    """
    Ensure every User has exactly one Profile.
    Created automatically on User creation; idempotent thereafter.
    """
    if created:
        Profile.objects.create(user=instance)