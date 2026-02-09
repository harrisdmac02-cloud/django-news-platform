from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response

from .authentication import ApiKeyAuthentication
from .models import Article, Publisher, CustomUser
from .serializers import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticlePublicSerializer
)
from .permissions import IsApiClientForSubscribedContent


class MyPersonalizedFeedView(generics.ListAPIView):
    """
    API endpoint for personalized feed for authenticated reader:
        - Articles from publishers the user is subscribed to
        - Articles from independent journalists the user follows
    """
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Get IDs of followed publishers and journalists
        followed_publisher_ids = user.subscribed_publishers.values_list('id', flat=True)
        followed_journalist_ids = user.subscribed_journalists.values_list('id', flat=True)

        # Articles from subscribed publishers
        qs_publisher = Article.objects.filter(
            publisher__id__in=followed_publisher_ids,
            status='published'
        )

        # Articles from followed independent journalists (publisher is NULL)
        qs_independent_journalists = Article.objects.filter(
            author__id__in=followed_journalist_ids,
            publisher__isnull=True,          # ← very important!
            status='published'
        )

        # Union + most recent first
        return (qs_publisher | qs_independent_journalists)\
            .select_related('author', 'publisher')\
            .distinct()\
            .order_by('-published_at')


class ArticleListView(generics.ListAPIView):
    """API endpoint for public list of latest published articles."""
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Article.objects.filter(status='published')\
            .select_related('author', 'publisher')\
            .order_by('-published_at')


class ArticleDetailView(generics.RetrieveAPIView):
    """API endpoint for public detail of any published article."""
    serializer_class = ArticleDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        return Article.objects.filter(status='published')\
            .select_related('author', 'publisher', 'approved_by')


class PublisherArticlesView(generics.ListAPIView):
    """API endpoint for all published articles of one publisher."""
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        publisher = get_object_or_404(Publisher, pk=self.kwargs['pk'])
        return Article.objects.filter(
            publisher=publisher,
            status='published'
        ).select_related('author').order_by('-published_at')


class JournalistArticlesView(generics.ListAPIView):
    """API endpoint for all published articles of one journalist (independent + publisher articles)."""
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        journalist = get_object_or_404(CustomUser, username=self.kwargs['username'])
        return Article.objects.filter(
            author=journalist,
            status='published'
        ).select_related('publisher').order_by('-published_at')

class SubscribedArticlesFeed(generics.ListAPIView):
    """
    GET /api/v1/feed/subscribed/

    Returns paginated list of published articles from:
    - publishers the linked user is subscribed to
    - independent journalists the linked user follows
    """
    serializer_class = ArticlePublicSerializer
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsApiClientForSubscribedContent]
    pagination_class = None  # or use PageNumberPagination / LimitOffsetPagination

    def get_queryset(self):
        user = self.request.user

        pub_ids = user.subscribed_publishers.values_list('id', flat=True)
        journ_ids = user.subscribed_journalists.values_list('id', flat=True)

        qs_pub = Article.objects.filter(
            publisher__id__in=pub_ids,
            status='published'
        )

        qs_indep = Article.objects.filter(
            author__id__in=journ_ids,
            publisher__isnull=True,
            status='published'
        )

        return (qs_pub | qs_indep) \
            .select_related('author', 'publisher') \
            .distinct() \
            .order_by('-published_at')

class PublicPublisherArticles(generics.ListAPIView):
    """Public list of published articles for one publisher"""
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        publisher = get_object_or_404(Publisher, pk=self.kwargs['pk'])
        return Article.objects.filter(
            publisher=publisher,
            status='published'
        ).select_related('author').order_by('-published_at')


class PublicJournalistArticles(generics.ListAPIView):
    """Public list of published articles by one journalist"""
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        journalist = get_object_or_404(CustomUser, username=self.kwargs['username'])
        return Article.objects.filter(
            author=journalist,
            status='published'
        ).select_related('publisher').order_by('-published_at')


class PublisherArticlesPublic(generics.ListAPIView):
    """
    GET /api/v1/publishers/<pk>/articles/

    Public list – but can be rate-limited or scoped later
    """
    serializer_class = ArticlePublicSerializer
    permission_classes = [permissions.AllowAny]  # or restrict to ApiClient

    def get_queryset(self):
        publisher = get_object_or_404(Publisher, pk=self.kwargs['pk'])
        return Article.objects.filter(
            publisher=publisher,
            status='published'
        ).select_related('author').order_by('-published_at')

class JournalistArticlesPublic(generics.ListAPIView):
    """
    GET /api/v1/journalists/<username>/articles/
    """
    serializer_class = ArticlePublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        journalist = get_object_or_404(CustomUser, username=self.kwargs['username'])
        return Article.objects.filter(
            author=journalist,
            status='published'
        ).select_related('publisher').order_by('-published_at')


class PublicJournalistArticlesView(generics.ListAPIView):
    """
    GET /api/v1/journalists/<username>/articles/public/

    Publicly accessible list of all **published** articles written by a specific journalist.
    Shows both independent articles and articles published through publishers.

    No authentication required.
    """
    serializer_class = ArticlePublicSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # or use rest_framework.pagination.PageNumberPagination

    def get_queryset(self):
        username = self.kwargs.get('username')

        journalist = get_object_or_404(
            CustomUser,
            username=username,
            groups__name='Journalist'  # only real journalists
        )

        # Only published articles
        # Includes both: publisher-affiliated and independent (publisher IS NULL)
        return Article.objects.filter(
            author=journalist,
            status='published'
        ).select_related(
            'publisher',
            'author'
        ).order_by('-published_at')

    def get_serializer_context(self):
        """
        Pass request to serializer so we can build absolute URLs if needed
        """
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Optional: add extra context / metadata
        journalist = get_object_or_404(CustomUser, username=kwargs.get('username'))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['journalist'] = {
                'username': journalist.username,
                'full_name': journalist.get_full_name() or journalist.username,
                'bio': journalist.bio or None,
                # You can add more public fields if desired
            }
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'journalist': {
                'username': journalist.username,
                'full_name': journalist.get_full_name() or journalist.username,
                'bio': journalist.bio or None,
            },
            'results': serializer.data,
            'count': queryset.count(),
        })