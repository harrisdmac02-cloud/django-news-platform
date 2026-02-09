# core/tests.py

from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser, Publisher, Article, ApiClient, Group


class SubscribedArticlesFeedAPITest(APITestCase):
    """
    Tests for the personalized subscribed feed endpoint
    (returns articles from subscribed publishers + followed independent journalists)
    """

    def setUp(self):
        # Groups
        self.reader_group, _ = Group.objects.get_or_create(name='Reader')
        self.journalist_group, _ = Group.objects.get_or_create(name='Journalist')

        # Reader
        self.reader = CustomUser.objects.create_user(
            username='reader_test',
            password='testpass123',
            email='reader@test.com'
        )
        self.reader.groups.add(self.reader_group)

        # Journalists
        self.journ_independent = CustomUser.objects.create_user(
            username='journ_indep',
            password='testpass123'
        )
        self.journ_independent.groups.add(self.journalist_group)

        self.journ_publisher = CustomUser.objects.create_user(
            username='journ_pub',
            password='testpass123'
        )
        self.journ_publisher.groups.add(self.journalist_group)

        # Publishers
        self.publisher_yes = Publisher.objects.create(name="My Favorite Publisher")
        self.publisher_no = Publisher.objects.create(name="Other Publisher")

        self.publisher_yes.journalists.add(self.journ_publisher)

        # Articles - published
        now = timezone.now()

        def create_article(title, author, publisher=None, delta_hours=0):
            slug = slugify(title)
            # Make slug unique if needed
            base_slug = slug
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            return Article.objects.create(
                title=title,
                slug=slug,
                content=f"Content for {title}",
                excerpt=f"Excerpt for {title}",
                author=author,
                publisher=publisher,
                status='published',
                published_at=now - timedelta(hours=delta_hours)
            )

        self.article_pub_yes = create_article(
            "News from subscribed publisher",
            self.journ_publisher,
            self.publisher_yes,
            delta_hours=3
        )

        self.article_indep_followed = create_article(
            "Independent article - followed journalist",
            self.journ_independent,
            None,
            delta_hours=2
        )

        self.article_pub_no = create_article(
            "News from non-subscribed publisher",
            self.journ_publisher,
            self.publisher_no,
            delta_hours=1
        )

        self.article_indep_not_followed = create_article(
            "Independent - not followed",
            self.journ_publisher,  # different journalist
            None,
            delta_hours=0.5
        )

        # API Client
        self.api_client = ApiClient.objects.create(
            name="Test Client App",
            user=self.reader,
            is_active=True
        )
        self.api_key = self.api_client.api_key

        # Set subscriptions / follows
        self.reader.subscribed_publishers.add(self.publisher_yes)
        self.reader.subscribed_journalists.add(self.journ_independent)

    def get_feed_url(self):
        # Try named URL first - adjust based on your actual urls.py
        possible_names = [
            'api_subscribed_feed',       # from one of your urlpatterns blocks
            'api_feed-subscribed',       # from another block
            'feed-subscribed',           # without api_ prefix
        ]

        for name in possible_names:
            try:
                return reverse(f'core:{name}')
            except:
                pass

        # Fallback - hardcode what you see in urls.py
        # Change this path to match your actual URL pattern
        return '/api/v1/feed/subscribed/'   # ←←← MOST LIKELY CANDIDATE

    def test_authenticated_via_api_key_returns_expected_articles(self):
        """Valid API key → only subscribed + followed independent articles"""
        url = self.get_feed_url()

        response = self.client.get(url, HTTP_X_API_KEY=self.api_key)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        titles = {item['title'] for item in response.data}

        self.assertIn("News from subscribed publisher", titles)
        self.assertIn("Independent article - followed journalist", titles)

        self.assertNotIn("News from non-subscribed publisher", titles)
        self.assertNotIn("Independent - not followed", titles)

    def test_no_subscriptions_or_follows_returns_empty_list(self):
        self.reader.subscribed_publishers.clear()
        self.reader.subscribed_journalists.clear()

        url = self.get_feed_url()
        response = self.client.get(url, HTTP_X_API_KEY=self.api_key)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_invalid_api_key_returns_401(self):
        url = self.get_feed_url()
        response = self.client.get(url, HTTP_X_API_KEY="this-is-definitely-wrong")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_api_client_returns_401(self):
        self.api_client.is_active = False
        self.api_client.save()

        url = self.get_feed_url()
        response = self.client.get(url, HTTP_X_API_KEY=self.api_key)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_drafts_are_not_returned(self):
        draft = Article.objects.create(
            title="This is still a draft",
            slug=slugify("This is still a draft"),
            content="draft content",
            author=self.journ_publisher,
            publisher=self.publisher_yes,
            status='draft'
        )

        url = self.get_feed_url()
        response = self.client.get(url, HTTP_X_API_KEY=self.api_key)

        titles = {item['title'] for item in response.data}
        self.assertNotIn("This is still a draft", titles)

    def test_last_used_at_is_updated_on_successful_request(self):
        url = self.get_feed_url()

        before = self.api_client.last_used_at

        response = self.client.get(url, HTTP_X_API_KEY=self.api_key)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.api_client.refresh_from_db()
        after = self.api_client.last_used_at

        self.assertIsNotNone(after)
        self.assertGreater(after, before or timezone.now() - timedelta(seconds=30))