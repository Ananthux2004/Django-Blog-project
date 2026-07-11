from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to='authors/', blank=True, null=True)
    website = models.URLField(blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ['-joined_date']


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status='published')


class PublishedPostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db).published()


class Post(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('published', 'Published')]

    title = models.CharField(max_length=200, unique=True)
    content = models.TextField()
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name='posts')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft')
    featured_image = models.ImageField(
        upload_to='posts/', blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(null=True, blank=True)

    # Default manager with all posts
    objects = PostQuerySet.as_manager()
    # Extra manager that returns only published posts
    published_objects = PublishedPostManager()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_date']

    def publish(self):
        self.status = 'published'
        self.published_date = timezone.now()
        self.save()


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"

    class Meta:
        ordering = ['created_date']

    def approve(self):
        """Approve the comment"""
        self.is_approved = True
        self.save()
