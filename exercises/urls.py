from django.urls import path

from .views import ExerciseDetailView, ExerciseListView

app_name = 'exercises'

urlpatterns = [
    path('', ExerciseListView.as_view(), name='list'),
    path('<slug:slug>/', ExerciseDetailView.as_view(), name='detail'),
]