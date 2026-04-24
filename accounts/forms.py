from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm

from .models import User


class UserCreationForm(DjangoUserCreationForm):
    """
    Custom signup form bound to our custom User model.
    Inherits all password validation and hashing logic from Django.
    """

    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = ('username',)