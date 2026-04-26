from django.contrib import admin

from .models import Set, Workout, WorkoutExercise


class SetInline(admin.TabularInline):
    model = Set
    extra = 0
    fields = ('order', 'reps', 'weight_kg', 'is_warmup', 'completed')


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 0
    fields = ('order', 'exercise', 'notes')


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'status', 'started_at', 'finished_at')
    list_filter = ('status', 'started_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('started_at',)
    inlines = [WorkoutExerciseInline]


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ('workout_exercise', 'order', 'reps', 'weight_kg', 'is_warmup', 'completed')
    list_filter = ('is_warmup', 'completed')