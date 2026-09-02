from django.db.models import Count
from .models import Post, Category, Tag

def sidebar_context(request):
    # Filter for published posts and order by created_date descending
    published_posts = Post.objects.filter(status='published').order_by('-created_date')
    
    return {
        'recent_posts': published_posts[:5],
        'popular_posts': published_posts.order_by('-views')[:5],
        'sidebar_categories': Category.objects.annotate(
            post_count=Count('posts')
        ).order_by('-post_count')[:10],
        'sidebar_tags': Tag.objects.annotate(
            post_count=Count('posts')
        ).order_by('-post_count')[:15],
    }
def categories_processor(request):
    """
    Makes non-empty categories available globally to all templates for the navbar.
    """
    categories = Category.objects.annotate(
        post_count=Count('posts')
    ).filter(post_count__gt=0).order_by('name')
    
    return {
        'navbar_categories': categories
    }
def notification_context(request):
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        return {"unread_notifications_count": unread_count}
    return {"unread_notifications_count": 0}