# core/views.py
"""
Views for the news platform.

This module contains:
- Function-based views for article/newsletter CRUD, approval, follow/unfollow
- Class-based generic views for dashboards, profiles, lists, and feeds
- Helper functions for notifications and social posting
"""

from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mass_mail
from django.conf import settings
import requests
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, CreateView, TemplateView
from rest_framework import permissions, generics

from .decorators import journalist_required
from .models import Article, Publisher, CustomUser, Newsletter
from .forms import ArticleForm, ArticleApprovalForm, SignUpForm, NewsletterForm
from .serializers import ArticleListSerializer


# ──────────────────────────────────────────────────────────────
# Article Approval + Notifications
# ──────────────────────────────────────────────────────────────

@login_required
@permission_required('core.change_article', raise_exception=True)
def article_approve(request, pk):
    """
    Allow editors to approve, reject, or change the status of an article.

    On approval, calls article.publish() and sends notifications.
    """
    article = get_object_or_404(Article, pk=pk)
    if article.status in ['published', 'rejected']:
        messages.warning(
            request,
            f"Article already {article.get_status_display().lower()}."
        )
        return redirect('core:article_detail', pk=article.pk)

    if request.method == 'POST':
        form = ArticleApprovalForm(request.POST, instance=article)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            if new_status == 'approved':
                article.publish(approved_by=request.user)
                messages.success(request, "Article published.")
            else:
                article.status = new_status
                article.save()
                messages.info(request, f"Status updated to {article.get_status_display()}.")
            return redirect('core:article_detail', pk=article.pk)
    else:
        form = ArticleApprovalForm(instance=article)

    return render(request, 'core/article_approve.html', {
        'article': article,
        'form': form,
        'can_approve': request.user.has_perm('core.change_article')
    })


def send_notifications_to_subscribers(article):
    """
    Send email notifications to all readers subscribed to the publisher
    or following the journalist who authored the article.
    """
    if not settings.EMAIL_HOST:
        print("Email settings not configured - skipping notifications")
        return

    subscribers = set()

    if article.publisher:
        subscribers.update(article.publisher.subscribed_readers.all())

    if article.author and article.author.is_journalist:
        subscribers.update(article.author.journalist_followers.all())

    if not subscribers:
        return

    subject = f"New Article: {article.title}"
    message = (
        f"A new article '{article.title}' has been published.\n\n"
        f"Read it here: {settings.SITE_URL}{article.get_absolute_url()}\n\n"
        f"Best regards,\nThe News Platform Team"
    )

    messages_to_send = [
        (subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        for user in subscribers if user.email
    ]

    try:
        send_mass_mail(messages_to_send, fail_silently=False)
    except Exception as e:
        print(f"Failed to send notification emails: {e}")


def post_to_x(article):
    """
    Post a tweet about a newly published article to X (Twitter).
    Requires TWITTER_BEARER_TOKEN in settings.
    """
    if not hasattr(settings, 'TWITTER_BEARER_TOKEN'):
        print("Twitter/X credentials not configured")
        return

    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }

    text = (
        f"New article: {article.title}\n"
        f"by {article.author.username}\n"
        f"{settings.SITE_URL}{article.get_absolute_url()}\n"
        f"#News #Journalism"
    )[:280]

    payload = {"text": text}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 201:
            print("Successfully posted to X")
        else:
            print(f"Failed to post to X: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error posting to X: {e}")


# ──────────────────────────────────────────────────────────────
# Article CRUD
# ──────────────────────────────────────────────────────────────

@journalist_required
def article_create(request):
    """
    Allow journalists to create a new article (starts as 'pending' status).
    """
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.status = 'pending'
            article.save()
            messages.success(request, "Article created successfully.")
            return redirect('core:article_detail', pk=article.pk)
    else:
        form = ArticleForm()

    return render(request, 'core/article_form.html', {
        'form': form,
        'title': 'Create Article'
    })


