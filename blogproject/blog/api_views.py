from rest_framework import generics, permissions, filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Post, Author
from .serializers import PostSerializer
from .permissions import IsAuthorOrReadOnly


@extend_schema_view(
    get=extend_schema(
        summary="List published posts",
        description="Returns a paginated list of published posts. Staff users can view all posts regardless of status."
    ),
    post=extend_schema(
        summary="Create a new post",
        description="Creates a new post attached to the authenticated user's author profile."
    )
)
class PostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'author__user__username', 'category__name']
    ordering_fields = ['created_date', 'views', 'title']
    ordering = ['-created_date']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Post.objects.select_related('author__user', 'category').prefetch_related('tags').all()
        return Post.objects.select_related('author__user', 'category').prefetch_related('tags').filter(status='published')

    def perform_create(self, serializer):
        author, _ = Author.objects.get_or_create(user=self.request.user)
        serializer.save(author=author)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve post details",
        description="Fetch a single post by its slug."
    ),
    put=extend_schema(
        summary="Update a post (Full)",
        description="Replace all fields of an existing post. Must be the author."
    ),
    patch=extend_schema(
        summary="Update a post (Partial)",
        description="Modify specific fields of an existing post. Must be the author."
    ),
    delete=extend_schema(
        summary="Delete a post",
        description="Remove a post permanently from the blog. Must be the author."
    )
)
class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.select_related('author__user', 'category').prefetch_related('tags')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    lookup_field = 'slug'