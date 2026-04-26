from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, View

from exercises.models import Exercise
from .forms import SetUpdateForm
from .models import Set, Workout, WorkoutExercise


class WorkoutListView(LoginRequiredMixin, ListView):
    """List the current user's workouts, most recent first."""
    model = Workout
    template_name = 'workouts/workout_list.html'
    context_object_name = 'workouts'
    paginate_by = 20

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user)


class WorkoutDetailView(LoginRequiredMixin, DetailView):
    """View a single workout. User can only access their own."""
    model = Workout
    template_name = 'workouts/workout_detail.html'
    context_object_name = 'workout'

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user)


class WorkoutStartView(LoginRequiredMixin, View):
    """
    POST-only endpoint that creates a new in-progress workout
    and redirects to its detail page.
    """
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        workout = Workout.objects.create(user=request.user)
        return HttpResponseRedirect(reverse('workouts:detail', kwargs={'pk': workout.pk}))


class WorkoutAddExerciseView(LoginRequiredMixin, View):
    """
    Show a list of exercises to add to a workout (GET) or add the
    selected one with 3 empty sets (POST).
    Only the workout owner can add exercises, and only while in progress.
    """

    def get_workout(self):
        return get_object_or_404(
            Workout,
            pk=self.kwargs['pk'],
            user=self.request.user,
        )

    def get(self, request, *args, **kwargs):
        workout = self.get_workout()
        if not workout.is_in_progress:
            return HttpResponseForbidden('Workout is finished.')

        query = request.GET.get('q', '').strip()
        exercises = Exercise.objects.all()
        if query:
            exercises = exercises.filter(name__icontains=query)

        from django.shortcuts import render
        return render(request, 'workouts/add_exercise.html', {
            'workout': workout,
            'exercises': exercises[:30],  # cap to avoid huge list
            'query': query,
        })

    def post(self, request, *args, **kwargs):
        workout = self.get_workout()
        if not workout.is_in_progress:
            return HttpResponseForbidden('Workout is finished.')

        exercise_id = request.POST.get('exercise_id')
        exercise = get_object_or_404(Exercise, pk=exercise_id)

        # Determine the next order number for this workout's exercises.
        next_order = (workout.workout_exercises.count() or 0) + 1

        we = WorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            order=next_order,
        )

        # Pre-create 3 empty sets (decision logged in DECISIONS.md ADR-004 note).
        for i in range(1, 4):
            Set.objects.create(
                workout_exercise=we,
                order=i,
                reps=0,
                weight_kg=0,
                completed=False,
            )

        return redirect('workouts:detail', pk=workout.pk)

    class SetUpdateView(LoginRequiredMixin, View):
        """
        HTMX endpoint: update a single Set's fields.
        Returns the updated set row fragment.
        """
        http_method_names = ['post']

        def post(self, request, *args, **kwargs):
            # Load set with full context, ensuring ownership.
            set_obj = get_object_or_404(
                Set.objects.select_related('workout_exercise__workout'),
                pk=self.kwargs['pk'],
                workout_exercise__workout__user=request.user,
            )

            if not set_obj.workout_exercise.workout.is_in_progress:
                return HttpResponseForbidden('Workout is finished.')

            form = SetUpdateForm(request.POST, instance=set_obj)
            if form.is_valid():
                form.save()
            # If invalid, we still return the fragment with current values —
            # HTMX will swap and the bad input is gone (silent revert is fine for MVP).

            from django.shortcuts import render
            return render(request, 'workouts/_set_row.html', {
                'set': set_obj,
                'we': set_obj.workout_exercise,
                'workout': set_obj.workout_exercise.workout,
            })
