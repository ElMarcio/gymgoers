from django.urls import path

from .views import (
    SetCreateView,
    SetDeleteView,
    SetUpdateView,
    WorkoutAddExerciseView,
    WorkoutDeleteView,
    WorkoutDetailView,
    WorkoutFinishView,
    WorkoutListView,
    WorkoutStartView,
    WorkoutUpdateMetaView,
)

app_name = 'workouts'

urlpatterns = [
    path('', WorkoutListView.as_view(), name='list'),
    path('start/', WorkoutStartView.as_view(), name='start'),
    path('<int:pk>/', WorkoutDetailView.as_view(), name='detail'),
    path('<int:pk>/finish/', WorkoutFinishView.as_view(), name='finish'),
    path('<int:pk>/delete/', WorkoutDeleteView.as_view(), name='delete'),
    path('<int:pk>/update-meta/', WorkoutUpdateMetaView.as_view(), name='update_meta'),
    path('<int:pk>/add-exercise/', WorkoutAddExerciseView.as_view(), name='add_exercise'),
    path('exercises/<int:pk>/add-set/', SetCreateView.as_view(), name='set_create'),
    path('sets/<int:pk>/update/', SetUpdateView.as_view(), name='set_update'),
    path('sets/<int:pk>/delete/', SetDeleteView.as_view(), name='set_delete'),
]