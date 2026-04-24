from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Currently identical to AbstractUser but exists so we can add fields
    later without painful migrations.
    """

    class Meta:
        verbose_name = 'Utilizador'
        verbose_name_plural = 'Utilizadores'

    def __str__(self):
        return self.username


class Profile(models.Model):
    """
    Extended profile data for a user.
    OneToOneField means every User has exactly one Profile.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    bio = models.TextField(blank=True, max_length=500)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'Profile of {self.user.username}'