from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

from exercises.models import Exercise


class Workout(models.Model):
    """
    A single workout session. Owned by a user.
    Lifecycle: created (in-progress) -> finished.
    Finished workouts are immutable (history); in-progress can be edited freely.
    """

    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'Em curso'
        FINISHED = 'finished', 'Terminado'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workouts',
    )
    title = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Treino'
        verbose_name_plural = 'Treinos'
        ordering = ['-started_at']

    def __str__(self):
        title = self.title or f'Treino de {self.started_at.strftime("%Y-%m-%d")}'
        return f'{title} ({self.user.username})'

    def get_absolute_url(self):
        return reverse('workouts:detail', kwargs={'pk': self.pk})

    @property
    def is_in_progress(self):
        return self.status == self.Status.IN_PROGRESS

    @property
    def is_finished(self):
        return self.status == self.Status.FINISHED

    def has_logged_sets(self):
        """True if at least one completed set with reps>0 exists across all exercises."""
        from .models import Set  # local import to avoid forward-reference issues
        return Set.objects.filter(
            workout_exercise__workout=self,
            completed=True,
            reps__gt=0,
        ).exists()

    def cleanup_empty_data(self):
        """
        Remove sets with reps=0 and WorkoutExercises that end up with zero sets.
        Called as part of finish() to keep history clean.
        """
        from .models import Set  # local import
        Set.objects.filter(
            workout_exercise__workout=self,
            reps=0,
        ).delete()
        self.workout_exercises.filter(sets__isnull=True).delete()

    def finish(self):
        """
        Mark workout as finished. Cleans up empty sets/exercises first.
        Raises ValueError if there's nothing meaningful to record.
        Idempotent (calling on a finished workout is a no-op).
        """
        if self.is_finished:
            return

        self.cleanup_empty_data()

        if not self.has_logged_sets():
            raise ValueError(
                "Não é possível terminar um treino sem sets registados. "
                "Adiciona pelo menos um set com repetições > 0."
            )

        self.status = self.Status.FINISHED
        self.finished_at = timezone.now()
        self.save(update_fields=['status', 'finished_at'])


class WorkoutExercise(models.Model):
    """
    An exercise performed within a workout, with ordering and optional notes.
    Acts as a join table between Workout and Exercise, plus parent of Sets.
    """
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='workout_exercises',
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT,  # don't allow deleting exercises that are referenced by workouts
        related_name='workout_entries',
    )
    order = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Exercício do treino'
        verbose_name_plural = 'Exercícios dos treinos'
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['workout', 'exercise', 'order'],
                name='unique_workoutexercise_per_workout_order',
            ),
        ]

    def __str__(self):
        return f'{self.exercise.name} in {self.workout}'


class Set(models.Model):
    """
    A single set: reps × weight at a given order within a WorkoutExercise.
    Weight is stored in kg with 2 decimal places (precise enough for plate-level granularity).
    """
    workout_exercise = models.ForeignKey(
        WorkoutExercise,
        on_delete=models.CASCADE,
        related_name='sets',
    )
    order = models.PositiveIntegerField(default=0)
    reps = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    is_warmup = models.BooleanField(default=False)
    completed = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Set'
        verbose_name_plural = 'Sets'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.reps} × {self.weight_kg}kg'