from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from .forms import CommentForm
from .models import Post, Author

User = get_user_model()


class CommentFormTests(TestCase):
    def test_comment_form_valid_data(self):
        """Test that CommentForm is valid with content."""
        form = CommentForm(data={'content': 'This is a great post!'})
        self.assertTrue(form.is_valid())

    def test_comment_form_empty_data(self):
        """Test that CommentForm fails validation when empty."""
        form = CommentForm(data={'content': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)


class BlogAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author1', password='password123')
        self.author, _ = Author.objects.get_or_create(user=self.user)
        self.token, _ = Token.objects.get_or_create(user=self.user)

        self.other_user = User.objects.create_user(username='author2', password='password123')
        self.other_token, _ = Token.objects.get_or_create(user=self.other_user)

        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Sample post body',
            status='published',
            author=self.author
        )
        
        # Adjust with 'blog:' prefix if app_name = 'blog' is in blog/urls.py
        try:
            self.list_url = reverse('blog:api_post_list')
            self.detail_url = reverse('blog:api_post_detail', kwargs={'slug': self.post.slug})
        except:
            self.list_url = reverse('api_post_list')
            self.detail_url = reverse('api_post_detail', kwargs={'slug': self.post.slug})

    def test_list_published_posts(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_post_unauthenticated_fails(self):
        data = {'title': 'Unauth Post', 'content': 'Content'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_authenticated_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {
            'title': 'New Auth Post',
            'content': 'Content via test client',
            'status': 'published'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)

    def test_update_post_permission_denied_for_non_author(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_token.key)
        response = self.client.patch(self.detail_url, {'title': 'Unauthorized Update'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)