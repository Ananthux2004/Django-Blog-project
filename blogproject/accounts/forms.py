from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
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


class EmailChangeForm(forms.ModelForm):
    """
    Form for changing email address in Account Settings.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new email address'
        })
    )

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "A user with this email address already exists.")
        return email


class StyledPasswordChangeForm(PasswordChangeForm):
    """
    Custom PasswordChangeForm with Bootstrap 5 'form-control' styling.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
            
class DeleteAccountForm(forms.Form):
    """
    Form to verify user's password before permanently deleting account.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password to confirm'
        }),
        label="Confirm Password"
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password. Please try again.")
        return password