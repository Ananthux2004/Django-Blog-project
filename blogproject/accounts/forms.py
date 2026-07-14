from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class RegistrationForm(UserCreationForm):
    """
    Registration form using Django's UserCreationForm as the base.

    Fields required by the task:
    - username
    - email
    - password
    - confirm password

    Validations:
    - unique username (handled by User model)
    - unique email (enforced here)
    - strong password (Django password validators)
    - password confirmation (handled by base UserCreationForm)
    """

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "A user with this email already exists.")
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        validate_password(password1)
        return password1
