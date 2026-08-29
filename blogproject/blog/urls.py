from django.urls import path
from django.views.generic import RedirectView
from .views import AuthorProfileEditView
from rest_framework.authtoken.views import obtain_auth_token
from . import views,api_views

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

    # ==========================================
    # --- NEW COMMENT ROUTES START HERE ---
    # ==========================================
    path(
        "post/<slug:slug>/comment/",
        views.add_comment,
        name="add_comment",
    ),
    path(
        "post/<slug:slug>/reply/<int:pk>/",
        views.reply_comment,
        name="reply_comment",
    ),
    path(
        "comment/<int:pk>/edit/",
        views.edit_comment,
        name="edit_comment",
    ),
    path(
        "comment/<int:pk>/delete/",
        views.delete_comment,
        name="delete_comment",
    ),
    path('search/', views.SearchResultsView.as_view(), name='search'),
    # path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tag/<slug:slug>/', views.TagDetailView.as_view(), name='tag_detail'),
    path("authors/", views.AuthorListView.as_view(), name="author_list"),
    path("author/<str:username>/", views.AuthorDetailView.as_view(), name="author_detail"),
    path('profile/edit/', AuthorProfileEditView.as_view(), name='profile_edit'),
    path('dashboard/', views.UserPostListView.as_view(), name='dashboard'),
    path('saved/', views.SavedPostsListView.as_view(), name='saved_posts'),
    path('posts/<slug:slug>/bookmark/', views.BookmarkToggleView.as_view(), name='toggle_bookmark'),
    path('api/v1/posts/', api_views.PostListCreateAPIView.as_view(), name='api_post_list'),
    path('api/v1/posts/<slug:slug>/', api_views.PostDetailAPIView.as_view(), name='api_post_detail'),
    path('api/v1/token-auth/', obtain_auth_token, name='api_token_auth'),
    
    
]
