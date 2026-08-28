from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q, Count, Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views.generic import View, CreateView, DeleteView, DetailView, ListView, UpdateView
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseNotAllowed

from .forms import PostForm, CommentForm, AuthorProfileForm
from .models import Post, Comment, Category, Tag, Author, Bookmark

User = get_user_model()


# ==========================================
# CORE & HOMEPAGE VIEWS
# ==========================================

from django.shortcuts import render
from django.db.models import Count
from django.core.cache import cache
from .models import Post, Category, Tag


def home(request):
    if request.user.is_staff:
        posts_qs = Post.objects.all()
    else:
        posts_qs = Post.objects.filter(status=Post.StatusChoices.PUBLISHED)

    posts = posts_qs.select_related('author__user', 'category').prefetch_related('tags')
    
    # Order by published_date first so newly published drafts sort to the top
    recent_qs = posts.order_by('-published_date', '-created_date')

    # Cache post IDs while preserving fresh live view counter evaluations
    latest_post_ids = cache.get('homepage_latest_post_ids')
    if latest_post_ids is None:
        latest_post_ids = list(recent_qs.values_list('id', flat=True)[:6])
        cache.set('homepage_latest_post_ids', latest_post_ids, 60 * 15)

    # Re-evaluate live model instances with fresh view counts
    posts_dict = {p.id: p for p in posts.filter(id__in=latest_post_ids)}
    latest_posts = [posts_dict[pid] for pid in latest_post_ids if pid in posts_dict]

    context = {
        'posts': recent_qs,
        'latest_posts': latest_posts,
        'featured_post': recent_qs.first(),
        'recent_posts': recent_qs[:5],
        'popular_posts': posts.order_by('-views')[:5],
        'sidebar_categories': Category.objects.annotate(post_count=Count('posts')).order_by('name'),
        'sidebar_tags': Tag.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:10],
    }

    return render(request, "blog/home.html", context)
# ==========================================
# MIXINS & SIDEBAR CONTEXT
# ==========================================

