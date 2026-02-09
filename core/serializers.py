from rest_framework import serializers
from django.conf import settings

from .models import Article, Publisher, CustomUser


class MinimalUserSerializer(serializers.ModelSerializer):
    """
    Minimal representation of a CustomUser, used as nested serializer
    for author fields in article serializers.
    """

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name']


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for Publisher model, exposing basic public information.
    Used as nested field in article serializers.
    """

    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description', 'website']


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing articles (summary view).

    Includes nested author and publisher data, but excludes full content.
    Intended for list views, feeds, and search results.
    """

    author = MinimalUserSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'publisher',
            'author',
            'status',
            'published_at',
            'created_at',
        ]
        read_only_fields = ['status', 'published_at']


class ArticleDetailSerializer(ArticleListSerializer):
    """
    Detailed serializer for a single article.

    Extends ArticleListSerializer by adding the full content field.
    Used for individual article detail views.
    """

    content = serializers.CharField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ['content']


class ArticlePublicSerializer(serializers.ModelSerializer):
    """
    Public-facing serializer for articles.

    Includes full content and an absolute URL field.
    Used for API endpoints that expose articles to unauthenticated users
    or third-party clients (e.g. public feeds, embeds, RSS-like access).

    The absolute_url field tries to use the request context when available
    (for correct domain in production), falling back to a relative path.
    """

    author = MinimalUserSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'content',
            'publisher',
            'author',
            'published_at',
            'created_at',
            'absolute_url',
        ]
        read_only_fields = ['published_at', 'created_at']

    def get_absolute_url(self, obj):
        """
        Returns the absolute URL for the article.

        Uses request.build_absolute_uri() when request context is available
        (normal API requests). Falls back to a simple relative path when
        no request context exists (e.g. in unit tests, background tasks,
        or when serializer is used without a view context).

        Args:
            obj: Article instance

        Returns:
            str: Absolute or relative URL to the article detail page
        """
        request = self.context.get('request')
        if request:
            try:
                return request.build_absolute_uri(obj.get_absolute_url())
            except Exception:
                # Fallback when reverse lookup fails (e.g. URL name missing)
                return f"/article/{obj.pk}/"

        # Fallback for tests / no request context
        return f"/article/{obj.pk}/"