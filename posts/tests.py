from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from .models import Post
from reddit_accounts.models import RedditAccount

User = get_user_model()

class PostTests(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.reddit_account = RedditAccount.objects.create(
            user=self.user,
            username='reddit_test_user',
            is_active=True
        )
        
        self.post_data = {
            'title': 'Test Post',
            'content': 'Test Content',
            'subreddit': 'test',
            'post_now': False
        }
        
        self.post = Post.objects.create(
            user=self.user,
            title='Existing Post',
            content='Existing Content',
            subreddit='test',
            reddit_account=self.reddit_account
        )

    def test_create_post(self):
        """Test creating a new post"""
        response = self.client.post('/api/posts/create/', self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(response.data['title'], 'Test Post')

    def test_list_posts(self):
        """Test listing all posts"""
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_post_detail(self):
        """Test retrieving a specific post"""
        response = self.client.get(f'/api/posts/{self.post.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Existing Post')

    def test_update_post(self):
        """Test updating a post"""
        update_data = {'title': 'Updated Post'}
        response = self.client.put(
            f'/api/posts/{self.post.id}/',
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Post')

    def test_delete_post(self):
        """Test deleting a post"""
        response = self.client.delete(f'/api/posts/{self.post.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Post.objects.count(), 0)

    def test_schedule_post(self):
        """Test scheduling a post"""
        schedule_time = timezone.now() + timezone.timedelta(hours=1)
        response = self.client.post(
            f'/api/posts/{self.post.id}/schedule/',
            {'scheduled_time': schedule_time.isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, Post.STATUS_SCHEDULED)

    def test_publish_post(self):
        """Test publishing a post"""
        response = self.client.post(f'/api/posts/{self.post.id}/publish/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, Post.STATUS_PENDING)

    def test_list_scheduled_posts(self):
        """Test listing scheduled posts"""
        self.post.status = Post.STATUS_SCHEDULED
        self.post.scheduled_time = timezone.now() + timezone.timedelta(hours=1)
        self.post.save()
        
        response = self.client.get('/api/posts/scheduled/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_posted_posts(self):
        """Test listing posted posts"""
        self.post.status = Post.STATUS_POSTED
        self.post.save()
        
        response = self.client.get('/api/posts/posted/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retry_failed_post(self):
        """Test retrying a failed post"""
        self.post.status = Post.STATUS_FAILED
        self.post.save()
        
        response = self.client.post(f'/api/posts/{self.post.id}/retry/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, Post.STATUS_PENDING)