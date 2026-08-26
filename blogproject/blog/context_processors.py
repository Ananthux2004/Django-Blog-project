from django.db.models import Count
from .models import Post, Category, Tag

def sidebar_context(request):
    all_posts = Post.objects.all().order_by('-published_date')
    return {
        'recent_posts': all_posts[:5],
        'popular_posts': Post.objects.all().order_by('-views')[:5],
        'sidebar_categories': Category.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:10],
        'sidebar_tags': Tag.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:15],
    }