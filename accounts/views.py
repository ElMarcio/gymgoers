from django.contrib.auth import login
from .forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView


class SignUpView(CreateView):
    """
    User registration.
    Uses Django's built-in UserCreationForm, which handles password hashing,
    validation, and confirmation.
    On success, logs the user in automatically and redirects to homepage.
    """
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('pages:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        # self.object is the newly created User (set by CreateView)
        login(self.request, self.object)
        return response