@login_required
def article_update(request, pk):
    """
    Allow the article author (journalist) or an editor to update an article.
    """
    article = get_object_or_404(Article, pk=pk)

    if not ((article.author == request.user and request.user.is_journalist)
            or request.user.is_editor):
        messages.error(request, "You don't have permission to update this article.")
        return redirect('core:article_detail', pk=pk)

    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article updated successfully.")
            return redirect('core:article_detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)

    return render(request, 'core/article_form.html', {
        'form': form,
        'title': 'Edit Article',
        'article': article
    })


# ──────────────────────────────────────────────────────────────
# Newsletter
# ──────────────────────────────────────────────────────────────

@journalist_required
def newsletter_create(request):
    """Create a new newsletter (starts as draft)."""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.status = 'draft'
            newsletter.save()
            messages.success(request, "Newsletter created successfully.")
            return redirect('core:newsletter_detail', pk=newsletter.pk)
    else:
        form = NewsletterForm()

    return render(request, 'core/newsletter_form.html', {'form': form})


@journalist_required
def newsletter_publish(request, pk):
    """Publish a draft newsletter."""
    newsletter = get_object_or_404(Newsletter, pk=pk, author=request.user)

    if newsletter.status == 'published':
        messages.warning(request, "This newsletter is already published.")
        return redirect('core:newsletter_detail', pk=newsletter.pk)

    if request.method == 'POST':
        newsletter.status = 'published'
        newsletter.published_at = timezone.now()
        newsletter.save()
        messages.success(request, "Newsletter published successfully.")
        return redirect('core:newsletter_detail', pk=newsletter.pk)

    return render(request, 'core/newsletter_publish.html', {
        'newsletter': newsletter
    })


@journalist_required
def newsletter_update(request, pk):
    """Update an existing newsletter."""
    newsletter = get_object_or_404(Newsletter, pk=pk, author=request.user)

    if request.method == 'POST':
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, "Newsletter updated successfully.")
            return redirect('core:newsletter_detail', pk=newsletter.pk)
    else:
        form = NewsletterForm(instance=newsletter)

    return render(request, 'core/newsletter_update.html', {
        'form': form,
        'newsletter': newsletter
    })


# ──────────────────────────────────────────────────────────────
# Class-Based Views
# ──────────────────────────────────────────────────────────────

class HomeView(ListView):
    """Homepage showing latest 6 published featured articles."""
    model = Article
    template_name = 'core/home.html'
    context_object_name = 'featured_articles'

    def get_queryset(self):
        return Article.objects.filter(status='published') \
            .select_related('author', 'publisher') \
            .order_by('-published_at')[:6]


class ArticleDetailView(DetailView):
    """Public detail view for a published article."""
    model = Article
    template_name = 'core/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.filter(status='published') \
            .select_related('author', 'publisher', 'approved_by')


class MyFeedView(LoginRequiredMixin, ListView):
    """Personalized feed for logged-in readers (subscribed publishers + followed journalists)."""
    model = Article
    template_name = 'core/my_feed.html'
    context_object_name = 'articles'

    def get_queryset(self):
        user = self.request.user
        if not getattr(user, 'is_reader', False):
            return Article.objects.none()

        pub_ids = user.subscribed_publishers.values_list('id', flat=True)
        journ_ids = user.subscribed_journalists.values_list('id', flat=True)

        return Article.objects.filter(
            Q(publisher_id__in=pub_ids) |
            Q(author_id__in=journ_ids, publisher__isnull=True),
            status='published'
        ).select_related('author', 'publisher').order_by('-published_at')


class PublisherListView(ListView):
    """List all publishers."""
    model = Publisher
    template_name = 'core/publisher_list.html'
    context_object_name = 'publishers'