class SetUpdateView(LoginRequiredMixin, View):
    """
    HTMX endpoint: update a single Set's fields.
    Returns the updated set row fragment.
    """
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        # Load set with full context, ensuring ownership.
        set_obj = get_object_or_404(
            Set.objects.select_related('workout_exercise__workout'),
            pk=self.kwargs['pk'],
            workout_exercise__workout__user=request.user,
        )

        if not set_obj.workout_exercise.workout.is_in_progress:
            return HttpResponseForbidden('Workout is finished.')

        form = SetUpdateForm(request.POST, instance=set_obj)
        if form.is_valid():
            form.save()
        # If invalid, we still return the fragment with current values —
        # HTMX will swap and the bad input is gone (silent revert is fine for MVP).

        from django.shortcuts import render
        return render(request, 'workouts/_set_row.html', {
            'set': set_obj,
            'we': set_obj.workout_exercise,
            'workout': set_obj.workout_exercise.workout,
        })

class SetCreateView(LoginRequiredMixin, View):
    """HTMX endpoint: add a new empty set to a WorkoutExercise."""
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        we = get_object_or_404(
            WorkoutExercise.objects.select_related('workout'),
            pk=self.kwargs['pk'],
            workout__user=request.user,
        )

        if not we.workout.is_in_progress:
            return HttpResponseForbidden('Workout is finished.')

        next_order = (we.sets.count() or 0) + 1
        Set.objects.create(
            workout_exercise=we,
            order=next_order,
            reps=0,
            weight_kg=0,
            completed=False,
        )

        # Re-render the entire WorkoutExercise block so the new row appears.
        from django.shortcuts import render
        return render(request, 'workouts/_workout_exercise_block.html', {
            'we': we,
            'workout': we.workout,
        })


class SetDeleteView(LoginRequiredMixin, View):
    """HTMX endpoint: delete a Set."""
    http_method_names = ['post', 'delete']

    def post(self, request, *args, **kwargs):
        return self._handle(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self._handle(request, *args, **kwargs)

    def _handle(self, request, *args, **kwargs):
        set_obj = get_object_or_404(
            Set.objects.select_related('workout_exercise__workout'),
            pk=self.kwargs['pk'],
            workout_exercise__workout__user=request.user,
        )

        if not set_obj.workout_exercise.workout.is_in_progress:
            return HttpResponseForbidden('Workout is finished.')

        we = set_obj.workout_exercise
        set_obj.delete()

        # Re-order remaining sets so they're contiguous (1, 2, 3, ...).
        for index, s in enumerate(we.sets.all().order_by('order'), start=1):
            if s.order != index:
                s.order = index
                s.save(update_fields=['order'])

        from django.shortcuts import render
        return render(request, 'workouts/_workout_exercise_block.html', {
            'we': we,
            'workout': we.workout,
        })
class WorkoutFinishView(LoginRequiredMixin, View):
    """Mark a workout as finished. Cleans up empty data first."""
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        workout = get_object_or_404(
            Workout,
            pk=self.kwargs['pk'],
            user=request.user,
        )
        try:
            workout.finish()
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('workouts:detail', pk=workout.pk)


class WorkoutDeleteView(LoginRequiredMixin, View):
    """Delete a workout entirely (cascade deletes WorkoutExercises and Sets)."""
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        workout = get_object_or_404(
            Workout,
            pk=self.kwargs['pk'],
            user=request.user,
        )
        workout.delete()
        return redirect('workouts:list')


class WorkoutUpdateMetaView(LoginRequiredMixin, View):
    """
    HTMX endpoint to inline-update workout title or notes.
    Only works while in progress.
    """
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        workout = get_object_or_404(
            Workout,
            pk=self.kwargs['pk'],
            user=request.user,
        )
        if not workout.is_in_progress:
            return HttpResponseForbidden('Workout is finished.')

        # Only allow updating these specific fields.
        if 'title' in request.POST:
            workout.title = request.POST['title'][:100]
        if 'notes' in request.POST:
            workout.notes = request.POST['notes']
        workout.save(update_fields=['title', 'notes'])

        from django.shortcuts import render
        return render(request, 'workouts/_workout_meta.html', {'workout': workout})