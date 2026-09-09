from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class EmailOrUsernameLoginForm(AuthenticationForm):
    """
    Login form allowing users to sign in with either Username or Email.
    Provides clear validation errors when authentication fails.
    """

    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username or Email",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        ),
    )

    error_messages = {
        "invalid_login": (
            "Invalid credentials. Please check your username/email and password."
        ),
        "inactive": "This account is currently inactive.",
    }


class RegistrationForm(UserCreationForm):
    """
    Registration form using Django's UserCreationForm as the base.
    Requires unique email and validates strong passwords.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Email address"}
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email")  # Do NOT include password fields here

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap 'form-control' styling to all form fields
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "A user with this email address already exists."
            )
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            validate_password(password1, user=self.instance)
        return password1


class EmailChangeForm(forms.ModelForm):
    """
    Form for changing email address in Account Settings.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter new email address",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if (
            User.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                "A user with this email address already exists."
            )
        return email


class StyledPasswordChangeForm(PasswordChangeForm):
    """
    Custom PasswordChangeForm with Bootstrap 5 'form-control' styling.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class DeleteAccountForm(forms.Form):
    """
    Form to verify user's password before permanently deleting account.
    """

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your password to confirm",
            }
        ),
        label="Confirm Password",
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not self.user.check_password(password):
            raise forms.ValidationError(
                "Incorrect password. Please try again."
            )
        return password