class JournalistProfileView(DetailView):
    """Public profile page for a journalist with latest articles."""
    model = CustomUser
    template_name = 'core/journalist_profile.html'
    context_object_name = 'journalist'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        return CustomUser.objects.filter(groups__name='Journalist')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_articles'] = self.object.articles.filter(
            status='published'
        ).order_by('-published_at')[:6]
        return context


class NewsletterDetailView(DetailView):
    """Detail view for a newsletter (public or private depending on status)."""
    model = Newsletter
    template_name = 'core/newsletter_detail.html'
    context_object_name = 'newsletter'

    def get_queryset(self):
        qs = Newsletter.objects.all()
        if not self.request.user.is_authenticated or not self.request.user.is_journalist:
            qs = qs.filter(status='published')
        return qs


class SignUpView(CreateView):
    """User registration view with role selection."""
    form_class = SignUpForm
    template_name = 'core/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, "Account created successfully! Please log in.")
        return super().form_valid(form)


class CustomLoginView(LoginView):
    """Custom login view with role-based redirect after login."""
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_journalist:
            return reverse_lazy('core:journalist_dashboard')
        elif user.is_editor:
            return reverse_lazy('core:publisher_dashboard')
        elif user.is_reader:
            return reverse_lazy('core:my-feed')
        return reverse_lazy('core:home')


class ReaderDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard for readers showing subscriptions, followed journalists, and recent feed."""
    template_name = 'core/reader_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['subscribed_publishers'] = user.subscribed_publishers.all()
        context['followed_journalists'] = user.subscribed_journalists.all()
        context['recent_feed_articles'] = Article.objects.filter(
            Q(publisher__in=user.subscribed_publishers.all()) |
            Q(author__in=user.subscribed_journalists.all(), publisher__isnull=True),
            status='published'
        ).select_related('author', 'publisher').order_by('-published_at')[:6]
        return context


class JournalistDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard for journalists showing article stats and recent work."""
    template_name = 'core/journalist_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['published_count'] = user.articles.filter(status='published').count()
        context['pending_count'] = user.articles.filter(status='pending').count()
        context['draft_count'] = user.articles.filter(status='draft').count()
        context['recent_articles'] = user.articles.order_by('-published_at', '-created_at')[:6]
        return context


