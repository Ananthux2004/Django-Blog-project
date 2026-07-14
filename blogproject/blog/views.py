from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView
from django.views.generic import UpdateView

from .forms import PostForm
from .models import Post


def home(request):
    # Template-driven homepage (latest posts previews are static/placeholder),
    # but you can switch to dynamic content later.
    return render(request, "blog/home.html")


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"

    def get_queryset(self):
        qs = Post.objects.select_related("author", "category").prefetch_related(
            "tags"
        )
        if self.request.user.is_staff:
            return qs.order_by("-created_date")
        return qs.published().order_by("-created_date")


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        # Only allow unpublished posts for staff
        obj = get_object_or_404(
            queryset, slug=self.kwargs.get(self.slug_url_kwarg))
        if (not self.request.user.is_staff) and obj.status != Post.StatusChoices.PUBLISHED:
            raise Http404("Post not found.")
        return obj

    def get_queryset(self):
        qs = Post.objects.select_related("author", "category").prefetch_related(
            "tags"
        )
        if self.request.user.is_staff:
            return qs
        return qs.published()

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        Post.objects.filter(pk=self.object.pk).update(
            views=F("views") + 1
        )

        self.object.refresh_from_db()

        return response

class PostCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    success_message = "Post created successfully."
    slug_field = "slug"

    def form_valid(self, form):
        from .models import Author

        author, _ = Author.objects.get_or_create(user=self.request.user)
        form.instance.author = author

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"slug": self.object.slug})


class PostUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    success_message = "Post updated successfully."
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_staff or obj.author.user == self.request.user

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"slug": self.object.slug})


class PostDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView
):
    model = Post
    template_name = "blog/post_confirm_delete.html"
    success_message = "Post deleted successfully."
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_staff or obj.author.user == self.request.user

    def get_success_url(self):
        return reverse_lazy("blog:post_list")


# Backwards-compatible wrappers for old routes (pk-based)
class PostDetailPkView(PostDetailView):
    slug_field = "pk"
    slug_url_kwarg = "pk"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = Post.objects.select_related("author", "category").prefetch_related(
                "tags"
            )
        obj = get_object_or_404(queryset, pk=self.kwargs.get("pk"))
        if (not self.request.user.is_staff) and obj.status != Post.StatusChoices.PUBLISHED:
            raise Http404("Post not found.")
        return obj

    def get_queryset(self):
        qs = Post.objects.select_related(
            "author", "category").prefetch_related("tags")
        if self.request.user.is_staff:
            return qs
        return qs.published()