class BlogSidebarMixin:
    """
    Mixin to provide shared context for the sidebar across multiple blog views.
    Optimizes queries and ensures data is consistently available.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_staff:
            sidebar_posts = Post.objects.all()
        else:
            sidebar_posts = Post.objects.filter(status='published')
            
        # Optimization: select_related('author__user') prevents N+1 queries when fetching usernames
        context['recent_posts'] = sidebar_posts.select_related('author__user', 'category').order_by('-published_date')[:5]
        context['popular_posts'] = sidebar_posts.select_related('author__user', 'category').order_by('-views')[:5]
        context['sidebar_categories'] = Category.objects.annotate(post_count=Count('posts')).order_by('name')
        context['sidebar_tags'] = Tag.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:10]
        
        return context


# ==========================================
# POST CRUD VIEWS (INCORPORATING SIDEBAR)
# ==========================================

class PostListView(BlogSidebarMixin, ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"

    def get_queryset(self):
        qs = Post.objects.select_related("author__user", "category").prefetch_related("tags")
        if self.request.user.is_staff:
            return qs.order_by("-created_date")
        return qs.published().order_by("-created_date")


class PostDetailView(BlogSidebarMixin, DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        obj = get_object_or_404(queryset, slug=self.kwargs.get(self.slug_url_kwarg))
        if (not self.request.user.is_staff) and obj.status != Post.StatusChoices.PUBLISHED:
            raise Http404("Post not found.")
        return obj

    def get_queryset(self):
        qs = Post.objects.select_related("author__user", "category").prefetch_related("tags")
        if self.request.user.is_staff:
            return qs
        return qs.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch only approved, active, top-level comments
        context['comments'] = self.object.comments.filter(is_active=True, is_approved=True, parent__isnull=True)
        context['comment_form'] = CommentForm()
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Check if current user is authenticated and is the author of this post
        is_author = (
            request.user.is_authenticated 
            and hasattr(self.object, 'author') 
            and self.object.author 
            and self.object.author.user == request.user
        )

        # Retrieve viewed posts array from session
        viewed_posts = request.session.get('viewed_posts', [])

        # Only increment if visitor is NOT author and hasn't viewed this post in current session
        if not is_author and self.object.pk not in viewed_posts:
            Post.objects.filter(pk=self.object.pk).update(views=F("views") + 1)
            self.object.refresh_from_db(fields=['views'])
            
            viewed_posts.append(self.object.pk)
            request.session['viewed_posts'] = viewed_posts

        return response
class PostCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    success_message = "Post created successfully."
    slug_field = "slug"

    def form_valid(self, form):
        if hasattr(self.request.user, 'author'):
            form.instance.author = self.request.user.author
        else:
            form.instance.author = self.request.user

        action = self.request.POST.get('action')
        if action == 'draft':
            form.instance.status = 'draft'
            response = super().form_valid(form)
            # Redirect straight to dashboard filtered by drafts
            return redirect(f"{reverse_lazy('blog:dashboard')}?status=draft")
        else:
            form.instance.status = 'published'
            return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"slug": self.object.slug})
    
class PostUpdateView(SuccessMessageMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    success_message = "Post updated successfully."
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_staff or obj.author.user == self.request.user

    def form_valid(self, form):
        # Set status based on the button submitted
        if self.request.POST.get('action') == 'publish':
            form.instance.status = getattr(Post.StatusChoices, 'PUBLISHED', 'published')
        else:
            form.instance.status = getattr(Post.StatusChoices, 'DRAFT', 'draft')

        return super().form_valid(form)

    def get_success_url(self):
        # Redirect drafts to dashboard so non-staff authors don't hit a 404 on post_detail
        if self.object.status == getattr(Post.StatusChoices, 'DRAFT', 'draft'):
            return reverse_lazy("blog:dashboard")
        return reverse_lazy("blog:post_detail", kwargs={"slug": self.object.slug})
    
class PostDeleteView(SuccessMessageMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView):
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
            queryset = Post.objects.select_related("author__user", "category").prefetch_related("tags")
        obj = get_object_or_404(queryset, pk=self.kwargs.get("pk"))
        if (not self.request.user.is_staff) and obj.status != Post.StatusChoices.PUBLISHED:
            raise Http404("Post not found.")
        return obj

    def get_queryset(self):
        qs = Post.objects.select_related("author__user", "category").prefetch_related("tags")
        if self.request.user.is_staff:
            return qs
        return qs.published()


# ==========================================
# COMMENT MANAGEMENT SYSTEMS
# ==========================================

@login_required
def add_comment(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.name = request.user.username  # Auto-fill name
            comment.email = request.user.email    # Auto-fill email
            comment.is_approved = True            # Auto-approve comment
            comment.save()
            messages.success(request, 'Comment submitted successfully.')
    return redirect('blog:post_detail', slug=post.slug)


@login_required
def reply_comment(request, slug, pk):
    post = get_object_or_404(Post, slug=slug)
    parent_comment = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.post = post
            reply.user = request.user
            reply.parent = parent_comment
            reply.name = request.user.username  # Auto-fill name
            reply.email = request.user.email    # Auto-fill email
            reply.is_approved = True            # Auto-approve reply
            reply.save()
            messages.success(request, 'Reply submitted successfully.')
    return redirect('blog:post_detail', slug=post.slug)


@login_required
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    # Safe slug lookup whether it's a main comment or nested reply
    post_slug = comment.post.slug if comment.post else comment.parent.post.slug

    if request.user != comment.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this comment.')
        return redirect('blog:post_detail', slug=post_slug)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comment updated successfully.')
        else:
            messages.error(request, 'Failed to update comment. Please check your text.')
    
    return redirect('blog:post_detail', slug=post_slug)


@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    if request.user == comment.user or request.user.is_staff:
        comment.is_active = False  # Soft delete
        comment.save()
        messages.success(request, 'Comment deleted successfully.')
    else:
        messages.error(request, 'You do not have permission to delete this comment.')
    return redirect('blog:post_detail', slug=comment.post.slug)


# ==========================================
# PHASE 2.5: SEARCH, CATEGORIES & TAGS
# ==========================================

class SearchResultsView(BlogSidebarMixin, ListView):
    model = Post
    template_name = 'blog/search_results.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        
        if self.request.user.is_staff:
            queryset = Post.objects.all()
        else:
            queryset = Post.objects.filter(status='published')
            
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(content__icontains=query) |
                Q(category__name__icontains=query) |
                Q(tags__name__icontains=query) |
                Q(author__user__username__icontains=query)
            )
        
        return queryset.select_related('author__user', 'category').prefetch_related('tags').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class CategoryListView(ListView):
    model = Category
    template_name = 'blog/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.annotate(post_count=Count('posts')).order_by('name')


class CategoryDetailView(BlogSidebarMixin, DetailView):
    model = Category
    template_name = 'blog/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        if self.request.user.is_staff:
            posts = Post.objects.filter(category=category)
        else:
            posts = Post.objects.filter(category=category, status='published')
            
        context['posts'] = posts.select_related('author__user', 'category').prefetch_related('tags').order_by('-published_date')
        return context


class TagListView(ListView):
    model = Tag
    template_name = 'blog/tag_list.html'
    context_object_name = 'tags'
    
    def get_queryset(self):
        return Tag.objects.annotate(post_count=Count('posts')).order_by('name')


class TagDetailView(BlogSidebarMixin, DetailView):
    model = Tag
    template_name = 'blog/tag_detail.html'
    context_object_name = 'tag'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag = self.get_object()
        
        if self.request.user.is_staff:
            posts = Post.objects.filter(tags=tag)
        else:
            posts = Post.objects.filter(tags=tag, status='published')
            
        context['posts'] = posts.select_related('author__user', 'category').prefetch_related('tags').order_by('-published_date')
        return context


# ==========================================
# PHASE 2.6: AUTHOR PROFILE VIEWS
# ==========================================

class AuthorListView(BlogSidebarMixin, ListView):
    model = Author
    template_name = "blog/author_list.html"
    context_object_name = "authors"
    
    def get_queryset(self):
        return Author.objects.select_related('user').annotate(
            published_posts_count=Count('posts', filter=Q(posts__status='published'))
        ).filter(published_posts_count__gt=0).order_by('-published_posts_count')


class AuthorDetailView(BlogSidebarMixin, DetailView):
    """
    Enhanced public author profile page with statistics,
    owner-only draft counts, featured articles, and paginated recent posts.
    """
    model = Author
    template_name = "blog/author_detail.html"
    context_object_name = "author"
    slug_field = "user__username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.object
        user = self.request.user

        # Owner verification check
        is_owner = user.is_authenticated and user == author.user
        context['is_owner'] = is_owner

        # Base Published Queryset
        published_posts = Post.objects.filter(
            author=author, status='published'
        ).select_related('author__user', 'category').prefetch_related('tags')

        # Statistics
        context['published_count'] = published_posts.count()
        context['draft_count'] = Post.objects.filter(author=author, status='draft').count() if is_owner else 0
        context['total_views'] = published_posts.aggregate(total_v=Sum('views'))['total_v'] or 0
        
        # Comments count on author's published posts
        context['total_comments'] = Comment.objects.filter(
            post__author=author,
            post__status='published',
            is_approved=True,
            is_active=True
        ).count()

        # Featured Posts (Top 3)
        if hasattr(Post, 'is_featured'):
            context['featured_posts'] = published_posts.filter(is_featured=True)[:3]
        elif hasattr(Post, 'featured'):
            context['featured_posts'] = published_posts.filter(featured=True)[:3]
        else:
            context['featured_posts'] = []

        # Recent Posts with Pagination (6 posts per page)
        order_field = '-published_date' if hasattr(Post, 'published_date') else '-created_date'
        recent_posts_qs = published_posts.order_by(order_field)
        
        paginator = Paginator(recent_posts_qs, 6)
        page_number = self.request.GET.get('page')
        context['page_obj'] = paginator.get_page(page_number)

        return context


class AuthorProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Author
    form_class = AuthorProfileForm
    template_name = 'blog/profile_edit.html'
    success_message = "Profile updated successfully."

    def get_object(self, queryset=None):
        """
        Always return the authenticated user's Author instance
        to prevent editing other profiles.
        """
        return self.request.user.author

    def get_success_url(self):
        """
        Redirect to the user's profile page after successful update.
        """
        author = self.get_object()
        if hasattr(author, 'get_absolute_url'):
            return author.get_absolute_url()
        return reverse_lazy('blog:author_detail', kwargs={'username': author.user.username})


class MyPostsDashboardView(LoginRequiredMixin, BlogSidebarMixin, ListView):
    model = Post
    template_name = "blog/my_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        # Base QuerySet restricted to current authenticated author
        qs = Post.objects.filter(author__user=self.request.user)\
                         .select_related("category", "author__user")\
                         .prefetch_related("tags")

        # Filtering logic
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter == 'published':
            qs = qs.filter(status=getattr(Post.StatusChoices, 'PUBLISHED', 'published'))
        elif status_filter == 'draft':
            qs = qs.filter(status=getattr(Post.StatusChoices, 'DRAFT', 'draft'))
        elif status_filter == 'featured':
            if hasattr(Post, 'is_featured'):
                qs = qs.filter(is_featured=True)
            elif hasattr(Post, 'featured'):
                qs = qs.filter(featured=True)

        # Sorting logic
        sort_by = self.request.GET.get('sort', 'newest').strip()
        if sort_by == 'oldest':
            qs = qs.order_by('created_date')
        elif sort_by == 'views':
            qs = qs.order_by('-views', '-created_date')
        else:  # Default: newest
            qs = qs.order_by('-created_date')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate summary statistics for dashboard header widgets
        user_posts = Post.objects.filter(author__user=self.request.user)
        context['total_my_posts'] = user_posts.count()
        context['published_my_posts'] = user_posts.filter(status='published').count()
        context['draft_my_posts'] = user_posts.filter(status='draft').count()
        
        # Filter and Sort states for UI controls
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context


# ==========================================
# BOOKMARK & SAVED POSTS
# ==========================================

class BookmarkToggleView(LoginRequiredMixin, View):
    """Save or remove a post from user bookmarks."""
    def post(self, request, slug, *args, **kwargs):
        post = get_object_or_404(Post, slug=slug)
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)

        if not created:
            # Already saved, so remove it
            bookmark.delete()
            is_bookmarked = False
        else:
            is_bookmarked = True

        # AJAX support
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'is_bookmarked': is_bookmarked,
                'bookmark_count': post.bookmarks.count()
            })

        # Redirect back to referring page or post detail
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', 'blog:post_list'))
        return redirect(next_url)


class SavedPostsListView(LoginRequiredMixin, ListView):
    """View all bookmarked posts for the logged-in user."""
    model = Bookmark
    template_name = 'blog/saved_posts.html'
    context_object_name = 'bookmarks'
    paginate_by = 10

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related(
            'post', 'post__author'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_saved'] = Bookmark.objects.filter(user=self.request.user).count()
        return context
class UserPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "blog/my_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_author_qs(self):
        user = self.request.user
        if hasattr(user, 'author'):
            return Post.objects.filter(author=user.author)
        return Post.objects.filter(Q(author=user) | Q(author__user=user))

    def get_queryset(self):
        qs = self.get_author_qs()
        status_param = self.request.GET.get('status')
        sort_param = self.request.GET.get('sort', 'newest')

        # Filter by status tab selection
        if status_param == 'draft':
            qs = qs.filter(Q(status__iexact='draft') | Q(status='D'))
        elif status_param == 'published':
            qs = qs.filter(Q(status__iexact='published') | Q(status='P'))
        elif status_param == 'featured':
            qs = qs.filter(Q(is_featured=True) | Q(featured=True))

        # Sorting choices
        if sort_param == 'oldest':
            qs = qs.order_by('created_date')
        elif sort_param == 'views':
            qs = qs.order_by('-views')
        else:
            qs = qs.order_by('-created_date')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_user_posts = self.get_author_qs()

        # Counter stats for top dashboard cards
        context['total_my_posts'] = all_user_posts.count()
        context['published_my_posts'] = all_user_posts.filter(Q(status__iexact='published') | Q(status='P')).count()
        context['draft_my_posts'] = all_user_posts.filter(Q(status__iexact='draft') | Q(status='D')).count()

        # Active filter tracking for UI pills
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context