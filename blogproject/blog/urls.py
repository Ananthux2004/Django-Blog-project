from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.home, name="home"),

    # New slug-based routes
    path("posts/", views.PostListView.as_view(), name="post_list"),
    path(
        "post/create/",
        views.PostCreateView.as_view(),
        name="post_create",
    ),
    path(
        "post/<slug:slug>/",
        views.PostDetailView.as_view(),
        name="post_detail",
    ),
    path(
        "post/<slug:slug>/edit/",
        views.PostUpdateView.as_view(),
        name="post_update",
    ),
    path(
        "post/<slug:slug>/delete/",
        views.PostDeleteView.as_view(),
        name="post_delete",
    ),

    # Backwards-compatible (keep existing working routes)
    path(
        "post/<int:pk>/",
        views.PostDetailPkView.as_view(),
        name="post_detail_old_pk",
    ),
]
