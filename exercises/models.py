from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

class MuscleGroup(models.TextChoices):
    """Primary muscle groups targeted by exercises."""
    CHEST = 'chest', 'Peito'
    BACK = 'back', 'Costas'
    LEGS = 'legs', 'Pernas'
    SHOULDERS = 'shoulders', 'Ombros'
    ARMS = 'arms', 'Braços'
    CORE = 'core', 'Core'
    FULL_BODY = 'full_body', 'Corpo inteiro'


class Equipment(models.TextChoices):
    """Equipment required to perform an exercise."""
    BARBELL = 'barbell', 'Barra'
    DUMBBELL = 'dumbbell', 'Halteres'
    MACHINE = 'machine', 'Máquina'
    CABLE = 'cable', 'Cabo'
    BODYWEIGHT = 'bodyweight', 'Peso corporal'
    KETTLEBELL = 'kettlebell', 'Kettlebell'
    OTHER = 'other', 'Outro'


class Exercise(models.Model):
    """
    A single exercise in the catalogue (e.g. "Bench Press", "Squat").
    Curated/seeded data — users don't create exercises in MVP, only select from this list.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    muscle_group = models.CharField(
        max_length=20,
        choices=MuscleGroup.choices,
    )
    equipment = models.CharField(
        max_length=20,
        choices=Equipment.choices,
        default=Equipment.OTHER,
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Exercício'
        verbose_name_plural = 'Exercícios'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('exercises:detail', kwargs={'slug': self.slug})