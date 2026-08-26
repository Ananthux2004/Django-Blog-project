from rest_framework import serializers
from .models import Post, Category, Tag

class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.user.username')
    category_name = serializers.ReadOnlyField(source='category.name')
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author', 'category', 
            'category_name', 'tags', 'excerpt', 'content', 
            'status', 'views', 'created_date', 'published_date'
        ]
        read_only_fields = ['slug', 'views', 'created_date']