class PublisherDashboardView(LoginRequiredMixin, DetailView):
    """Dashboard for publisher editors showing stats and pending articles."""
    model = Publisher
    template_name = 'core/publisher_dashboard.html'
    context_object_name = 'publisher'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.has_perm('core.change_article'):
            return qs
        return qs.filter(editors=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publisher = self.object
        context['published_count'] = publisher.articles.filter(status='published').count()
        context['pending_count'] = publisher.articles.filter(status='pending').count()
        context['pending_articles'] = publisher.articles.filter(status='pending').order_by('-created_at')[:6]
        context['recent_articles'] = publisher.articles.filter(status='published').order_by('-published_at')[:6]
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Displays the current user's profile page.
    Shows basic info, role, bio, profile picture, etc.
    """
    template_name = 'core/profile.html'
    login_url = reverse_lazy('core:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update({
            'user': user,
            'full_name': user.get_full_name() or user.username,
            'role': 'Reader' if user.is_reader else 'Journalist' if user.is_journalist else 'Editor' if user.is_editor else 'Unknown',
            'bio': user.bio,
            'profile_picture': user.profile_picture,
            'date_joined': user.date_joined,
            'email': user.email or "Not set",
            'article_count': user.articles.count() if user.is_journalist else 0,
            'followed_count': user.subscribed_journalists.count() if user.is_reader else 0,
            'subscribed_count': user.subscribed_publishers.count() if user.is_reader else 0,
        })
        return context


class MySubscriptionsView(LoginRequiredMixin, TemplateView):
    """
    Shows all publishers the user is subscribed to
    and all journalists the user is following.
    """
    template_name = 'core/subscriptions.html'
    login_url = reverse_lazy('core:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update({
            'subscribed_publishers': user.subscribed_publishers.all().order_by('name'),
            'followed_journalists': user.subscribed_journalists.all().order_by('username'),
            'has_subscriptions': user.subscribed_publishers.exists() or user.subscribed_journalists.exists(),
        })
        return context


class SubscribePublisherView(LoginRequiredMixin, View):
    """Handle subscription/unsubscription to a publisher."""
    login_url = reverse_lazy('login')

    def post(self, request, pk):
        publisher = get_object_or_404(Publisher, pk=pk)
        user = request.user

        if not user.groups.filter(name='Reader').exists():
            messages.error(request, "Only readers can subscribe.")
            return redirect('core:publisher_articles', pk=publisher.pk)

        if user.subscribed_publishers.filter(pk=publisher.pk).exists():
            user.subscribed_publishers.remove(publisher)
            messages.success(request, f"Unsubscribed from {publisher.name}.")
        else:
            user.subscribed_publishers.add(publisher)
            messages.success(request, f"Subscribed to {publisher.name}.")

        return redirect('core:publisher_articles', pk=publisher.pk)


class ArticleListView(ListView):
    """Public list of all published articles with pagination."""
    model = Article
    template_name = 'core/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        return Article.objects.filter(status='published') \
            .select_related('author', 'publisher') \
            .order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "All Articles"
        context['show_search'] = True
        return context


# ──────────────────────────────────────────────────────────────
# Follow / Unfollow
# ──────────────────────────────────────────────────────────────

@login_required
def follow_journalist(request, username):
    """Follow a journalist (reader action)."""
    journalist = get_object_or_404(
        CustomUser,
        username=username,
        groups__name='Journalist'
    )

    if request.user == journalist:
        messages.error(request, "You cannot follow yourself.")
    else:
        request.user.subscribed_journalists.add(journalist)
        messages.success(request, f"Now following {journalist.get_full_name() or journalist.username}.")

    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


@login_required
def unfollow_journalist(request, username):
    """Unfollow a journalist (reader action)."""
    journalist = get_object_or_404(
        CustomUser,
        username=username,
        groups__name='Journalist'
    )

    request.user.subscribed_journalists.remove(journalist)
    messages.success(request, f"Unfollowed {journalist.get_full_name() or journalist.username}.")

    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


# ──────────────────────────────────────────────────────────────
# Article Delete
# ──────────────────────────────────────────────────────────────

@login_required
@require_POST
def article_delete(request, pk):
    """Delete an article (with permission checks)."""
    article = get_object_or_404(Article, pk=pk)

    can_delete = (
        request.user.has_perm('core.delete_article')
        or request.user.is_editor
        or (article.author == request.user and request.user.is_journalist)
        or (article.publisher and request.user in article.publisher.editors.all())
    )

    if not can_delete:
        messages.error(request, "You do not have permission to delete this article.")
        return redirect('core:article_detail', pk=article.pk)

    title = article.title
    article.delete()
    messages.success(request, f"Article '{title}' has been deleted.")

    if article.publisher:
        return redirect('core:publisher_articles', pk=article.publisher.pk)
    return redirect('core:home')


def publisher_articles(request, pk):
    """Public view of all published articles from a specific publisher."""
    publisher = get_object_or_404(Publisher, pk=pk)
    articles = Article.objects.filter(
        publisher=publisher,
        status='published'
    ).select_related('author').order_by('-published_at')
    return render(request, 'core/publisher_articles.html', {
        'publisher': publisher,
        'articles': articles,
    })

# ──────────────────────────────────────────────────────────────
# Legacy / duplicated decorators (kept for backward compatibility)
# ──────────────────────────────────────────────────────────────

def journalist_required(view_func):
    """Legacy decorator (prefer the one in decorators.py)."""
    decorated_view_func = user_passes_test(
        lambda u: u.is_authenticated and u.is_journalist,
        login_url='login'
    )(view_func)
    return decorated_view_func