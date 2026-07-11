from django.shortcuts import get_object_or_404, redirect, render

from .models import Post


def home(request):
    # Template-driven homepage (latest posts previews are static/placeholder),
    # but you can switch to dynamic content later.
    return render(request, "blog/home.html")


def post_list(request):
    posts = Post.objects.all().order_by("-created_date")
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request, pk: int):
    post = get_object_or_404(Post, pk=pk)
    return render(request, "blog/post_detail.html", {"post": post})
