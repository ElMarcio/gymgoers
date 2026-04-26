from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, View

from .models import Workout


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