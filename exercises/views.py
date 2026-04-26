from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import Exercise, MuscleGroup


class ExerciseListView(ListView):
    """Public catalogue with optional search and muscle group filter."""
    model = Exercise
    template_name = 'exercises/exercise_list.html'
    context_object_name = 'exercises'
    paginate_by = 24

    def get_queryset(self):
        qs = Exercise.objects.all()

        query = self.request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        muscle_group = self.request.GET.get('muscle_group', '').strip()
        if muscle_group:
            qs = qs.filter(muscle_group=muscle_group)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '')
        ctx['selected_muscle_group'] = self.request.GET.get('muscle_group', '')
        ctx['muscle_groups'] = MuscleGroup.choices
        return ctx

    def get_template_names(self):
        # HTMX requests get just the results fragment, not the full page.
        if self.request.headers.get('HX-Request'):
            return ['exercises/_exercise_list_fragment.html']
        return [self.template_name]


class ExerciseDetailView(DetailView):
    """Single exercise page."""
    model = Exercise
    template_name = 'exercises/exercise_detail.html'
    context_object_name = 'exercise'