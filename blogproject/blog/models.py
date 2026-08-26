from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse

class Author(models.Model):
    """
    Stores a profile for a Django User.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    bio = models.TextField(max_length=500, blank=True)

    profile_picture = models.ImageField(
        upload_to="authors/",
        blank=True,
        null=True,
    )

    website = models.URLField(blank=True, null=True)
    joined_date = models.DateTimeField(auto_now_add=True)

    github = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)

    location = models.CharField(max_length=255, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ["-joined_date"]
        indexes = [
            models.Index(fields=["joined_date"]),
            models.Index(fields=["updated_at"]),
        ]


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)

    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
    )

    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
        ]


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)

    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
        ]


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Post.StatusChoices.PUBLISHED)


class PublishedPostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db).published()


class Post(models.Model):

    class StatusChoices(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200, unique=True)

    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
    )

    excerpt = models.TextField(blank=True)

    content = models.TextField()

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="posts",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="posts",
    )

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )

    featured_image = models.ImageField(
        upload_to="posts/",
        blank=True,
        null=True,
    )

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(blank=True, null=True)

    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=0)

    objects = PostQuerySet.as_manager()
    published = PublishedPostManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def publish(self):
        self.status = self.StatusChoices.PUBLISHED
        self.published_date = timezone.now()
        self.save(update_fields=["status", "published_date"])

    def get_absolute_url(self):
        return reverse(
            "blog:post_detail",
            kwargs={"slug": self.slug},
        )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ["-created_date"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_date"]),
            models.Index(fields=["published_date"]),
        ]
class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    name = models.CharField(max_length=80)
    email = models.EmailField()
    content = models.TextField()

    created_date = models.DateTimeField(auto_now_add=True)

    is_approved = models.BooleanField(default=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="comments",
        blank=True,
        null=True,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    def approve(self):
        self.is_approved = True
        self.is_active = True
        self.save()

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["-created_date"]
        indexes = [
            models.Index(fields=["created_date"]),
            models.Index(fields=["is_active"]),
        ]
from django.db import models
from django.conf import settings

class Bookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='bookmarks'
    )
    post = models.ForeignKey(
        'Post', 
        on_delete=models.CASCADE, 
        related_name='bookmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_user_post_bookmark')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.post.title}"