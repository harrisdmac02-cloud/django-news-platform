# core/models.py
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, Group
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.

    Supports three mutually exclusive primary roles via groups:
    • Reader
    • Journalist
    • Editor

    Additional functionality:
    - Profile fields (bio, profile picture)
    - Reader ↔ Journalist subscription/follow relationship
    - Convenience properties to check role membership

    Note: A user should belong to exactly one of the three role groups.
    The application logic is expected to enforce this constraint.
    """

    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    subscribed_journalists = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='journalist_followers',
        blank=True,
        limit_choices_to={'groups__name': 'Journalist'},
    )

    @property
    def is_reader(self):
        """Check if the user belongs to the 'Reader' group."""
        return self.groups.filter(name='Reader').exists()

    @property
    def is_journalist(self):
        """Check if the user belongs to the 'Journalist' group."""
        return self.groups.filter(name='Journalist').exists()

    @property
    def is_editor(self):
        """Check if the user belongs to the 'Editor' group."""
        return self.groups.filter(name='Editor').exists()


class Publisher(models.Model):
    """
    Represents a news organization / media outlet / publisher.

    Publishers serve as:
    • Organizational grouping for articles
    • Affiliation entity for journalists
    • Management entity for editors
    • Subscription target for readers

    Relationships:
    - Many editors can manage one publisher
    - Many journalists can be affiliated with one publisher
    - Many readers can subscribe to updates from one publisher
    """

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    editors = models.ManyToManyField(
        CustomUser,
        related_name='editing_publishers',
        limit_choices_to={'groups__name': 'Editor'},
        blank=True,
    )
    journalists = models.ManyToManyField(
        CustomUser,
        related_name='affiliated_publishers',
        limit_choices_to={'groups__name': 'Journalist'},
        blank=True,
    )
    subscribed_readers = models.ManyToManyField(
        CustomUser,
        related_name='subscribed_publishers',
        limit_choices_to={'groups__name': 'Reader'},
        blank=True,
    )

    def __str__(self):
        return self.name


class Newsletter(models.Model):
    """
    Model for newsletters created by journalists (independent or publisher-affiliated).

    Newsletters can be in draft or published state.
    Similar in structure to articles but focused on periodic/subscription content.
    """

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=400, blank=True)

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='newsletters',
        limit_choices_to={'groups__name': 'Journalist'}
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newsletters'
    )

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('published', 'Published')],
        default='draft'
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Returns URL to view this newsletter (currently reuses article detail view)."""
        return reverse('core:article_detail', kwargs={'pk': self.pk})


class Article(models.Model):
    """
    Core news article model with complete editorial workflow support.

    Workflow states:
        draft → pending → approved / rejected → published

    Features:
    • Optional association with a Publisher
    • Journalist-only authorship
    • Editor approval tracking
    • Auto-generated unique slugs
    • Lead image support
    • Category tagging
    • Notification control flag

    Business rules:
    - Only users in the 'Journalist' group can be authors
    - Only users in the 'Editor' group can approve articles
    - Published articles should have published_at timestamp
    """

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=400, blank=True)

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='articles',
        limit_choices_to={'groups__name': 'Journalist'}
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_articles',
        limit_choices_to={'groups__name': 'Editor'}
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notifications_sent = models.BooleanField(default=False)  # Prevents duplicate notifications

    categories = models.ManyToManyField('Category', blank=True, related_name='articles')
    lead_image = models.ForeignKey(
        'ArticleImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='lead_articles'
    )

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def publish(self, approved_by=None):
        """
        Marks the article as published and sets relevant timestamps.

        Args:
            approved_by: Optional Editor user who approved the article
        """
        if self.status == 'published':
            return
        self.status = 'published'
        self.published_at = timezone.now()
        if approved_by and approved_by.is_editor:
            self.approved_by = approved_by
            self.approved_at = timezone.now()
            self.notifications_sent = False
            self.save()

    def get_absolute_url(self):
        """Returns the canonical URL for viewing this article."""
        return reverse('core:article_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        """
        Custom save method that auto-generates a unique slug from the title
        if no slug is provided.
        """
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Category(models.Model):
    """
    Categorization tag for articles (e.g. Politics, Technology, Sports).
    """

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ArticleImage(models.Model):
    """
    Images associated with an article, supporting multiple images per article
    with ordering, captions, and lead image designation.
    """

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='articles/%Y/%m/')
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_lead = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.article.title} (order {self.order})"


class ApiClient(models.Model):
    """
    Represents a third-party application / API client that can access
    subscribed content on behalf of a linked reader account.

    Each ApiClient inherits the subscriptions (publishers + followed journalists)
    of its associated user (who must be a Reader).
    """

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    api_key = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        blank=True,   # generated automatically
        help_text="Long random token used for API authentication"
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='api_clients',
        limit_choices_to={'groups__name': 'Reader'},
        help_text="The reader account whose subscriptions this API client can access"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def clean(self):
        """Generate API key if not set and validate its length."""
        if not self.api_key:
            import secrets
            self.api_key = secrets.token_urlsafe(48)
        if len(self.api_key) < 40:
            raise ValidationError("API key is too short")

    def save(self, *args, **kwargs):
        """Ensure full_clean() is called on creation to generate key."""
        if not self.pk:  # only on create
            self.full_clean()  # calls clean()
        super().save(*args, **kwargs)