from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q, Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from .forms import PostForm, CommentForm
from .models import Post, Comment, Category, Tag


# ==========================================
# CORE & HOMEPAGE VIEWS
# ==========================================

def home(request):
    """Template-driven homepage."""
    return render(request, "blog/home.html")


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
        Post.objects.filter(pk=self.object.pk).update(views=F("views") + 1)
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

    def get_success_url(self):
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
    
    if request.user != comment.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this comment.')
        return redirect('blog:post_detail', slug=comment.post.slug)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comment updated successfully.')
            return redirect('blog:post_detail', slug=comment.post.slug)
    else:
        form = CommentForm(instance=comment)
        
    return render(request, 'blog/comment_form.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    if request.user == comment.user or request.user.is_staff:
        comment.is_active = False # Soft delete
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