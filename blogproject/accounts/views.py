from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import (
    DeleteAccountForm,
    EmailChangeForm,
    RegistrationForm,
    StyledPasswordChangeForm,
)

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


# ---- Account Settings View (Phase 2.6.5 & Phase 2.6.6) ----
class AccountSettingsView(LoginRequiredMixin, View):
    """
    Handles Password Change, Email Change, Notification, Privacy, and Account Deletion.
    """
    template_name = "accounts/settings.html"

    def get(self, request, *args, **kwargs):
        email_form = EmailChangeForm(instance=request.user)
        password_form = StyledPasswordChangeForm(user=request.user)
        delete_form = DeleteAccountForm(user=request.user)
        return render(
            request,
            self.template_name,
            {
                "email_form": email_form,
                "password_form": password_form,
                "delete_form": delete_form,
                "active_tab": request.GET.get("tab", "password"),
            },
        )

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        email_form = EmailChangeForm(instance=request.user)
        password_form = StyledPasswordChangeForm(user=request.user)
        delete_form = DeleteAccountForm(user=request.user)
        active_tab = "password"

        if action == "change_password":
            active_tab = "password"
            password_form = StyledPasswordChangeForm(
                user=request.user, data=request.POST
            )
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Prevents logout after password change
                messages.success(request, "Your password was successfully updated!")
                return redirect("accounts:settings")
            else:
                messages.error(request, "Please correct the error(s) in the password form.")

        elif action == "change_email":
            active_tab = "email"
            email_form = EmailChangeForm(request.POST, instance=request.user)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, "Your email address was updated successfully!")
                return redirect("accounts:settings")
            else:
                messages.error(request, "Please correct the error(s) in the email form.")

        elif action == "delete_account":
            active_tab = "delete"

            # Protection for staff/superuser accounts
            if request.user.is_staff or request.user.is_superuser:
                messages.error(
                    request, "Staff and Administrator accounts cannot be deleted through settings."
                )
                return redirect("accounts:settings")

            delete_form = DeleteAccountForm(user=request.user, data=request.POST)
            if delete_form.is_valid():
                user = request.user
                logout(request)
                user.delete()  # Permanently deletes User and associated Author profile
                messages.success(request, "Your account has been permanently deleted.")
                return redirect("blog:home")
            else:
                messages.error(
                    request, "Account deletion failed. Please check your password and try again."
                )

        elif action == "update_notifications":
            active_tab = "notifications"
            messages.info(request, "Notification preferences saved (Placeholder).")
            return redirect("accounts:settings")

        elif action == "update_privacy":
            active_tab = "privacy"
            messages.info(request, "Privacy settings saved (Placeholder).")
            return redirect("accounts:settings")

        return render(
            request,
            self.template_name,
            {
                "email_form": email_form,
                "password_form": password_form,
                "delete_form": delete_form,
                "active_tab": active_tab,
            },
        )


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