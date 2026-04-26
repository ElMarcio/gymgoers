from django.urls import path

from .views import WorkoutDetailView, WorkoutListView, WorkoutStartView

app_name = 'workouts'

urlpatterns = [
    path('', WorkoutListView.as_view(), name='list'),
    path('start/', WorkoutStartView.as_view(), name='start'),
    path('<int:pk>/', WorkoutDetailView.as_view(), name='detail'),
]