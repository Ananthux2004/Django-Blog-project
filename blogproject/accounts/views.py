from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import RegistrationForm

User = get_user_model()


def register(request):
    """
    Registration using RegistrationForm (UserCreationForm-based).

    Development mode behavior:
    - Create the user as ACTIVE immediately (is_active=True)
    - Create associated Author profile so existing blog models work
    - Log the user in immediately after registration
    """
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()

            # Ensure Author profile exists so blog Post FK isn't broken.
            from blog.models import Author

            Author.objects.get_or_create(user=user)

            login(request, user)
            messages.success(request, "Registration successful. You are now logged in.")
            return redirect("blog:home")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


# ---- Built-in auth views (login/logout/password change/reset) ----
class AuthLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    extra_context = {"title": "Login"}

    def get_success_url(self):
        """
        Redirect to the original requested page if one exists.
        Otherwise:
        - Staff users -> Django admin
        - Normal users -> Blog home
        """

        next_url = self.get_redirect_url()
        if next_url:
            return next_url

        if self.request.user.is_staff:
            return reverse_lazy("admin:index")

        return reverse_lazy("blog:home")
class AuthLogoutView(LogoutView):
    next_page = reverse_lazy("blog:home")


class AuthPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change_form.html"
    success_url = reverse_lazy("blog:home")


class AuthPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")

    def form_valid(self, form):
        print("Password reset requested for:", form.cleaned_data["email"])
        response = super().form_valid(form)
        print("PasswordResetView completed.")
        return response


from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.tokens import default_token_generator

class AuthPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    def dispatch(self, request, *args, **kwargs):
        print("uidb64:", kwargs.get("uidb64"))
        print("token:", kwargs.get("token"))

        response = super().dispatch(request, *args, **kwargs)

        print("validlink:", getattr(self, "validlink", None))
        print("user:", getattr(self, "user", None))

        if getattr(self, "user", None):
            print(
                "manual check:",
                default_token_generator.check_token(
                    self.user, kwargs.get("token")
                ),
            )

        return response


def password_reset_done(request):
    return render(request, "accounts/password_reset_done.html")


def password_reset_complete(request):
    return render(request, "accounts/password_reset_complete.html")
