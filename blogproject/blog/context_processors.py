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